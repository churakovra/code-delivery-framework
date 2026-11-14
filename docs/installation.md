# Installation and removal

CDF is installed in Codex as a native plugin. The portable profile is the standard choice: eleven standalone skills, no hooks, no native roles, and no managed `AGENTS.md`. The optional desktop-controlled profile packages the same skills with metadata observation hooks. Do not enable both profiles together.

Skills and hooks do not provide a security boundary. Check model availability and host integration in the intended Codex client. Use Python 3.11 or newer on POSIX to build the package.

## Build and install

Choose a marketplace directory, build the portable plugin into it, and copy the example catalog:

```sh
mkdir -p /path/to/marketplace/build /path/to/marketplace/.agents/plugins
python3 scripts/package_cdf_plugin.py --profile portable --output /path/to/marketplace/build/cdf-plugin-portable
cp templates/cdf-marketplace.example.json /path/to/marketplace/.agents/plugins/marketplace.json
```

The example catalog points to `./build/cdf-plugin-portable`. Keep that path or update the catalog to match the selected package. Register the local marketplace and add the plugin using the intended Codex executable and HOME:

```sh
codex plugin marketplace add /path/to/marketplace --json
codex plugin add code-delivery-framework@cdf-local --json
codex plugin list --json
```

Restart Codex. Use `$cdf` to invoke the kernel explicitly. Without a mention, Codex may select a relevant discovered specialist based on the request; installing the plugin does not force global CDF activation. The package script builds only; Codex performs registration and installation. These commands change the selected Codex home's plugin settings.

The package contains root `plugin.json`, assets, and eleven `skills/<name>/SKILL.md` entries. `--with-learning` adds two standalone skills; `--with-operator` adds explicit model calibration. Disabled extras are absent. The kernel includes the optional-subskill catalog. Plugin installation does not install native roles or third-party integrations.

## Optional native roles

`policies/native-agents.example.toml` contains editable candidates for the three standard Codex roles: `cdf_explorer`, `cdf_reviewer`, and `cdf_diagnostician`. Role setup is separate from plugin installation.

```sh
python3 scripts/cdf.py profile --target /path/to/project --policy policies/native-agents.example.toml --dry-run --json
python3 scripts/cdf.py profile --target /path/to/project --policy policies/native-agents.example.toml --check --json
python3 scripts/cdf.py profile --target /path/to/project --policy policies/native-agents.example.toml --apply --json
python3 scripts/cdf.py profile --target /path/to/project --rollback --dry-run --json
```

Preview is offline. Check queries advertised model and effort support; this does not prove a role loaded or ran. Apply checks capabilities again and reports `configured` with `runtime_routing: NOT_OBSERVED`. Unknown model/effort pairs block setup; there is no silent fallback. Role instructions inherit parent permissions and do not create a sandbox. Project roles require native project trust; CDF does not grant trust or change `config.toml`. Edited owned roles block updates/removal, and unowned conflicting role files are preserved. Rollback removes only role files created by this setup and its receipt; it does not restore an earlier profile.

If role setup is interrupted, inspect and apply transaction recovery against the same target:

```sh
python3 scripts/cdf.py recover --target /path/to/project --dry-run --json
python3 scripts/cdf.py recover --target /path/to/project --json
```

Global roles require explicit `--scope global --target /selected/home --home /selected/home`. Use this only for an intentionally selected home. Development and checks use disposable homes and project targets.

## Optional desktop observation

The `desktop-controlled` plugin profile adds three metadata-only hooks: SessionStart and CDF SubagentStart/Stop. Build it with:

```sh
python3 scripts/package_cdf_plugin.py --profile desktop-controlled --output /path/to/marketplace/build/cdf-plugin-desktop
```

Use the `code-delivery-framework-desktop` catalog name and point its source to the desktop package. Building does not register the plugin or grant hook trust. Review the individual hooks through Codex's native `/hooks` flow; trust them only if you accept their commands. Hook execution requires Python 3 on the host PATH. The hooks record allowlisted IDs, role, model, event, and timestamp to native plugin data. They do not read source, transcripts, commands, tool output, or assistant messages. A full log is preserved and reported as degraded. Runtime behavior, warnings, and overhead still require acceptance on the intended host.

Use the diagnostic command to inspect native hook discovery and event records:

```sh
python3 scripts/cdf.py doctor --target /path/to/project --runtime --codex /path/to/codex --json
python3 scripts/cdf.py doctor --target /path/to/project --runtime --codex /path/to/codex --plugin-data /explicit/native/plugin/data --session-id ID --json
```

Discovery distinguishes enabled/trusted configuration from actual events. Historical records establish past observations only, not current execution or skill application.

## Remove

Remove the selected plugin through Codex and remove an unused marketplace through Codex's native management commands or UI:

```sh
codex plugin remove code-delivery-framework@cdf-local --json
```

For desktop-controlled, remove `code-delivery-framework-desktop@cdf-local`. Roll back optional native role setup with `profile --rollback --dry-run`, then `profile --rollback` in the same scope. Event logs are retained in native plugin data; archive or remove them explicitly if desired. Use disposable homes and targets for development; do not change the normal HOME during development.

## Evaluation tooling and license

The optional evaluation runner and synthetic fixtures are maintained separately on local branch `codex/cdf-2-evaluation-tooling` at commit `ec6c789d0724558eda6402f1bedf8a8567ad640e`. Obtain it with:

```sh
git worktree add /path/to/cdf-evaluation-tooling codex/cdf-2-evaluation-tooling
```

The plugin does not depend on it. This repository has no selected root license. Before public distribution, the copyright owner must choose and add licensing terms. MIT is a common option for an open-source Python/skills project, but no license is assumed here.
