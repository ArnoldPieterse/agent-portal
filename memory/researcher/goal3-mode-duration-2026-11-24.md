# Researcher Goal 3: Mode Duration Tracker - COMPLETE

**Date:** 2026-11-24T00:03Z
**Script:** memory/researcher/mode_duration.py
**Output:** memory/ops/mode-durations.json

## What was built
- Python script that computes time spent in each fleet mode (WORK/MAINTENANCE/IDLE) over 7 days
- Primary source: mode-transitions.jsonl (doesn't exist yet); fallback: derive from model-load.jsonl episode grouping
- Flags anomalies: single mode episodes >6h without transition
- Ran successfully: 83.8h tracked, MAINTENANCE 83.8%, IDLE 16.2%, WORK 0%

## Verification
- Script runs without error on model-load.jsonl (802 lines)
- Output is valid JSON with mode_durations, episodes list, and anomalies array
- 5 anomalies detected (>6h single episode) - consistent with extended maintenance periods

## Key findings
- Fleet has NOT been in WORK mode in the last 7 days per model-load data
- Dominant state: MAINTENANCE (agents partially loaded/unreachable)
- When mode-transitions.jsonl is created (by Builder's fleet-mode writer), the script will use it automatically for more accurate measurements
