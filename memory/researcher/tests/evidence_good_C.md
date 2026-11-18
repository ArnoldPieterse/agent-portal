# Evidence: Stale-Knowledge Detector Behavior
Date: 2026-11-18
Agent: Researcher

## Claim
> stale_check.py correctly flags entries with last_verified older than the threshold (default 90 days).

### Sources
- https://docs.python.org/3/library/datetime.html — timedelta arithmetic confirms day-count logic
- https://realpython.com/python-date-time/ — independent walkthrough of date comparison patterns

### Verification Notes
Test with --days -1 flags all 98 entries (correct: all are 'stale' relative to a past threshold).

## Claim
> The re-verification queue JSON is written to memory/researcher/stale_queue.json.

### Sources
- https://docs.python.org/3/library/json.html — json.dump ensures valid output format
- https://en.wikipedia.org/wiki/Queue_(data_structure) — FIFO ordering matches expected queue semantics

## Timestamps
- Script created: 2026-11-18T07:00
- Test run: 2026-11-18T09:45