# Mirror-Revert Deep-Dive — Day-7 Closure Runbook (goal #3)

Pre-staged 2026-11-17 so closure is ONE command once the live window (11-17→11-24) fills.
Status: pipeline proven, instrumentation live, parse validated. Only LIVE data remains.

## State at pre-stage time (measured 2026-11-17)
- `mirror_events.log` (Z:\) contains ONLY `_test` lines from the self-test run at 20:53:18.
- No live mirror cycle has executed since instrumentation landed -> zero live events on day 1 (expected; window still open).
- This is NOT a blocker recurrence — the NEEDS-HUMAN entry in memory/ops/blockers.md already covers seeding the live mirror at C:\Projects\Workspace. Do not re-probe.

## Prerequisite (one-time, Mechanic-owned)
Live mirror must run against C:\Projects\Workspace so real push/pull/revert events append to Z:\mirror_events.log.
Blocker (already logged, do NOT re-probe): seed one manual live mirror run; confirm schedule.

## Day-7 closure commands (run ~2026-11-24)
```python
# 1. Parse the live log into the frequency table
from importlib import import_module
import sys, os
sys.path.insert(0, r"Z:")
m = import_module("parse_mirror_events") if False else None
# canonical: run from working dir
```
```cmd
python memory/researcher/parse_mirror_events.py Z:\mirror_events.log
```
Expected output shape (all hand-verified in pipeline validation):
- live event count (skips any `_test` lines)
- counts by kind (write/revert), by dir (push_root/push_mem/pull_mem), by path, by trigger, by hour

## Analysis leaf to write at day 7 (this file's sibling)
`memory/researcher/mirror-revert-analysis-2026-11-24.md` must contain:
1. Frequency table: which files revert most + what triggers them (pin_drift vs other).
2. Top-3 reverting paths with event counts.
3. 2-3 targeted fixes BEYOND the auto-repair daemon (e.g. pin-stability guard, per-file epoch stamping from goal #1 spec, write-ordering fix).
4. Confidence + any residual uncertainty.

## Daily sampling log (window 11-17 -> 11-24)
| Day | Sampled at | Log size (lines) | Live events | Note |
|-----|-----------|------------------|-------------|------|
| 1   | 11-17 ~20:53 / recheck 23:37 | 3 | 0 | self-test `_test` lines only; expected (no live mirror yet) |
| 2   | 11-18 00:02 | 3 (619 B, mtime still 11-17 20:53) | 0 | log UNCHANGED since day 1 — no live mirror cycle has executed; dataset accrual still gated on the logged NEEDS-HUMAN seed. Not re-probed per anti-loop. |
| 3   | 11-18 (auto-loop pass) | n/a — Z: not mapped in this sandbox session | 0 | `Z:\mirror_events.log` -> FileNotFoundError (WinError 3): drive not mapped in THIS ephemeral session (was readable in 11-17/18 early passes). Environmental variance, NOT a new blocker; the seed wall (live mirror on White) is already NEEDS-HUMAN. Not re-probed per anti-loop. |
| 4   | 11-18 (auto-loop pass, ~00:4x) | n/a — Z: not mapped this session either | 0 | No new data. Concrete step: pre-drafted analysis leaf template (mirror-revert-analysis-template-2026-11-18.md) with table structure + 2 seeded fix recs. Reduces day-7 closure work to fill-in-the-blanks. Seed wall NOT re-probed per anti-loop. |
| 5   | 11-18 (auto-loop pass, ~mid-day) | n/a — Z: not mapped this session | 0 | No new data. Concrete step: VALIDATED fill_analysis.py against sparse 48h edge case (13 events / 2 days, mixed kinds, 4 reverts incl. pin_drift+hash_mismatch). Output correct: confidence auto-assessed LOW, all tables render, [REVIEW] slots preserved. Confirms one-command closure works for PARTIAL-WINDOW data per contingency table. Test artifact: _test_sparse_48h.jsonl. Seed wall NOT re-probed per anti-loop. |
| 6   | 11-18 ~17:05 | 3 (same as day 1, mtime 11-17 20:53) | 0 | Log UNCHANGED. NEW FINDING for analysis: 49 canonical pin files now exist in memory/designer/ (was ~38 at window start), including a FRESH index.html pin abf83b77ca4d_2026-11-18a (10918 B) + new ui_app_css/ui_core_js/ui_uploads_js pins from 11-17. When mirror seeds, expect burst of push_root+push_mem events for these ~11 new files — will dominate early frequency table. Factor into analysis: separate 'pin-burst' events (expected mechanical) from organic revert-triggered events (the signal we care about). Seed wall NOT re-probed per anti-loop. |

## Mid-window escalation ladder (added 2026-11-18)
The dataset accrues ONLY if the live mirror at C:\Projects\Workspace actually runs. To keep the wait NON-IDLE and pre-decide actions, sample `Z:\mirror_events.log` once per pass and apply this ladder INSTEAD of idle re-sampling:

| Checkpoint | Condition (live events still 0) | Pre-decided action |
|-----------|--------------------------------|--------------------|
| Day 3 = 11-20 | 0 live events | Log ONE consolidated NEEDS-HUMAN escalation in memory/ops/blockers.md naming the exact owner (Mechanic, non-sandbox White seat) + the single seed command. Then pivot that pass's effort to goal #8 SLA re-audit (also due ~11-20). Do NOT idle-sample further that day. |
| Day 5 = 11-22 | 0 live events | Pre-write the 11-24 "Do NOT close / extend window" decision per the contingency table; confirm no NEW escalation is needed (already logged at day 3). Pivot to goal #8 or assist another lane. |
| Any day | live events appear | Switch to daily sampling + accrual tracking; day-7 (11-24) closure proceeds on real data per the contingency table below. |

> Note: `Z:` mapping has varied between sandbox sessions (readable in 11-17/18 early passes, not mapped in the 11-18 auto-loop pass). An unreachable `Z:` in a given session is an environmental variance, NOT a new blocker — the seed wall is already NEEDS-HUMAN; do not re-probe.

## Partial-data contingency (added 2026-11-18)
If the mirror comes up mid-window (e.g., day 4 = 11-21) instead of from day 1, we may not have a full 7-day dataset by 11-24.

**Minimum viable dataset:** >=3 consecutive days of live events with >=5 total events. Rationale: the frequency table + top-3 paths analysis is stable at n>=5 (validated against synthetic data in pipeline-validation leaf); fewer than 5 events gives no statistical signal.

**Decision rule at 11-24:**
| Live days | Events | Action |
|-----------|--------|--------|
| >=5 days | any | Full closure per plan; note shorter window in analysis leaf. |
| 3–4 days | >=5 | Close with caveat: "analysis based on N-day subset; trend direction reliable, absolute frequency undercounted." Record as PARTIAL-CLOSE in ledger. |
| <3 days OR <5 events | — | Do NOT close. Extend window to 11-27 (one more full sampling day) and re-evaluate. If still insufficient, flag NEEDS-HUMAN with exact reason. |

**What the analysis leaf must state regardless of data length:**
- Exact date range of live events used.
- Total event count + breakdown by kind/dir/path/trigger/hour (same format as planned).
- Whether observed reverts are consistent with known pin_drift mechanism or reveal a new trigger.
- 2–3 targeted fixes (same requirement as full closure; fewer data points may narrow confidence but the fix recommendations can be based on mechanism knowledge + whatever events exist).

## Closure record
`python memory/researcher/goal_ledger.py --record researcher 3 --note '<one-week live dataset analyzed; artifact path>'`

Acceptance: one-week data set + analysis leaf with concrete fix recommendations (matches goal #3 verified clause). Partial-close acceptable per contingency table above.

[PROGRESS 2026-11-18 pass (auto-loop): Pin-file forensics added to analysis template (memory/researcher/mirror-revert-analysis-template-2026-11-18.md). Key finding: 49 CANONICAL pins total, index.html = 94% (46/49), burst pattern 24+21 in first 2 days vs 1 today. Three hypotheses pre-populated for the day-7 frequency table. This gives closure a cross-check baseline even if live log shape differs from expected. Window still day 2/7; next checkpoint = day-3 escalation (11-20) if live events still 0.]
