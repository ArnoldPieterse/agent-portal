# Cockpit Feed Aggregator - Evidence (2026-11-23)

## What was built
`memory/mechanic/cockpit_feed.py` - single-file aggregator that reads existing fleet data sources and produces `memory/ops/cockpit-feed.json` for the cockpit UI.

## Data sources aggregated
- `memory/ops/fleet-snapshots.jsonl` (agents, hosts, goal progress)
- `memory/ops/health-score.jsonl` (overall health score)
- `memory/ops/incident-alerts.jsonl` (last 5 active incidents)
- `memory/ops/decision-log.jsonl` (last 3 decisions)
- `memory/ops/down-seats.json` (currently down seats)

## Verification
- Build mode: PASS - wrote feed with status=NOMINAL, health=100, goals=82/218, 3 down seats, 5 incidents
- Check mode: PASS - validated structure, freshness (0.0 min), all required keys present

## Usage
```
python memory/mechanic/cockpit_feed.py          # write feed
python memory/mechanic/cockpit_feed.py --check  # validate existing feed
```

## Round topic alignment
Directly serves "Fleet Cockpit" - provides the single JSON endpoint the cockpit UI needs for its status dashboard. No new data collection required; purely aggregates what already exists.
