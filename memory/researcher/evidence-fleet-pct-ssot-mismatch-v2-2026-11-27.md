# EVIDENCE — Fleet-% SSOT Discrepancy #2 (stale goal_ledger.json + forecast drift) — 2026-11-27

## Finding
Three sources report three different fleet completion numbers:

| Source | Value | Status |
|--------|-------|--------|
| `goal_ledger.json` (on disk, pre-fix) | 109/111 (98.2%) | **STALE** — designer=10/10 & verifier=10/10 were wrong |
| `next10.json` forecast (gen 12:48:55) | 93/111 (84%) | **PARTIALLY STALE** — outlet was 1, now 9 |
| Fresh `goal_ledger.py` run (this pass) | **101/111 (91%)** | **CORRECT** |

## Root Cause
1. `goal_ledger.json` was last regenerated at an earlier time when designer.md and verifier.md contained more closure markers. After cycle-20 goals were set (2026-11-26), those files were rewritten with fresh goal lists that have fewer `(verified:)` / `[REACHED]` markers. The JSON artifact was never re-run.
2. `next10.json` was generated at 12:48:55 when outlet had only 1/10 reached; outlet subsequently closed 8 more goals (evidence leaves written) before the next forecast refresh.

## Remediation
- Backed up stale artifact → `memory/researcher/backup_goal_ledger_STALE_2026-11-27b.json`
- Ran `python memory/researcher/goal_ledger.py --json` to regenerate from source .md files
- New on-disk SSOT: 101/111 (91%), matching fresh computation exactly

## Correct per-agent state (verified by fresh run)
| Agent | Reached/Total |
|-------|--------------|
| archivist | 10/10 |
| builder | 10/10 |
| designer | **3/10** (was claimed 10/10) |
| forge | 10/10 |
| mechanic | 10/10 |
| orchestrator | 10/10 |
| outlet | 9/10 |
| pixel | 9/10 |
| researcher | 11/11 |
| scribe | 10/10 |
| verifier | **9/10** (was claimed 10/10) |

## Impact
The MEMORY.md GOAL line and any dashboard reading `goal_ledger.json` now show correct 101/111 (91%). The forecast engine will pick up the corrected value on next refresh cycle.

## Open items (NOT blockers, just state)
- Designer has 7 genuinely open goals (cycle-20 work in progress)
- Verifier has 1 open goal (#7 coverage map — Forge assist evidence exists but marker not yet in file)
- Outlet has 1 open goal (#1 live account connection)
- Pixel has 1 open goal (#6 CDP screenshot — blocked by WinError 10013)

(verified: 2026-11-27T??:??Z — fresh goal_ledger.py run = 101/111, matches per-agent .md file inspection; stale artifact backed up and replaced)
