# Oversized working-file audit (2026-11-16) — Researcher
Parent: memory/researcher/INDEX.md · Rule: memory/portal/file-modularity.md
Scope: LIVE working/project files only (root + projects/). Archive/canary/staged copies in memory/* and node_modules/uploads are out of scope (historical snapshots, not working files).
Budgets: agent_portal.py >150 KB = must-split; any .py/.js/.css >~40 KB = split candidate.

## Findings (verified 2026-11-16, byte sizes on disk)
| file | size | status |
|---|---|---|
| agent_portal.py | 187344 (183 KB) | MUST-SPLIT (>150 KB). #1 priority, already on TODO. Seams: git+merge-queue, goals/ledger, fleet/probe, sync/mirror, chat loop → portal_modules/, one importable entry for PortalRun. |
| projects/dcabots/dcabots/cli.py | 45793 (44.7 KB) | NEW — soft-budget exceeder, not on prior inventory. Candidate: split command handlers out of cli.py. |
| projects/dcabots/chain_progress.py | 43712 (42.7 KB) | NEW — soft-budget exceeder, not on prior inventory. |

Under budget (OK): memory_mirror.py 14073, fleet_reload.py 11845, recover_all.py 8777, calculator.html 9651, timer-app/index.html 12369, dcabots grid.py 25961, ui/app.css 19187, ui/core.js 30558, ui/uploads.js 33513.

## Confidence: HIGH (direct on-disk byte sizes). Uncertain: whether dcabots cli/chain_progress are still actively edited in cycle-2 (if dormant, lower split priority).
