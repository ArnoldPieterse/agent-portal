# Goal 9: Capacity Planning — Alert Threshold Configurable (2026-11-21)

## Change
Added configurable alert threshold system to `capacity_report.py`:
- `--alert-pct` CLI flag (default 90.0%)
- `--lead-hours` CLI flag (default 48h before predicted breach)
- `--save-config` persists to `capacity_config.json`
- `check_alerts()` function fires CRITICAL/WARNING alerts based on thresholds
- Report now includes "Alert Configuration" table + active alerts section

## Selftest
```
[selftest] PASS: 4 sections, 4 hosts, 29 rows, alert config + 3 alert tests
```
Tests verified:
1. Custom alert_pct=75 reflected in report output
2. CRITICAL alert fires when current_pct >= threshold
3. WARNING alert fires when predicted breach within lead_hours
4. No false alert at safe utilization (50%)

## Remaining for closure
- 7-day data accumulation (depends on probe schtask, same as Goal 1)
- Trend prediction accuracy test on historical data (needs >=3 real data points)

## Runbook note
`capacity_report.py` now supports: `python capacity_report.py --alert-pct 80 --lead-hours 72 --save-config`
Config persists to `capacity_config.json` in same directory.