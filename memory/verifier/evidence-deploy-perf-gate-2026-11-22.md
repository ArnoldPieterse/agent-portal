# Deploy Perf Gate - 2026-11-22T05:58:21Z

## Steps
1. Baseline: kept valid (18/20 valid p50)
2. Fresh baseline captured: YES
3. schtask registered: NO (manual run required)
4. Initial gate check: exit 1

## Baseline file
`C:\Projects\Workspace\memory\verifier\perf-baseline.json`

## Next steps for goal #1 closure
- Run gate for 3 consecutive days (schtask handles this automatically)
- Negative test: deflate one endpoint p50 in a copy -> alert fires
- Record: `python memory/researcher/goal_ledger.py --record verifier 1`
