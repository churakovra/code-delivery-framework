# Changelog

## 2.0.1

- Make native Codex plugin installation the only supported CDF installation path.
- Keep legacy inventory and fixtures for historical ownership and migration evaluation.
- Remove legacy install, upgrade, status, and uninstall commands from the CLI; retain transaction recovery for optional native-role setup.
- Update installation guidance, plugin discovery checks, and skill references for the plugin-only path.

## 2.0.0 — stable source version

- Add decision-before-code reasoning, minimality critique and architecture method.
- Build eleven standalone portable skills while retaining legacy single-entry
  installs and owned-file migration/recovery behavior.
- Add explicit native profile preview/check/apply/removal over standard Codex
  agent TOMLs; distinguish catalog support, installed files and child execution.
- Add opt-in three-event Desktop metadata observation and native hook diagnostics;
  preserve historical logs and report full/unsafe history as degraded.
- Refine risk-based verification, solution review and bounded research packets.
- Add compact SessionStart version/profile detection without inferring routing.
- Document installation, migration, recovery, trust and removal.

This source version is prepared for local installation and user acceptance. Native
routing and Desktop observation have bounded evidence; broader host acceptance
and comparative benefit remain unestablished. No quality or usage-saving claim
is made. See docs/installation.md.
