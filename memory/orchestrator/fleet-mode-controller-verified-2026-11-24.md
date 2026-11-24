# Fleet Mode Controller - Verified 2026-11-24

## What was built
`memory/orchestrator/fleet_mode.py` (204 LOC) - determines fleet mode from goal completion % + time-since-last-activity.

## Logic
- **WORK**: any agent has open goals (pct < 100%)
- **MAINTENANCE**: all reached, < 6h since last activity
- **IDLE**: all reached, > 6h since last activity

## Activity detection
Scans key JSONL logs for most recent mtime: scheduler-log, fleet-snapshots, decision-log, autoloop.jsonl.

## Verification (4 test cases)
| goal_pct | elapsed | expected | actual |
|----------|---------|----------|--------|
| 99%      | 0.5h    | WORK     | WORK ✓ |
| 100%     | 2.0h    | MAINTENANCE | MAINTENANCE ✓ |
| 100%     | 7.0h    | IDLE     | IDLE ✓ |
| 50%      | 0.1h    | WORK     | WORK ✓ |

## Output file
`memory/ops/fleet-mode.json` - atomic write (tmp + os.replace), schema:
```json
{"mode":"WORK","timestamp":"ISO-8601","goal_pct":25.0,"goals_total":80,"goals_reached":20,"goals_open":60,"elapsed_since_activity_h":0.04,"activity_source":"memory/ops/scheduler-log.jsonl","threshold_idle_h":6.0}
```

## Usage
```bash
python memory/orchestrator/fleet_mode.py          # run + write
python memory/orchestrator/fleet_mode.py --dry-run  # print only
```
