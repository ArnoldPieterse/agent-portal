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
