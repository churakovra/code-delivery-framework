"""Legacy installer compaction; native plugins retain standalone source skills."""
from __future__ import annotations

from pathlib import PurePosixPath
import re

PREFIX = '.agents/skills/'


def compact_skills(files, selected):
    """Keep relative module references intact, but expose only cdf/SKILL.md."""
    result = {}
    index = ['# CDF specialist modules', '',
             'Read only the guide matching the current task. Paths below are relative to this index.',
             'Names such as `cdf-debugging` in any guide refer to these modules, not separately installed skills.',
             'Use the local method when optional external skills or tools are unavailable.', '',
             '| Module | When to read | Guide |', '| --- | --- | --- |']
    modules = [name for name in selected if name != 'cdf']
    for name in modules:
        text = files[f'{PREFIX}{name}/SKILL.md'].decode('utf-8')
        header, body = text.split('---', 2)[1:]
        description = re.search(r'^description:\s*(.+)$', header, re.M)[1].strip('"')
        explicit = name == 'cdf-model-calibration'
        trigger = ('Explicit request for model calibration only. ' if explicit else '') + description
        index.append(f'| `{name}` | {trigger.replace("|", "/")} | [{name}]({name}/GUIDE.md) |')
    index.extend(['', 'Model calibration is never selected implicitly. Read it only when the user explicitly requests it.',
                  'Learning guides apply to explanation or teaching requests; they do not replace implementation.', ''])
    for path, contents in files.items():
        if not path.startswith(PREFIX):
            result[path] = contents
            continue
        name, relative = path[len(PREFIX):].split('/', 1)
        if name == 'cdf':
            result[path] = contents
            continue
        # Modules are methods, not discoverable skills. Their UI metadata and
        # icons belong only to the standalone source format.
        if relative.startswith(('agents/', 'assets/')):
            continue
        if relative == 'SKILL.md':
            relative = 'GUIDE.md'
            text = contents.decode('utf-8').split('---', 2)[2].lstrip()
            preface = ('CDF module `' + name + '`. Resolve other CDF module names through '
                       '[the module index](../index.md). Read local references relative to this guide.\n\n')
            if name == 'cdf-model-calibration':
                preface += 'Read this module only for an explicit user request for model calibration.\n\n'
            contents = (preface + text).replace(
                '`.codex/cdf/subskills.catalog.json` in the installation target or configured home',
                '`../../subskills.catalog.json` relative to this guide').encode('utf-8')
        if PurePosixPath(relative).name == 'SKILL.md':
            raise ValueError('Nested discoverable skill in a CDF module')
        result[f'{PREFIX}cdf/modules/{name}/{relative}'] = contents
    index_path = f'{PREFIX}cdf/modules/index.md'
    result[index_path] = '\n'.join(index).encode('utf-8')
    kernel_path = f'{PREFIX}cdf/SKILL.md'
    kernel = result[kernel_path].decode('utf-8')
    routing = '''## Specialist methods
Read [the module index](modules/index.md) and then the relevant guide before applying a specialist method. Do not load every module. The index supplies triggers for requirements, research, backend, frontend, UI design, debugging, documentation, review, verification, and any selected extras.
CDF module names in guides refer to files in this folder; do not require separately discovered skills. The optional candidate catalog is `subskills.catalog.json` in this CDF folder; it never authorizes automatic installation. Pass the needed guide path and accepted scope to a reviewer or diagnostician. Model calibration requires an explicit user request.

'''
    kernel = kernel.replace('## Optional subskills', routing + '## Optional subskills') if '## Optional subskills' in kernel else kernel + '\n' + routing
    result[kernel_path] = kernel.encode('utf-8')
    result[f'{PREFIX}cdf/subskills.catalog.json'] = files['.codex/cdf/subskills.catalog.json']
    return result
