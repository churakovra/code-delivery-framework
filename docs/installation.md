# Installation, migration and removal

CDF 2.0.0-rc1 is a prerelease candidate. Use Python >=3.11 on POSIX.
Skills and hooks do not provide a security boundary. Model availability and
host integration must be checked on the intended account/client.

## Choose one installation

Choose **portable** for eleven standalone skills, **desktop-controlled** for the
same skills plus optional metadata hooks and separately installed native roles,
or **legacy** for the compatible one-entry installer. Do not enable two modes
in the same project/HOME. Inspect both project and global legacy copies first.

For native plugins, using the intended Codex executable and HOME:

```sh
codex plugin marketplace add /absolute/path/to/marketplace --json
codex plugin add code-delivery-framework@cdf-local --json
codex plugin list --json
```

For controlled mode, choose `code-delivery-framework-desktop@cdf-local`
instead of the portable plugin. Restart Codex. Review the three individual hooks
in native `/hooks`; trust them manually only if you accept their commands.
Untrusted/disabled hooks remain degraded; CDF never grants trust. Hook execution
requires Python 3 on the host PATH. Portable has no hooks or native role setup.
Try `$cdf`, a named specialist, and an ordinary request without mentioning CDF.
Discovery and guide reads do not prove that the method improved the decision.

For the legacy installer, from the source checkout:

```sh
python3 scripts/cdf.py install --target /absolute/path/to/project --dry-run --json
python3 scripts/cdf.py install --target /absolute/path/to/project --json
python3 scripts/cdf.py status --target /absolute/path/to/project --json
```

This retains the compact layout, managed AGENTS block, ownership manifest and
existing recovery engine. It does not install a standalone plugin. Optional `--with-learning` / `--with-operator` select extras. For native plugins,
select extras explicitly when building the package.

## Migrate from 1.5.0 and roll back

Preserve the exact old distribution and a backup of the target before mutation.
For the compatible legacy path, run current `status`, `upgrade --dry-run`, then
`upgrade` against the old target. Use `--scope global --home /selected/home` only
for an intentionally selected home matching `--target`. The installer preserves
user text outside managed blocks and refuses edited owned files during upgrade.
After interruption, inspect `recover --dry-run`, then `recover`; do not delete
journals or force through conflicts. Pinned 1.5 tests cover both scopes and
recovery after an actual first write, including file bytes and modes.

For legacy-to-plugin migration, preview `uninstall --dry-run`, resolve modified
files, uninstall the owned legacy setup, then enable one native plugin. Inspect
native discovery to ensure no bare `cdf` or duplicate plugin remains. For
rollback, remove the plugin first, then reinstall the preserved 1.5 distribution
into the clean target. Direct version downgrade through `upgrade` is refused.
Uninstall keeps modified files; `--release-modified-skills` explicitly releases
the modified skill folder rather than deleting it. Preserve it outside discovery
before enabling a replacement. CDF never silently merges conflicting guidance.

Native roles use a separate existing CLI workflow:

```sh
python3 scripts/cdf.py profile --target /absolute/project --policy policies/native-agents.example.toml --profile balanced --dry-run --json
python3 scripts/cdf.py profile --target /absolute/project --policy policies/native-agents.example.toml --profile balanced --check --codex /absolute/codex --json
python3 scripts/cdf.py profile --target /absolute/project --policy policies/native-agents.example.toml --profile balanced --apply --codex /absolute/codex --json
```

The check is advertised availability, apply is CONFIGURED, and actual child
execution is a separate observation. Unavailable model/effort pairs block apply;
edit the candidate policy explicitly rather than accept silent fallback.
Role instructions inherit parent permissions; read-only text is not a sandbox.
Project roles require native project trust; CDF does not grant it. Profile
rollback removes only CDF-created role setup, not a history of successful profiles.
Conflicting or edited roles are preserved and require reconciliation.

## Build the selected plugin

```sh
mkdir -p /absolute/path/to/marketplace/build
python3 scripts/package_cdf_plugin.py --profile portable --output /absolute/path/to/marketplace/build/cdf-plugin-portable
```

Copy `templates/cdf-marketplace.example.json` into
`/absolute/path/to/marketplace/.agents/plugins/marketplace.json`.
The catalog's local path must point to the selected package. For desktop, build
with `--profile desktop-controlled`, then change the catalog name to
`code-delivery-framework-desktop` and its source path to that package.
The builder refuses an existing output; it never registers or installs it.
Do not enable portable and desktop variants together.

## Observe and diagnose desktop hooks

SessionStart returns compact bundle/profile metadata. Role-file detection is not
availability, routing or skill application. Subagent events record only supplied
IDs/model; effort stays unknown. No source/transcript or command content is logged.

```sh
python3 scripts/cdf.py doctor --target /absolute/project --runtime --codex /absolute/codex --json
python3 scripts/cdf.py doctor --target /absolute/project --runtime --codex /absolute/codex --plugin-data /explicit/native/plugin/data --session-id ID --json
```

Native discovery distinguishes enabled/trusted configuration from actual events.
Missing/untrusted/disabled/error/full-log states are degraded. Historical events
do not establish current execution. Validate SessionStart context and overhead on
your host; there is no full-host latency or enforcement guarantee.

## Disable and remove

Disable hooks through native `/hooks`; remove the selected plugin with
`codex plugin remove NAME@cdf-local --json`. Remove an unused marketplace through
native management commands/UI. Preview `profile --rollback --dry-run`, then
`profile --rollback` in the same scope; use existing `recover` if interrupted.
Legacy installations use `uninstall --dry-run` then `uninstall`.

Events stay in native `PLUGIN_DATA/events.jsonl`, capped at about 1 MiB with
mode 0600. A full log is preserved and degraded, never deleted automatically.
Explicitly archive/remove it to resume observation. Use disposable homes/targets
for development; do not change the normal HOME without authorization.
