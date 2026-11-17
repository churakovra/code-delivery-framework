# Install, update and inspect CDF

CDF is one native Codex plugin, `code-delivery-framework`, with 14 standard
skills and SessionStart, UserPromptSubmit and SubagentStart context hooks.
It requires Python 3.11+ and native plugin support. Technical checks cover the
POSIX client; Windows and other clients need independent acceptance.

## Install from GitHub

For PR #13, clone the candidate branch and build a local marketplace:

```sh
git clone --branch codex/cdf-2.1.0 https://github.com/churakovra/code-delivery-framework.git
cd code-delivery-framework
mkdir -p build/marketplace/.agents/plugins
python3 scripts/package_cdf_plugin.py --output build/marketplace/cdf-plugin
cp templates/cdf-marketplace.example.json build/marketplace/.agents/plugins/marketplace.json
codex plugin marketplace add "$PWD/build/marketplace" --json
codex plugin add code-delivery-framework@cdf-local --json
```

No distribution profile is required. The package retains source skills and
references, includes assets and bundled hooks, and excludes managed AGENTS
blocks, native roles and third-party installations. The output parent must
exist and the output directory must be new. Building alone does not register,
install or grant trust. Native plugin commands change the selected Codex home's
plugin settings; development probes use disposable homes only.

The official root manifest uses `extensions.com.openai.hooks`. A compatibility
overlay references the same hook file; the OpenAI loader selects one declaration,
not both. Known clients 0.167.0-alpha.4.1 and 0.169.0-alpha.11.1 ignore hooks
when root plugin.json exists. The builder detects the target `codex` on PATH and
emits compatibility-only layout for these versions, under the same identity.
Use `--codex /absolute/path/to/codex` for a different target. Offline builds
without a target produce the canonical root manifest plus fallback; discovery
on an unknown client must be checked, never assumed.

Old `--profile portable` and `--profile desktop-controlled` options remain
compatibility aliases, not distinct products. `--with-learning` is a no-op;
`--with-operator` explicitly adds calibration. If the previous desktop plugin
is installed, remove it explicitly with
`codex plugin remove code-delivery-framework-desktop@cdf-local --json` before
using the unified plugin. The packager never disables another installation.

## Trust and confirm

Restart Codex. Open `/hooks` in the CLI or Review hooks / Settings > Hooks in
the desktop app. Review and trust the three bundled commands. Updated scripts
may require renewed trust. CDF never grants trust, changes permissions or uses
bypass flags. Without trusted hooks, skills remain discoverable and `$cdf`
works explicitly, but persistent context is not delivered.

```sh
python3 scripts/cdf.py doctor --target "$PWD" --runtime --json
```

Doctor reports installed/enabled plugin, discovery of all 14 standard skills,
hook declarations, trust and duplicate registrations. Unknown trust is UNKNOWN.
No execution or method use is inferred from installation. If hooks are absent,
check the intended client, rebuild using its `--codex` path, reinstall and open
`/hooks`; do not treat skill discovery as hook readiness.

To inspect only a selected native plugin data directory/session:

```sh
python3 scripts/cdf.py doctor --target "$PWD" --runtime --plugin-data /explicit/native/plugin/data --session-id SESSION_ID --json
```

Use the plugin data directory supplied by the host, not a transcript directory.
`events.jsonl` contains only allowlisted event/session/time/context-hash metadata
and technical format/status fields. It stores no prompt, answer, source, model,
tool argument or transcript. Records are bounded to about 1 MiB and mode 0600.
Full/unsafe history is preserved; archive or remove it explicitly to resume
recording. Context stdout still works when metadata recording is unavailable.

`OBSERVED_HISTORY` proves a selected prior record, not current execution.
A context hash records stdout emission, not model receipt. Method application
stays NOT_OBSERVED without actual model evidence. Even trusted, discovered
hooks yield only READY_NOT_EXECUTION_PROOF. Native permissions remain the
execution boundary; CDF provides guidance, not enforcement.

## Update or remove

Fetch the desired repository revision with `git pull --ff-only`. Build into a
new marketplace directory (for example `build/marketplace-next`) using the same
commands above with that path, then remove the old cached plugin, register the
new local marketplace and add the plugin again:

```sh
codex plugin remove code-delivery-framework@cdf-local --json
codex plugin marketplace remove cdf-local
codex plugin marketplace add "$PWD/build/marketplace-next" --json
codex plugin add code-delivery-framework@cdf-local --json
```

Build successfully before removing the prior installation. Restart and review
hook trust after updating. To uninstall, use the same native `plugin remove`
command and remove an unused marketplace with
`codex plugin marketplace remove cdf-local`. No custom updater is installed.

## Optional roles and evaluation

Native roles remain explicit opt-in configuration through `scripts/cdf.py
profile`. Preview with `--dry-run`, query advertised support with `--check`,
apply with `--apply`, and remove created roles with `--rollback`. CDF does not
install these roles with the plugin. See the existing profile examples in the
README; a configured role is not proof of execution.

The existing [evaluation runner](../evals/README.md) now uses native plugin
packaging/installation for the current candidate. Historical snapshots stay
separate. No new behavioral cases or paid model runs are part of this change.
Manual effectiveness testing belongs to the user. Existing historical tests
that invoke removed legacy CLI commands need separate maintenance; production
install/status/upgrade/uninstall commands are not restored for those tests.
