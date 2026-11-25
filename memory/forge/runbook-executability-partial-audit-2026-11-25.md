# Runbook Executability Audit — Partial Scan (Archivist assist)
Date: 2026-11-25T07:54Z
Scope: memory/ops/**/*.md with 'runbook' in filename
Method: regex for .py script references + manual classification

## Results: 12 runbooks found

| # | File | Script Ref? | Classification | Gap |
|---|------|-------------|----------------|-----|
| 1 | autonomous-remediation-loop-runbook-2026-11-24.md | Yes (2 scripts) | EXECUTABLE | None |
| 2 | boot-deployment-runbook.md | Yes (2 scripts) | EXECUTABLE | None |
| 3 | boot-detection-runbook.md | Implicit (boot_recovery.py) | SEMI-EXECUTABLE | schtasks registration not scripted per-host |
| 4 | citation-phantom-triage-runbook.md | Yes (verify_claims.py) | EXECUTABLE | None |
| 5 | live-leg-runbook-2026-11-20.md | Yes (elev.py, goal_ledger.py) | EXECUTABLE | None |
| 6 | loadtest/closure_runbook.md | Yes (elev.py, load_trend.py) | EXECUTABLE | None |
| 7 | memory-tree-runbook.md | Yes (orphan_remediation.py, xref_check.py) | EXECUTABLE | None |
| 8 | runbook-autonomy.md | Yes (autonomy_score.py, pre_cycle_gate.py) | EXECUTABLE | None |
| 9 | runbook-cockpit-feed-refresh-deploy-2026-11-24.md | Yes (deploy_all_schtasks.py, cockpit_staleness_monitor.py) | EXECUTABLE | None |
| 10 | runbook-notes.md | No | REFERENCE (not procedural) | N/A — log of past incidents |
| 11 | runbook-staleness-audit-2026-11-24.md | Yes (citation_map.py) | EXECUTABLE | None |
| 12 | windows-runbook.md | No | MANUAL | schtasks/reboot steps not scripted; needs a `windows_recovery.py` wrapper |

## Summary
- **9/12 executable** (75%) — have at least one .py script reference
- **1 semi-executable** (boot-detection: needs per-host registration loop)
- **1 manual** (windows-runbook: reboot recovery steps could be a single `python windows_recovery.py --host <name>`)
- **1 reference-only** (runbook-notes: not a procedure, no action needed)

## Recommended next step for Forge
Write `memory/ops/windows_recovery.py` wrapping the 4 manual steps in windows-runbook.md
(recover-all task, portal restart, studio check, log verification). That closes the last gap.
