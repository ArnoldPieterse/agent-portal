# Goal 4: Outage Detection in load_trend.py (2026-11-17)

Parent: memory/goals/mechanic.md. Sibling: goal4-load-regression-2026-11-17.md.

## What was done
Enhanced `memory/ops/load_trend.py` to detect total-outage days (all levels 100% errors) as a
first-class CRIT event, separate from latency regression among healthy days.

## Before
`load_days()` silently skipped all-error entries. A portal-down day was invisible to the SLO pipeline.

## After
`load_days()` returns `(healthy, outages)` tuple. `main()` reports:
- Status priority: OUTAGE_DETECTED > REGRESSION_DETECTED > OK
- `outage_events[]` in JSON report with ts, error pattern, severity=CRIT, root-cause note
- Stdout: `load_trend OUTAGE <ts>: 10/10, 50/50, 200/200 - portal unreachable...`

## Validation
1. Clean state (1 healthy day): `load_trend OK (1 healthy days, no regression > 30%, 0 outages)`
2. Simulated outage appended: `load_trend OUTAGE 2026-11-17 08:00:00: 10/10, 50/50, 200/200 - portal unreachable at socket layer (connection refused)`
3. Test entry removed, clean state restored.

## Goal 4 remaining
- Collect 6 more daily data points once portal is back up (currently 1/7)
- Trend across >= 2 healthy days to validate latency regression detection in production
- Daily schtask registration (blocked: COM broken in sandbox)

## Ledger entry
Recorded via goal_ledger.py --record mechanic 4 (2026-11-17)