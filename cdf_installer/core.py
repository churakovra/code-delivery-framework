"""CDF 2.0 installation, ownership and crash recovery.

The installer owns its manifest-listed payload and a persistent private-state
ignore block. It never touches Codex's configuration, third-party dependencies,
or anything outside the selected root.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
import tomllib
import uuid

from cdf_runtime.contracts import validate_record
from cdf_registry import CORE, EXTRAS

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = '.codex/cdf/manifest.json'
TX = '.codex/cdf/transaction'
LOCK = '.codex/cdf.lock'
CLEANUP = '.codex/cdf-cleanup.json'
LEGACY_CLEANUP = '.cdf-cleanup.json'
IGNORE = '.codex/.gitignore'
IGNORE_START = b'# BEGIN CDF private state\n'
IGNORE_END = b'# END CDF private state\n'
IGNORE_BLOCK = (IGNORE_START + b'/cdf.lock/\n/cdf-cleanup.json\n/cdf/manifest.json\n'
                b'/cdf/backups/\n/cdf/transaction/\n' + IGNORE_END)
START = b'<!-- BEGIN CDF 2.0 MANAGED: core -->'
END = b'<!-- END CDF 2.0 MANAGED: core -->'
HEX = re.compile(r'^[0-9a-f]{64}$')


class CDFError(Exception):
    def __init__(self, code, message, paths=(), exit_code=2):
        super().__init__(message)
        self.code, self.paths, self.exit_code = code, list(paths), exit_code


def digest(data):
    return None if data is None else hashlib.sha256(data).hexdigest()


def target_root(value, scope='project', selected_home=None):
    raw = Path(value).expanduser().absolute()
    if '..' in raw.parts:
        raise CDFError('UNSAFE_TARGET', 'Target cannot contain traversal components.')
    for p in (raw, *raw.parents):
        if p.is_symlink():
            raise CDFError('UNSAFE_TARGET', 'Target cannot contain symlinks.', [str(p)])
    if not raw.is_dir() or raw == Path(raw.anchor):
        raise CDFError('UNSAFE_TARGET', 'Target must be an existing non-root directory.', [str(raw)])
    resolved = raw.resolve()
    actual_home = Path.home().resolve()
    home = Path(selected_home).expanduser().resolve() if selected_home else actual_home
    if scope == 'project' and resolved == actual_home:
        raise CDFError('UNSAFE_TARGET', 'A home directory requires explicit global scope.', [str(resolved)])
    if scope == 'global' and resolved != home:
        raise CDFError('UNSAFE_TARGET', 'Global target must equal the selected home directory.', [str(resolved)])
    return resolved


def relative_path(value):
    if not isinstance(value, str) or not value or '\\' in value or '\x00' in value:
        raise CDFError('UNSAFE_TARGET', 'Invalid managed path.', [str(value)])
    p = PurePosixPath(value)
    if p.is_absolute() or any(part in ('..', '.') for part in value.split('/')) or str(p) != value:
        raise CDFError('UNSAFE_TARGET', 'Invalid managed path.', [value])
    return p


def safe(root, value):
    p = relative_path(value)
    current = root
    for part in p.parts:
        if current.is_dir():
            matches = [entry.name for entry in current.iterdir() if entry.name.casefold() == part.casefold()]
            if any(name != part for name in matches):
                raise CDFError('PATH_COLLISION', 'Case-colliding target path.', [value])
        current = current / part
        if current.is_symlink():
            raise CDFError('UNSAFE_TARGET', 'Symlink in managed path.', [value])
        if current.exists() and current != root / p and not current.is_dir():
            raise CDFError('UNSAFE_TARGET', 'Non-directory in managed path.', [value])
    if current.exists() and not current.is_file() and not current.is_dir():
        raise CDFError('UNSAFE_TARGET', 'Special file in managed path.', [value])
    return current


def allowed(path, agents):
    p = relative_path(path)
    parts = p.parts
    return (path == agents or path == '.codex/cdf/subskills.catalog.json'
            or path in ('.codex/agents/cdf_reviewer.toml', '.codex/agents/cdf_diagnostician.toml')
            or path in ('.codex/cdf/backups/AGENTS.original', '.codex/cdf/backups/AGENTS.absent')
            or (len(parts) >= 4 and parts[:2] == ('.agents', 'skills') and parts[2] in set(CORE) | set(sum(EXTRAS.values(), ()))) )


def valid_created_directory(value):
    """Limit deletion claims to directory ancestors in the CDF payload."""
    p = relative_path(value)
    parts = p.parts
    if value in ('.agents', '.agents/skills', '.codex', '.codex/agents',
                 '.codex/cdf', '.codex/cdf/backups'):
        return True
    names = set(CORE) | set(sum(EXTRAS.values(), ()))
    return (len(parts) >= 3 and parts[:2] == ('.agents', 'skills')
            and parts[2] in names)


def validate_directories(root, values):
    if not isinstance(values, list) or any(not isinstance(p, str) for p in values) or len(set(values)) != len(values):
        raise ValueError('invalid created directory list')
    for value in values:
        if not valid_created_directory(value):
            raise ValueError('unapproved created directory')
        safe(root, value)
    return values


def cleanup_directories(root, values):
    """Remove only recorded empty directories, deepest first; preserve contents."""
    for value in sorted(set(values), key=lambda p: (-len(PurePosixPath(p).parts), p)):
        path = safe(root, value)
        if not path.exists():
            continue
        if not path.is_dir():
            continue
        try:
            path.rmdir()
            sync_dir(path.parent)
        except OSError as exc:
            # Non-empty user directories are preserved. Other failures remain visible.
            import errno
            if exc.errno not in (errno.ENOTEMPTY, errno.EEXIST):
                raise


def cleanup_intent(root, scope):
    raw = read_file(root, CLEANUP)
    legacy = read_file(root, LEGACY_CLEANUP)
    if raw is not None and legacy is not None:
        raise CDFError('RECOVERY_REQUIRED', 'Multiple cleanup intents require manual inspection.', [CLEANUP, LEGACY_CLEANUP], 3)
    if raw is None:
        raw = legacy
    if raw is None:
        return None
    try:
        value = json.loads(raw)
        if (not isinstance(value, dict) or set(value) != {'schema', 'target', 'scope', 'directories'}
                or value['schema'] != 1 or value['target'] != str(root) or value['scope'] != scope):
            raise ValueError('invalid cleanup intent')
        validate_directories(root, value['directories'])
        return value['directories']
    except (TypeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        raise CDFError('RECOVERY_REQUIRED', f'Invalid cleanup intent: {exc}', [CLEANUP], 3) from exc


def ensure_cleanup_intent(root, scope, directories):
    if not directories:
        return
    intended = sorted(set(directories))
    existing = cleanup_intent(root, scope)
    if existing is not None:
        if existing != intended:
            raise CDFError('RECOVERY_REQUIRED', 'A different cleanup intent already exists.', [CLEANUP], 3)
        return
    payload = json.dumps({'schema': 1, 'target': str(root), 'scope': scope,
                          'directories': intended}, sort_keys=True).encode() + b'\n'
    path = safe(root, CLEANUP)
    txdir = safe(root, TX)
    fd, temporary = tempfile.mkstemp(prefix='intent-', dir=txdir)
    try:
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise CDFError('RECOVERY_REQUIRED', 'Cleanup intent appeared concurrently.', [CLEANUP], 3) from exc
        sync_dir(path.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
            sync_dir(txdir)


def finish_cleanup(root, scope, directories):
    intent = cleanup_intent(root, scope)
    if intent is None:
        return
    if sorted(set(directories)) != intent:
        raise CDFError('RECOVERY_REQUIRED', 'Cleanup intent does not match the transaction.', [CLEANUP], 3)
    cleanup_directories(root, intent)
    marker = CLEANUP if safe(root, CLEANUP).exists() else LEGACY_CLEANUP
    safe(root, marker).unlink()
    sync_dir(safe(root, marker).parent)


def read_file(root, path):
    p = safe(root, path)
    if not p.exists():
        return None
    if not p.is_file():
        raise CDFError('PATH_COLLISION', 'Expected a regular file.', [path])
    return p.read_bytes()


def mode(root, path):
    p = safe(root, path)
    return stat.S_IMODE(p.stat().st_mode) if p.exists() and p.is_file() else None


def sync_dir(p):
    fd = os.open(p, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def mkdir_durable(root, relative, leaf_mode=0o755, created=None):
    """Create missing directories and persist each newly created parent entry."""
    parts = relative_path(relative).parts
    current = root
    for index, part in enumerate(parts):
        next_path = safe(root, PurePosixPath(*parts[:index + 1]).as_posix())
        if not next_path.exists():
            next_path.mkdir(mode=leaf_mode if index == len(parts) - 1 else 0o755)
            sync_dir(current)
            sync_dir(next_path)
            if created is not None:
                created.append(PurePosixPath(*parts[:index + 1]).as_posix())
        elif not next_path.is_dir():
            raise CDFError('PATH_COLLISION', 'Expected a directory.', [str(next_path)])
        current = next_path
    return current


def write_atomic(path, data, permissions=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.cdf-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), permissions)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        sync_dir(path.parent)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def apply_file(root, path, data, permissions):
    p = safe(root, path)
    if data is None:
        if p.exists():
            p.unlink()
            sync_dir(p.parent)
    else:
        # Recheck every parent after creation, including a newly created parent.
        parent = PurePosixPath(path).parent.as_posix()
        if parent != '.': mkdir_durable(root, parent)
        p = safe(root, path)
        write_atomic(p, data, permissions if permissions is not None else 0o644)


def parse_skill(path, name):
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---\n') or '\n---\n' not in text[4:]:
        raise CDFError('INVALID_BUNDLE', 'Missing skill frontmatter.', [str(path)])
    header = text.split('---', 2)[1]
    actual = re.search(r'^name:\s*(\S+)\s*$', header, re.M)
    desc = re.search(r'^description:\s*(\S.+)$', header, re.M)
    if not actual or actual.group(1) != name or not desc:
        raise CDFError('INVALID_BUNDLE', 'Invalid skill name or description.', [str(path)])
    for ref in re.findall(r'`(references/[^`]+\.md)`', text):
        rp = relative_path(ref)
        if not (path.parent / rp).is_file() or (path.parent / rp).is_symlink():
            raise CDFError('INVALID_BUNDLE', 'Missing skill reference.', [str(path.parent / rp)])


def bundle(root=ROOT, extras=()):
    result = {}
    selected = list(CORE)
    for extra in sorted(extras):
        if extra not in EXTRAS:
            raise CDFError('INVALID_REQUEST', 'Unknown extra.', [extra])
        selected.extend(EXTRAS[extra])
    try:
        for name in selected:
            source = root / 'skills' / name
            entry = source / 'SKILL.md'
            if source.is_symlink() or entry.is_symlink():
                raise CDFError('INVALID_BUNDLE', 'Symlink in skill bundle.', [str(source)])
            parse_skill(entry, name)
            for item in sorted(source.rglob('*')):
                if item.is_symlink():
                    raise CDFError('INVALID_BUNDLE', 'Symlink in skill bundle.', [str(item)])
                if item.is_file():
                    result[f'.agents/skills/{name}/{item.relative_to(source).as_posix()}'] = item.read_bytes()
        for name in ('cdf_reviewer', 'cdf_diagnostician'):
            file = root / 'templates' / f'{name}.toml'
            data = file.read_bytes()
            fields = tomllib.loads(data.decode('utf-8'))
            if fields.get('name') != name or any(k in fields for k in ('model', 'model_reasoning_effort')) or not fields.get('description') or not fields.get('developer_instructions'):
                raise CDFError('INVALID_BUNDLE', 'Invalid agent template.', [str(file)])
            result[f'.codex/agents/{name}.toml'] = data
        catalog = (root / 'subskills.catalog.json').read_bytes()
        entries = json.loads(catalog)
        if not isinstance(entries.get('candidates'), dict):
            raise CDFError('INVALID_BUNDLE', 'Invalid subskill catalog.')
        result['.codex/cdf/subskills.catalog.json'] = catalog
        block = (root / 'templates/AGENTS.cdf-block.md').read_bytes()
        if block.count(START) != 1 or block.count(END) != 1 or not block.startswith(START) or not block.rstrip(b'\r\n').endswith(END):
            raise CDFError('INVALID_BUNDLE', 'Invalid managed block template.')
        block = block.rstrip(b'\r\n') + b'\n'
        return result, block
    except (OSError, UnicodeError, ValueError, tomllib.TOMLDecodeError) as exc:
        raise CDFError('INVALID_BUNDLE', f'Cannot read bundle: {exc}') from exc


def block_span(data):
    if data.count(START) != 1 or data.count(END) != 1:
        raise CDFError('MANAGED_BLOCK_MODIFIED', 'Expected exactly one intact managed block.')
    start = data.index(START)
    end_marker = data.find(END)
    if end_marker < start:
        raise CDFError('MANAGED_BLOCK_MODIFIED', 'Managed block markers are reversed.')
    end = end_marker + len(END)
    if data[end:end + 2] == b'\r\n': end += 2
    elif data[end:end + 1] == b'\n': end += 1
    return start, end


def manifest_read(root, scope):
    raw = read_file(root, MANIFEST)
    if raw is None:
        return None
    try:
        m = json.loads(raw)
        required = {'schema', 'framework_version', 'scope', 'source_revision', 'selected_extras', 'state', 'owned_files', 'managed_blocks', 'preserved_preimages', 'transaction'}
        if not isinstance(m, dict) or not required.issubset(m) or set(m) - required - {'created_directories'} or m['schema'] != 2 or m['scope'] != scope or not re.fullmatch(r'[12]\.\d+\.\d+(?:\.dev\d+|[-+][A-Za-z0-9.-]+)?', m['framework_version']) or not isinstance(m['source_revision'], str) or not m['source_revision']:
            raise ValueError('unsupported manifest fields or scope')
        if m['state'] not in ('installed', 'partial', 'recovery-required', 'conflict') or not isinstance(m['selected_extras'], list) or len(set(m['selected_extras'])) != len(m['selected_extras']) or not set(m['selected_extras']) <= set(EXTRAS):
            raise ValueError('invalid state or extras')
        if m['transaction'] is not None:
            raise ValueError('unsupported active transaction field')
        agents = '.codex/AGENTS.md' if scope == 'global' else 'AGENTS.md'
        if not all(isinstance(m[x], dict) for x in ('owned_files', 'managed_blocks', 'preserved_preimages')):
            raise ValueError('invalid maps')
        for path, info in m['owned_files'].items():
            if not allowed(path, agents) or path == agents or not isinstance(info, dict) or set(info) != {'sha256', 'mode'} or not isinstance(info['sha256'], str) or not HEX.fullmatch(info['sha256']) or type(info['mode']) is not int or not 0 <= info['mode'] <= 4095:
                raise ValueError('invalid owned file')
            safe(root, path)
        if set(m['managed_blocks']) - {agents} or set(m['preserved_preimages']) - {agents}:
            raise ValueError('invalid managed block path')
        for path, info in m['managed_blocks'].items():
            if not isinstance(info, dict) or set(info) != {'start_marker', 'end_marker', 'sha256'} or info['start_marker'].encode() != START or info['end_marker'].encode() != END or not isinstance(info['sha256'], str) or not HEX.fullmatch(info['sha256']):
                raise ValueError('invalid block')
            safe(root, path)
        for path, info in m['preserved_preimages'].items():
            if not isinstance(info, dict) or set(info) != {'sha256', 'backup'} or not isinstance(info['sha256'], str) or not HEX.fullmatch(info['sha256']) or info['backup'] not in ('.codex/cdf/backups/AGENTS.original', '.codex/cdf/backups/AGENTS.absent'):
                raise ValueError('invalid backup')
            if info['backup'] not in m['owned_files'] or m['owned_files'][info['backup']]['sha256'] != info['sha256']:
                raise ValueError('unowned backup')
            safe(root, info['backup'])
        if bool(m['managed_blocks']) != bool(m['preserved_preimages']):
            raise ValueError('incomplete managed block records')
        validate_directories(root, m.get('created_directories', []))
        if m['state'] == 'installed':
            required_files = {f'.agents/skills/{name}/SKILL.md' for name in CORE}
            for extra in m['selected_extras']:
                required_files.update(f'.agents/skills/{name}/SKILL.md' for name in EXTRAS[extra])
            required_files.update({'.codex/agents/cdf_reviewer.toml',
                                   '.codex/agents/cdf_diagnostician.toml',
                                   '.codex/cdf/subskills.catalog.json'})
            present_skills = {p.split('/')[2] for p in m['owned_files']
                              if p.startswith('.agents/skills/')}
            declared_skills = set(CORE)
            for extra in m['selected_extras']:
                declared_skills.update(EXTRAS[extra])
            if (not required_files.issubset(m['owned_files']) or present_skills != declared_skills
                    or set(m['managed_blocks']) != {agents}
                    or set(m['preserved_preimages']) != {agents}):
                raise ValueError('installed manifest lacks required files, extras or managed block')
        return m
    except (TypeError, ValueError, KeyError, AttributeError, json.JSONDecodeError) as exc:
        raise CDFError('MANIFEST_UNSUPPORTED', f'Invalid or unsupported manifest: {exc}', [MANIFEST]) from exc


def check_legacy(root, agents):
    old_manifest = safe(root, '.codex/delivery-framework/manifest.json')
    # Legacy installations have a managed instruction marker even when their state layout differs.
    data = read_file(root, agents) or b''
    legacy = b'<!-- codex-delivery-framework:start -->' in data or old_manifest.exists()
    return legacy


def find_duplicates(root, selected, owned, scope):
    # Codex can discover both project/ancestor and user-level skills. Read-only
    # collision checks include these locations; they never create directories.
    roots = [root, *[p for p in root.parents if p != Path(p.anchor)]]
    home = root if scope == 'global' else Path.home()
    roots.append(home)
    directories = []
    for base in roots:
        directories.extend((base / '.agents/skills', base / '.codex/skills'))
    codex_home = os.environ.get('CODEX_HOME')
    if codex_home:
        directories.append(Path(codex_home).expanduser() / 'skills')
    owned_paths = {(root / p).resolve() for p in owned}
    seen = set()
    for base in directories:
        if not base.exists():
            continue
        resolved = base.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if not base.is_dir():
            raise CDFError('PATH_COLLISION', 'Skills location is not a directory.', [str(base)])
        for entry in base.rglob('SKILL.md'):
            if entry.resolve() in owned_paths:
                continue
            if not entry.is_file():
                continue
            try:
                txt = entry.read_text(encoding='utf-8')
            except (UnicodeError, OSError) as exc:
                raise CDFError('PATH_COLLISION', f'Cannot inspect discovered skill: {exc}', [str(entry)]) from exc
            name = re.search(r'^name:\s*[\"\']?([^\r\n\"\']+)', txt, re.M)
            if name and name.group(1).strip() in selected:
                try:
                    path = entry.relative_to(root).as_posix()
                except ValueError:
                    path = str(entry)
                raise CDFError('PATH_COLLISION', 'A discovered unowned skill has the same name.', [path])


def changes_plan(root, scope, action, extras=(), src=ROOT, release_modified_skills=False):
    agents = '.codex/AGENTS.md' if scope == 'global' else 'AGENTS.md'
    if safe(root, LEGACY_CLEANUP).exists():
        raise CDFError('RECOVERY_REQUIRED', 'Interrupted legacy directory cleanup requires recovery.', [LEGACY_CLEANUP], 3)
    if safe(root, CLEANUP).exists():
        raise CDFError('RECOVERY_REQUIRED', 'Interrupted directory cleanup requires recovery.', [CLEANUP], 3)
    tx = safe(root, TX)
    if tx.exists():
        raise CDFError('RECOVERY_REQUIRED', 'Interrupted transaction requires recovery.', [TX], 3)
    m = manifest_read(root, scope)
    if action == 'install' and (m or check_legacy(root, agents)):
        raise CDFError('LEGACY_MIGRATION_REQUIRED' if not m else 'PATH_COLLISION', 'Existing installation must be inspected before installing.')
    if action == 'upgrade' and not m:
        raise CDFError('LEGACY_MIGRATION_REQUIRED' if check_legacy(root, agents) else 'MANIFEST_UNSUPPORTED', 'No compatible v2 installation exists.')
    if action == 'upgrade' and m['state'] != 'installed':
        raise CDFError('MANIFEST_UNSUPPORTED', 'Resolve the partial installation before upgrading.')
    if action == 'uninstall' and not m:
        return [], None, [], []
    if action in ('install', 'upgrade'):
        files, block = bundle(src, extras)
        hasher = hashlib.sha256()
        for name, contents in sorted(files.items()):
            hasher.update(name.encode('utf-8') + b'\x00' + bytes.fromhex(digest(contents)))
        hasher.update(b'AGENTS\x00' + bytes.fromhex(digest(block)))
        source_identity = 'sha256:' + hasher.hexdigest()
        find_duplicates(root, {p.split('/')[2] for p in files if p.startswith('.agents/skills/')}, set(m['owned_files']) if m else set(), scope)
    else:
        files, block = {}, None
    old_owned = m['owned_files'] if m else {}
    observed_agents = read_file(root, agents)
    observed_agents_mode = mode(root, agents)
    conflicts, warnings, preserved = [], [], []
    desired = dict(files)
    if action == 'install':
        original = observed_agents
        if original and (START in original or END in original):
            raise CDFError('MANAGED_BLOCK_MODIFIED', 'Unowned managed block already exists.', [agents])
        backup = '.codex/cdf/backups/AGENTS.absent' if original is None else '.codex/cdf/backups/AGENTS.original'
        desired[backup] = original or b''
        before = original or b''
        desired[agents] = before + (b'\n' if before and not before.endswith(b'\n') else b'') + block
        preimages = {agents: {'sha256': digest(original or b''), 'backup': backup}}
    else:
        preimages = dict(m['preserved_preimages'])
        for path, info in old_owned.items():
            actual = read_file(root, path)
            if digest(actual) != info['sha256'] or mode(root, path) != info['mode']:
                if action == 'uninstall' and actual is None: continue
                if action == 'uninstall': preserved.append(path)
                else: conflicts.append(path)
        if agents in m['managed_blocks']:
            current = observed_agents
            try:
                if current is None: raise CDFError('MANAGED_BLOCK_MODIFIED', 'Managed block is missing.')
                start, end = block_span(current)
                if digest(current[start:end]) != m['managed_blocks'][agents]['sha256']:
                    raise CDFError('MANAGED_BLOCK_MODIFIED', 'Managed block was edited.')
                if action == 'upgrade': desired[agents] = current[:start] + block + current[end:]
                else:
                    outside = current[:start] + current[end:]
                    backup = preimages[agents]['backup']
                    original = read_file(root, backup)
                    if backup in preserved or original is None:
                        preserved.append(agents)
                    else:
                        if original and not original.endswith(b'\n') and outside == original + b'\n': outside = original
                        desired[agents] = None if backup.endswith('AGENTS.absent') and not outside else outside
            except CDFError:
                if action == 'uninstall': preserved.append(agents)
                else: conflicts.append(agents)
        if action == 'upgrade':
            # Preimage is intentionally retained across upgrades.
            for entry in preimages.values(): desired[entry['backup']] = read_file(root, entry['backup'])
        elif agents in preserved:
            for entry in preimages.values():
                if entry['backup'] not in preserved:
                    desired[entry['backup']] = read_file(root, entry['backup'])
    if action in ('install', 'upgrade'):
        for path in desired:
            if path != agents and path not in old_owned and read_file(root, path) is not None:
                conflicts.append(path)
    if conflicts:
        raise CDFError('MANAGED_FILE_MODIFIED' if m else 'PATH_COLLISION', 'Conflicting or modified paths prevent this operation.', sorted(set(conflicts)))
    released = []
    if action == 'uninstall':
        if release_modified_skills:
            skill_names = {p.split('/')[2] for p in preserved if p.startswith('.agents/skills/')}
            released = [p for p in old_owned if p.startswith('.agents/skills/')
                        and p.split('/')[2] in skill_names and read_file(root, p) is not None]
            preserved = list(set(preserved) | set(released))
        for path in preserved:
            desired.pop(path, None)
        warnings = ['Modified files were preserved; resolve them before retrying.'] if set(preserved) - set(released) else []
    candidates = set(desired) | (set(old_owned) - set(preserved))
    operations = []
    for path in sorted(candidates):
        if not allowed(path, agents): raise CDFError('UNSAFE_TARGET', 'Unapproved managed path.', [path])
        before = read_file(root, path)
        after = desired.get(path)
        before_mode = mode(root, path)
        if path == agents and (before, before_mode) != (observed_agents, observed_agents_mode):
            raise CDFError('CONCURRENT_MUTATION', 'Managed instructions changed during planning.', [path])
        if path in old_owned and path not in preserved and not (action == 'uninstall' and before is None) and (digest(before), before_mode) != (old_owned[path]['sha256'], old_owned[path]['mode']):
            raise CDFError('CONCURRENT_MUTATION', 'Managed file changed during planning.', [path])
        after_mode = (before_mode if before_mode is not None else (0o600 if path.startswith('.codex/cdf/backups/') else 0o644)) if after is not None else None
        if before == after and before_mode == after_mode: op = 'unchanged'
        elif before is None: op = 'add'
        elif after is None: op = 'remove'
        else: op = 'update'
        operations.append({'path': path, 'operation': op, 'before_sha256': digest(before), 'after_sha256': digest(after), '_before': before, '_after': after, '_old_mode': before_mode, '_new_mode': after_mode})
    if released:
        warnings.append('Modified skills were preserved and ownership was released: ' + ', '.join(sorted(released)))
    remaining = [p for p in preserved if p not in released]
    if action == 'uninstall' and not remaining:
        new_manifest = None
    else:
        if action == 'uninstall':
            kept = {p: v for p, v in old_owned.items() if p in remaining or p in desired}
            keep_block = agents in preserved
            new_manifest = dict(m, state='partial', owned_files=kept,
                                managed_blocks=m['managed_blocks'] if keep_block else {},
                                preserved_preimages=preimages if keep_block else {})
        else:
            owned = {op['path']: {'sha256': op['after_sha256'], 'mode': op['_new_mode']} for op in operations if op['path'] != agents and op['_after'] is not None}
            new_manifest = {'schema': 2, 'framework_version': _version(src), 'scope': scope,
                            'source_revision': source_identity, 'selected_extras': sorted(extras),
                            'state': 'installed', 'owned_files': owned,
                            'managed_blocks': {agents: {'start_marker': START.decode(), 'end_marker': END.decode(), 'sha256': digest(block)}},
                            'preserved_preimages': preimages, 'transaction': None}
    return operations, new_manifest, sorted(set(preserved)), warnings


def _version_key(value):
    """Return a comparable framework version; reject forms we cannot safely order.

    Development releases precede alpha, beta, release candidates and final
    releases of the same numeric version. Local build metadata does not change
    ordering. Unrecognized qualifiers cannot authorize a downgrade.
    """
    if not isinstance(value, str):
        raise ValueError('version must be a string')
    match = re.fullmatch(
        r'([12])\.(\d+)\.(\d+)(?:(?:\.|-)(dev|a|b|rc)(\d+))?(?:\+[A-Za-z0-9.-]+)?',
        value,
    )
    if not match:
        raise ValueError('version cannot be safely ordered')
    major, minor, patch = (int(match.group(i)) for i in (1, 2, 3))
    stage = {'dev': 0, 'a': 1, 'b': 2, 'rc': 3, None: 4}[match.group(4)]
    return major, minor, patch, stage, int(match.group(5) or 0)


def _version(src):
    try:
        value = tomllib.loads((src / 'pyproject.toml').read_text())['project']['version']
        _version_key(value)
        if not re.fullmatch(r'[12]\.\d+\.\d+(?:\.dev\d+|[-+][A-Za-z0-9.-]+)?', value):
            raise ValueError('version does not match the installed manifest contract')
        return value
    except (OSError, KeyError, ValueError, tomllib.TOMLDecodeError) as exc:
        raise CDFError('INVALID_BUNDLE', f'Invalid framework version: {exc}') from exc


def public_plan(root, scope, action, ops, warnings):
    return {'schema': 1, 'action': action, 'state': 'ready', 'scope': scope, 'target': str(root),
            'planned_actions': [{k: v for k, v in op.items() if not k.startswith('_')} for op in ops],
            'conflicts': [], 'warnings': ['Dry-run plan; apply rechecks paths and hashes.'] + warnings}


class Lock:
    def __init__(self, root): self.root = root
    def __enter__(self):
        path = safe(self.root, LOCK)
        self.parent_created = not path.parent.exists()
        mkdir_durable(self.root, '.codex')
        try:
            path.mkdir(mode=0o700)
            sync_dir(path.parent)
        except FileExistsError as exc:
            raise CDFError('CONCURRENT_MUTATION', 'CDF lock exists. Inspect the owner and remove a stale lock only after confirming no operation is running.', [LOCK]) from exc
        self.path = path
        try:
            (path / 'owner.json').write_text(json.dumps({'pid': os.getpid()}) + '\n')
        except OSError:
            path.rmdir()
            raise
        return self
    def __exit__(self, *args):
        try:
            (self.path / 'owner.json').unlink(missing_ok=True)
            self.path.rmdir()
            if self.parent_created:
                try: self.path.parent.rmdir()
                except OSError: pass
        except OSError:
            pass


def journal_read(root, scope):
    txdir = safe(root, TX)
    if not txdir.exists(): return None
    if not txdir.is_dir(): raise CDFError('RECOVERY_REQUIRED', 'Invalid transaction directory.', [TX], 3)
    raw = read_file(root, TX + '/journal.json')
    if raw is None:
        # A transaction directory without a journal was interrupted before any
        # payload mutation. Only known regular preparation files may be removed.
        names = {x.name for x in txdir.iterdir()}
        if any(not re.fullmatch(r'backup-[0-9]+|intent-[A-Za-z0-9_]+', n) for n in names):
            raise CDFError('RECOVERY_REQUIRED', 'Unexpected incomplete transaction contents require manual inspection.', [TX], 3)
        return {'preparing': True}
    try:
        names = {x.name for x in txdir.iterdir()}
        if any(not (n == 'journal.json' or re.fullmatch(r'backup-[0-9]+|intent-[A-Za-z0-9_]+', n)) for n in names):
            raise ValueError('unexpected transaction contents')
        j = json.loads(raw)
        validate_record('transaction-journal', j)
        required = {'schema', 'transaction_id', 'action', 'target_canonical', 'scope', 'phase', 'paths', 'manifest_planned_sha256'}
        if not isinstance(j, dict) or not required.issubset(j) or set(j) - required - {'created_directories', 'cleanup_directories'} or j['schema'] != 1 or j['target_canonical'] != str(root) or j['scope'] != scope or j['action'] not in ('install', 'upgrade', 'uninstall', 'recover') or j['phase'] not in ('prepared', 'applying', 'complete') or not isinstance(j['transaction_id'], str) or not re.fullmatch(r'[0-9a-f]{32}', j['transaction_id']): raise ValueError('invalid header')
        if not isinstance(j['manifest_planned_sha256'], str) or not HEX.fullmatch(j['manifest_planned_sha256']): raise ValueError('invalid manifest hash')
        if not isinstance(j['paths'], list): raise ValueError('invalid paths')
        validate_directories(root, j.get('created_directories', []))
        validate_directories(root, j.get('cleanup_directories', []))
        agents = '.codex/AGENTS.md' if scope == 'global' else 'AGENTS.md'
        seen = set()
        for i, item in enumerate(j['paths']):
            if not isinstance(item, dict) or set(item) != {'relative_path', 'old_sha256', 'new_sha256', 'backup', 'old_mode', 'new_mode'}: raise ValueError('invalid path entry')
            p = item['relative_path']
            if p in seen or not (p == MANIFEST or allowed(p, agents)): raise ValueError('invalid managed path')
            seen.add(p)
            safe(root, p)
            for key in ('old_sha256', 'new_sha256'):
                if item[key] is not None and (not isinstance(item[key], str) or not HEX.fullmatch(item[key])): raise ValueError('invalid hash')
            for key in ('old_mode', 'new_mode'):
                if item[key] is not None and (type(item[key]) is not int or not 0 <= item[key] <= 4095): raise ValueError('invalid mode')
            if (item['old_sha256'] is None) != (item['old_mode'] is None) or (item['new_sha256'] is None) != (item['new_mode'] is None): raise ValueError('inconsistent mode')
            if item['backup'] != (f'backup-{i}' if item['old_sha256'] is not None else None): raise ValueError('invalid backup name')
            if item['backup'] and j['phase'] != 'complete':
                data = read_file(root, TX + '/' + item['backup'])
                if digest(data) != item['old_sha256']: raise ValueError('backup hash mismatch')
        return j
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise CDFError('RECOVERY_REQUIRED', f'Invalid recovery journal: {exc}', [TX], 3) from exc


def recover_locked(root, scope, dry=False):
    j = journal_read(root, scope)
    if j is None:
        cleanup = cleanup_intent(root, scope)
        if cleanup is None:
            return {'schema': 1, 'state': 'absent', 'next_action': 'No transaction requires recovery.'}
        if dry:
            return {'schema': 1, 'action': 'recover', 'state': 'ready', 'scope': scope, 'target': str(root),
                    'planned_actions': [], 'conflicts': [], 'warnings': ['Recorded empty directories will be removed.']}
        return {'schema': 1, 'state': 'recovered', 'restored_paths': [], '_cleanup_directories': cleanup}
    if j.get('preparing'):
        actions = []
    elif j['phase'] == 'complete':
        actions, conflicts = [], []
        for item in j['paths']:
            path = item['relative_path']
            if (digest(read_file(root, path)), mode(root, path)) != (item['new_sha256'], item['new_mode']):
                conflicts.append(path)
        if conflicts:
            raise CDFError('CONCURRENT_MUTATION', 'Committed files changed before cleanup; preserve them for manual reconciliation.', conflicts, 3)
    else:
        actions, conflicts = [], []
        for item in reversed(j['paths']):
            path = item['relative_path']
            current, current_mode = digest(read_file(root, path)), mode(root, path)
            old = (item['old_sha256'], item['old_mode'])
            new = (item['new_sha256'], item['new_mode'])
            if (current, current_mode) == old:
                continue
            if (current, current_mode) != new:
                conflicts.append(path)
            else:
                actions.append(item)
        if conflicts:
            raise CDFError('CONCURRENT_MUTATION', 'Files changed since the transaction; recovery preserves them for manual reconciliation.', conflicts, 3)
    cleanup = ((cleanup_intent(root, scope) or []) if j.get('preparing') else
               j.get('cleanup_directories', []) if j['phase'] == 'complete' else
               j.get('created_directories', []))
    if dry:
        return {'schema': 1, 'action': 'recover', 'state': 'ready', 'scope': scope, 'target': str(root),
                'planned_actions': [{'path': a['relative_path'], 'operation': 'remove' if a['old_sha256'] is None else 'update', 'before_sha256': a['new_sha256'], 'after_sha256': a['old_sha256']} for a in actions], 'conflicts': [], 'warnings': ['Recovery will recheck file states.']}
    for item in actions:
        path = item['relative_path']
        if (digest(read_file(root, path)), mode(root, path)) != (item['new_sha256'], item['new_mode']):
            raise CDFError('CONCURRENT_MUTATION', 'Path changed during recovery.', [path], 3)
        old = read_file(root, TX + '/' + item['backup']) if item['backup'] else None
        apply_file(root, path, old, item['old_mode'])
    tx = safe(root, TX)
    for item in tx.iterdir():
        if item.is_symlink() or not item.is_file() or not (item.name == 'journal.json' or re.fullmatch(r'backup-[0-9]+|intent-[A-Za-z0-9_]+', item.name)):
            raise CDFError('RECOVERY_REQUIRED', 'Unexpected transaction content requires manual inspection.', [str(item)], 3)
    ensure_cleanup_intent(root, scope, cleanup)
    cleanup_directories(root, cleanup)
    journal_path = tx / 'journal.json'
    if journal_path.exists():
        journal_path.unlink()
        sync_dir(tx)
    for item in tx.iterdir(): item.unlink()
    tx.rmdir()
    sync_dir(tx.parent)
    cleanup_directories(root, cleanup)
    return {'schema': 1, 'state': 'recovered', 'restored_paths': [a['relative_path'] for a in actions],
            '_cleanup_directories': cleanup}


def transact(root, scope, action, ops, new_manifest, lock_created=False):
    """Write preimages and durable journal before applying payload; manifest last."""
    old_manifest = read_file(root, MANIFEST)
    old = manifest_read(root, scope) if old_manifest is not None else None
    cleanup = old.get('created_directories', []) if action == 'uninstall' and new_manifest is None and old else []
    created = ['.codex'] if lock_created else []
    management_missing = not safe(root, '.codex/cdf').exists()
    if management_missing:
        created.append('.codex/cdf')
    parents = set()
    for op in ops:
        if op['_after'] is not None:
            path = PurePosixPath(op['path']).parent
            while str(path) != '.':
                parents.add(str(path))
                path = path.parent
    missing = [p for p in sorted(parents, key=lambda p: (len(PurePosixPath(p).parts), p))
               if p != '.codex/cdf' and not safe(root, p).exists()]
    if new_manifest is not None:
        previous = old.get('created_directories', []) if old else []
        new_manifest['created_directories'] = sorted(set(previous + created + missing))
    data = None if new_manifest is None else (json.dumps(new_manifest, indent=2, sort_keys=True) + '\n').encode()
    changes = [o for o in ops if o['operation'] != 'unchanged']
    if old_manifest != data:
        changes.append({'path': MANIFEST, '_before': old_manifest, '_after': data,
                        '_old_mode': mode(root, MANIFEST), '_new_mode': 0o600 if data is not None else None})
    for op in changes:
        if (digest(read_file(root, op['path'])), mode(root, op['path'])) != (digest(op['_before']), op['_old_mode']):
            raise CDFError('CONCURRENT_MUTATION', 'File changed during preflight.', [op['path']])
    if management_missing and safe(root, '.codex/cdf').exists():
        raise CDFError('CONCURRENT_MUTATION', 'Management directory appeared during preflight.', ['.codex/cdf'])
    tx = safe(root, TX)
    mkdir_durable(root, TX, leaf_mode=0o700)
    os.chmod(tx, 0o700)
    sync_dir(tx.parent)
    records = []
    try:
        for i, op in enumerate(changes):
            backup = f'backup-{i}' if op['_before'] is not None else None
            if backup:
                write_atomic(safe(root, TX + '/' + backup), op['_before'], 0o600)
            records.append({'relative_path': op['path'], 'old_sha256': digest(op['_before']),
                            'new_sha256': digest(op['_after']), 'backup': backup,
                            'old_mode': op['_old_mode'], 'new_mode': op['_new_mode']})
        j = {'schema': 1, 'transaction_id': uuid.uuid4().hex, 'action': action,
             'target_canonical': str(root), 'scope': scope, 'phase': 'prepared', 'paths': records,
             'manifest_planned_sha256': digest(data or b''),
             'created_directories': sorted(created), 'cleanup_directories': sorted(cleanup)}
        write_atomic(safe(root, TX + '/journal.json'), (json.dumps(j, indent=2) + '\n').encode(), 0o600)
        sync_dir(tx)
        for directory in missing:
            if safe(root, directory).exists():
                raise CDFError('CONCURRENT_MUTATION', 'Directory appeared during transaction.', [directory])
            newly_created = []
            mkdir_durable(root, directory, created=newly_created)
            created.extend(newly_created)
            j['created_directories'] = sorted(created)
            write_atomic(safe(root, TX + '/journal.json'), (json.dumps(j, indent=2) + '\n').encode(), 0o600)
        for op in changes:
            if (digest(read_file(root, op['path'])), mode(root, op['path'])) != (digest(op['_before']), op['_old_mode']):
                raise CDFError('CONCURRENT_MUTATION', 'File changed during transaction.', [op['path']])
            apply_file(root, op['path'], op['_after'], op['_new_mode'])
        j['phase'] = 'complete'
        write_atomic(safe(root, TX + '/journal.json'), (json.dumps(j, indent=2) + '\n').encode(), 0o600)
        sync_dir(tx)
        ensure_cleanup_intent(root, scope, cleanup)
        cleanup_directories(root, cleanup)
        (tx / 'journal.json').unlink()
        sync_dir(tx)
        for item in tx.iterdir(): item.unlink()
        tx.rmdir()
        sync_dir(tx.parent)
        cleanup_directories(root, cleanup)
        return cleanup
    except Exception:
        try:
            recover_locked(root, scope)
        except (CDFError, OSError):
            pass
        raise


def private_ignore_plan(root):
    """Validate and describe the durable private-state ignore policy."""
    if read_file(root, '.codex/cdf/.gitignore') is not None:
        raise CDFError('PATH_COLLISION', 'Nested ignore rules could expose private state.', ['.codex/cdf/.gitignore'])
    existing = read_file(root, IGNORE)
    data = existing or b''
    if IGNORE_START in data or IGNORE_END in data:
        if data.count(IGNORE_START) != 1 or data.count(IGNORE_END) != 1 or IGNORE_BLOCK not in data:
            raise CDFError('PATH_COLLISION', 'CDF private ignore rules were modified.', [IGNORE])
        # Rules must be last, so later negations cannot expose private data.
        if data[data.index(IGNORE_BLOCK) + len(IGNORE_BLOCK):].strip():
            raise CDFError('PATH_COLLISION', 'CDF private ignore rules must be last.', [IGNORE])
        return None
    new = data + (b'\n' if data and not data.endswith(b'\n') else b'') + IGNORE_BLOCK
    return {'path': IGNORE, 'operation': 'add' if existing is None else 'update',
            'before_sha256': digest(existing), 'after_sha256': digest(new),
            '_before': existing, '_after': new}


def ensure_private_ignore(root):
    """Publish ignore rules before creating any recoverable private state."""
    planned = private_ignore_plan(root)
    if planned is None:
        return
    existing, new = planned['_before'], planned['_after']
    mkdir_durable(root, '.codex')
    if read_file(root, IGNORE) != existing:
        raise CDFError('CONCURRENT_MUTATION', 'Ignore file changed during setup.', [IGNORE])
    write_atomic(safe(root, IGNORE), new, mode(root, IGNORE) or 0o644)


def perform(root, scope, action, *, dry=False, enable=(), disable=(), src=ROOT, release_modified_skills=False):
    if not dry and (os.name != 'posix' or not hasattr(os, 'fchmod')):
        raise CDFError('UNSUPPORTED_PLATFORM', 'Mutating operations require a POSIX platform.')
    if scope not in ('project', 'global'): raise CDFError('INVALID_REQUEST', 'Unknown scope.')
    if action == 'recover':
        if safe(root, LOCK).exists():
            raise CDFError('CONCURRENT_MUTATION', 'CDF lock exists; inspect the current operation before retrying.', [LOCK])
        preview = recover_locked(root, scope, True)
        if preview['state'] == 'absent':
            return preview
        ignore_op = private_ignore_plan(root)
        if dry:
            if ignore_op:
                preview['planned_actions'].insert(0, {k: v for k, v in ignore_op.items() if not k.startswith('_')})
            preview['warnings'].append('The private-state ignore policy remains after recovery.')
            return preview
        ensure_private_ignore(root)
        with Lock(root):
            result = recover_locked(root, scope)
        cleanup = result.pop('_cleanup_directories', [])
        finish_cleanup(root, scope, cleanup)
        return result
    if action not in ('install', 'upgrade', 'uninstall'): raise CDFError('INVALID_REQUEST', 'Unknown action.')
    if release_modified_skills and action != 'uninstall':
        raise CDFError('INVALID_REQUEST', 'Releasing modified skills is only valid during uninstall.')
    if set(enable) & set(disable): raise CDFError('INVALID_REQUEST', 'Cannot enable and disable the same extra.')
    def plan():
        old = manifest_read(root, scope)
        source_version = _version(src) if action in ('install', 'upgrade') else None
        if old and action == 'upgrade':
            try:
                older = _version_key(source_version) < _version_key(old['framework_version'])
            except ValueError as exc:
                raise CDFError('MANIFEST_UNSUPPORTED', f'Cannot safely compare installed version: {exc}', [MANIFEST]) from exc
            if older:
                raise CDFError('MANIFEST_UNSUPPORTED', 'Refusing to downgrade an installed CDF version.', [MANIFEST])
        extras = set(old['selected_extras']) if old and action == 'upgrade' else set()
        extras.update(enable)
        extras.difference_update(disable)
        ops, new, preserved, warnings = changes_plan(root, scope, action, extras, src, release_modified_skills)
        if new is not None and action in ('install', 'upgrade'): new['framework_version'] = source_version
        return ops, new, preserved, warnings
    if dry:
        if safe(root, LOCK).exists():
            raise CDFError('CONCURRENT_MUTATION', 'CDF lock exists; inspect the current operation before retrying.', [LOCK])
        ops, new, _, warnings = plan()
        if action == 'uninstall' and new is None and not ops and read_file(root, MANIFEST) is None:
            return public_plan(root, scope, action, ops, warnings)
        ignore_op = private_ignore_plan(root)
        if ignore_op:
            ops.insert(0, ignore_op)
        warnings.append('The private-state ignore policy remains after uninstall and recovery.')
        return public_plan(root, scope, action, ops, warnings)
    # Fail deterministic collisions before creating any lock or directories.
    ops, new, _, _ = plan()
    if action == 'uninstall' and new is None and not ops and read_file(root, MANIFEST) is None:
        return {'schema': 1, 'state': 'absent', 'preserved': []}
    private_ignore_plan(root)
    ensure_private_ignore(root)
    with Lock(root) as lock:
        ops, new, preserved, warnings = plan()
        if action == 'uninstall' and new is None and not ops and read_file(root, MANIFEST) is None:
            return {'schema': 1, 'state': 'absent', 'preserved': []}
        cleanup = transact(root, scope, action, ops, new, lock.parent_created)
        result = {'schema': 1, 'state': 'partial' if new is not None and action == 'uninstall' else ('absent' if action == 'uninstall' else 'installed'),
                  'preserved': preserved, 'warnings': warnings}
    finish_cleanup(root, scope, cleanup)
    return result


def status(root, scope):
    if safe(root, TX).exists() or safe(root, CLEANUP).exists() or safe(root, LEGACY_CLEANUP).exists():
        issues = [p for p in (TX, CLEANUP, LEGACY_CLEANUP) if safe(root, p).exists()]
        try:
            recover_locked(root, scope, dry=True)
        except CDFError as exc:
            issues.extend(exc.paths)
        return {'schema': 1, 'state': 'recovery-required', 'scope': scope, 'files': 'unverified', 'managed_block': 'unverified', 'skills_discovery': 'unverified', 'native_agents': 'unverified', 'mcp': 'not_managed', 'issues': sorted(set(issues)), 'next_action': 'Inspect the reported paths and run recover --dry-run.'}
    m = manifest_read(root, scope)
    issues, block_state = [], 'absent'
    if m:
        for p, info in m['owned_files'].items():
            if digest(read_file(root, p)) != info['sha256'] or mode(root, p) != info['mode']: issues.append(p)
        for p, info in m['managed_blocks'].items():
            try:
                content = read_file(root, p)
                start, end = block_span(content or b'')
                if digest(content[start:end]) != info['sha256']: raise ValueError()
                block_state = 'clean'
            except (CDFError, ValueError):
                issues.append(p)
                block_state = 'modified'
    if safe(root, LOCK).exists(): issues.append(LOCK)
    return {'schema': 1, 'state': m['state'] if m else 'absent', 'scope': scope,
            'files': 'modified' if issues else ('clean' if m else 'absent'), 'managed_block': block_state,
            'skills_discovery': 'unverified', 'native_agents': 'unverified', 'mcp': 'not_managed',
            'issues': sorted(set(issues)), 'next_action': 'Resolve reported issues.' if issues else 'Start a fresh trusted Codex session and verify skill and agent discovery.'}


def legacy_report(root, scope):
    agents = '.codex/AGENTS.md' if scope == 'global' else 'AGENTS.md'
    old_manifest = '.codex/delivery-framework/manifest.json'
    candidates = [agents, old_manifest, '.codex/delivery-framework/model-policy.toml', '.codex/delivery-framework/roles.json', '.codex/config.toml']
    found = [p for p in candidates if safe(root, p).is_file()]
    result = {'schema': 1, 'state': 'report', 'scope': scope, 'target': str(root), 'detected_paths': found,
              'legacy_marker_detected': check_legacy(root, agents), 'legacy_manifest': None,
              'next_action': 'Inspect old status/recovery, preserve your files and model preferences, use the old uninstaller, then inspect v2 install --dry-run.',
              'steps': ['Inspect v0.6 status and recover any interrupted transaction.', 'Back up managed instructions, configuration, model policy and local edits.', 'Run v0.6 uninstall --dry-run and resolve conflicts before using its uninstaller.', 'Run v2 install --dry-run and inspect collisions.', 'Install v2 and verify in a fresh trusted session.']}
    raw = read_file(root, old_manifest)
    if raw is not None:
        try:
            old = json.loads(raw)
            if not isinstance(old, dict): raise ValueError('manifest is not an object')
            status = {'version': old.get('framework_version'), 'state': old.get('state'),
                      'owned': {}, 'reused': {}, 'generated_agents': [],
                      'external_dependency_paths': [], 'external_mcp': None, 'warnings': []}
            for field, out in [('files', 'owned'), ('reused', 'reused')]:
                mapping = old.get(field, {})
                if not isinstance(mapping, dict): raise ValueError('invalid path map')
                for path, recorded_hash in mapping.items():
                    try:
                        if not isinstance(recorded_hash, str) or not HEX.fullmatch(recorded_hash):
                            raise ValueError('invalid hash')
                        actual = read_file(root, path)
                        status[out][path] = 'missing' if actual is None else 'clean' if digest(actual) == recorded_hash else 'modified'
                        if path.startswith('.codex/agents/'): status['generated_agents'].append(path)
                        if 'codebase-memory' in path: status['external_dependency_paths'].append(path)
                    except (CDFError, ValueError, TypeError):
                        status['warnings'].append('Unsafe or malformed legacy path: ' + str(path))
            external = old.get('external_mcp')
            if external is not None:
                try:
                    if not isinstance(external, dict) or set(external) != {'path', 'sha256', 'config'}:
                        raise ValueError('invalid external MCP metadata fields')
                    path, sha, config = external['path'], external['sha256'], external['config']
                    if (not isinstance(path, str) or not Path(path).is_absolute() or '..' in Path(path).parts
                            or not isinstance(sha, str) or not HEX.fullmatch(sha)
                            or not isinstance(config, dict) or config.get('command') != path
                            or set(config) - {'command', 'args', 'enabled', 'startup_timeout_sec', 'tool_timeout_sec'}
                            or not isinstance(config.get('args', []), list)
                            or any(not isinstance(arg, str) for arg in config.get('args', []))
                            or type(config.get('enabled', True)) is not bool
                            or any(type(config[key]) not in (int, float) or config[key] < 0
                                   for key in ('startup_timeout_sec', 'tool_timeout_sec') if key in config)):
                        raise ValueError('invalid external MCP path, digest or config')
                    # The legacy external binary remains user-owned. Its path is
                    # reported as metadata only; never stat, follow, open or run it.
                    status['external_mcp'] = {'path': path, 'sha256': sha,
                                              'ownership': 'external-unowned',
                                              'verification': 'not-checked'}
                except (TypeError, ValueError) as exc:
                    status['external_mcp'] = {'state': 'invalid', 'verification': 'not-checked'}
                    status['warnings'].append(str(exc))
            result['legacy_manifest'] = status
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            result['legacy_manifest'] = {'state': 'unreadable', 'warning': str(exc)}
    return result
