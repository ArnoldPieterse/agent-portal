<!-- PROVENANCE agent=archivist created=2026-11-20 trigger=goal9-posthook-wire -->
# Goal 9 - Post-Hook Wiring (2026-11-20)

## What was done
Added `_post_hooks()` to `memory_mirror.py` that runs `provenance.py --sweep` after every mirror cycle.
New files created by remote agents automatically get provenance headers on the next 5-min mirror tick.

## Live test result
```
[{'hook': 'provenance-sweep', 'rc': 0,
  'stdout': 'Provenance sweep [APPLIED]: 6765 files scanned\n  Injected: 3\n  Already had header: 5626\n  Errors: 0'}]
```

## Remaining for full closure
- `/api/memory/provenance?file=X` endpoint (egress-wall blocked; needs portal restart on White)
- This does NOT require re-probing the firewall - just a code change in agent_portal.py

## Files changed
- `memory_mirror.py`: +15 lines (`_post_hooks()` function + call in `main()`)