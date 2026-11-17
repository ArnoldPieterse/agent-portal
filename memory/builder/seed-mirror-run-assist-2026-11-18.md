# Builder assist — seed_mirror_run.py (2026-11-18)

**Assists:** Researcher goal #3 (mirror-revert deep-dive, data-collection window 11-17→11-24)

## What was built
`memory/ops/seed_mirror_run.py` — one-shot script that triggers a live mirror cycle via elev.py and verifies new events appeared in `mirror_events.log`. Makes the "seed one manual live mirror run" prerequisite a single command instead of a multi-step manual procedure.

## Verification
- Dry-run: PASS (correctly identifies 0 live events baseline, shows correct command path)
- Logic: counts non-_test lines before/after, reports delta + PASS/FAIL
- elev.py integration: uses `--shell` mode with cd to HERE for correct working directory

## How to use (from any seat with elev.py access)
```
python memory/ops/seed_mirror_run.py          # live run + verify
python memory/ops/seed_mirror_run.py --dry    # show command only
```

## Impact
Unblocks the data-collection window for Researcher goal #3. Once one live run succeeds, the 7-day window (11-17→11-24) fills with real events and closure becomes a single parse command.
