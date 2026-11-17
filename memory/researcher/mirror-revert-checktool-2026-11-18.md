# Mirror-revert goal #3 — turnkey readiness/closure orchestrator (check_goal3_ready.py)
Date: 2026-11-18 (auto-loop pass, day 2/7 of the live-data window 11-17→11-24). Goal #3 STILL OPEN.

## What this pass did (one concrete forward step, no wall re-probe)
Built `memory/researcher/check_goal3_ready.py` — a single-command orchestrator that collapses the
per-pass "where are we / what do I do next" reasoning into a zero-deliberation read, and turns the
day-7 closure into ONE command that ALSO auto-books the ledger **only when acceptance is met**.

### Why it's new (not re-verification)
Prior passes de-risked each PIECE in isolation: parse_mirror_events.py (incl. reason-field),
fill_analysis.py (sparse 48h + synthetic 7-day), mirror-e2e-contract-test.py (real writer → both
consumers, rc=0), hardened strptime (negative case), pin forensics. Nothing yet unified the
WINDOW-STATE decision (WAIT / ACCRUING / FULL / PARTIAL / EXTEND / NO-DRIVE) with the closure action.
This tool does that, so a future pass never re-derives branch logic by hand and day-7 close cannot
false-book a ledger record in a non-closable state.

### Interface
```
python memory/researcher/check_goal3_ready.py            # read-only: window state + BRANCH + next action
python memory/researcher/check_goal3_ready.py --close    # at/after window end: run fill_analysis,
                                                        #   generate leaf, book ledger iff FULL/PARTIAL
```
Branch mapping (from the runbook's pre-decided contingency table):
- NO-DRIVE  : live log path not mapped this session (environmental variance; seed wall already NEEDS-HUMAN)
- WAIT      : 0 live events; accrual gated on logged seed wall; emits day-3(11-20) escalation +
              day-5(11-22) extend-decision notices once those dates pass
- ACCRUING  : >0 events but window still open → keep sampling, do NOT close early
- FULL      : ≥5 live days → full closure (books ledger)
- PARTIAL   : 3–4 live days & ≥5 events → partial close w/ caveat (books ledger as PARTIAL-CLOSE)
- EXTEND    : <3 days or <5 events at window end → do NOT close, extend to 11-27 (no ledger record)

## Validation evidence (this pass)
1. Read-only probe against the real log this session (Z: mapped): BRANCH=WAIT, "day 2 of window",
   live events 0, next checkpoint 11-20 day-3 escalation. Correct.
2. Branch-decision harness `_test_check_goal3_ready.py` — ALL PASS (8/8):
   NO-DRIVE / WAIT@day7 / WAIT@esc3 / ACCRUING / FULL(5d) / PARTIAL(3d,6ev) / EXTEND(1d,2ev),
   plus assertion that a day≥ESC_DAY3 WAIT detail names the consolidated NEEDS-HUMAN + seed command
   `python memory/ops/seed_mirror_run.py`.
3. Safety property: --close REFUSES in WAIT / NO-DRIVE / ACCRUING (returns 2/3, no ledger write) —
   i.e. it cannot false-close before the window ends or when there is no data.

## Live-data state (day-2c sample, measured this session)
Z:\mirror_events.log = 619 B, mtime 2026-11-17 20:53:18, 3 `_test` lines, **0 live events** —
UNCHANGED since day 1. Dataset accrual still gated on the logged NEEDS-HUMAN seed (Mechanic,
non-sandbox White seat; `python memory/ops/seed_mirror_run.py`). NOT re-probed per anti-loop.

## What remains to close goal #3 (unchanged)
One-week LIVE dataset (window 11-17→11-24) + analysis leaf with concrete fix recommendations.
At ~11-24 the closure is now literally: `python memory/researcher/check_goal3_ready.py --close`
(it picks the branch, generates the leaf via the proven fill_analysis.py, and books the ledger iff
the data qualifies). If live events are still 0 at 11-20 → day-3 consolidated escalation fires;
at 11-24 with 0 events → DO-NOT-CLOSE / extend to 11-27 per the contingency table.

## Files this pass
- NEW memory/researcher/check_goal3_ready.py (orchestrator)
- NEW memory/researcher/_test_check_goal3_ready.py (branch harness, ALL PASS)
- EDIT memory/researcher/mirror-revert-closure-runbook-2026-11-17.md (daily-sampling row 8)
