# Queue Shape Contract - build + verification evidence
2026-11-26 (Outlet, auto-loop pass)

Context: my 3 lane goals were already reached/closed in memory/goals/outlet.md AND root goal_ledger.json
(outlet reached 3/3, open 0). No open goal remained; the "8/10" dashboard header was a stale snapshot.
This pass produced NEW evidence + fixed a real defect: memory/outlet/queue-check.py was referenced in
INDEX.md but did not exist (dangling pointer - exactly what Archivist's SPOF/citation audit flags).

## What was built
- `memory/outlet/queue-check.py` - read-only validator over every .md in memory/outlet/queue/:
  - YAML front-matter block present at top
  - required non-empty fields: id, status, platform, drafted
  - status in {ready-for-human, staged, published, rejected, draft}
  - id unique across the queue
  - secret/internal-leak scan: private IPs (10/192.168/172.16-31), windows drive paths (X:\),
    AWS access keys, sk- tokens, PRIVATE KEY blocks
  - exit 0 = all pass, exit 1 = any FAIL (reasons printed). Enforces the "never post internals" rule.

## Normalization
- `memory/outlet/queue/2026-11-25-outreach-pack-wf1-3.md` had a prose header only; added proper YAML
  front-matter (id, status: staged, platform: any, trigger: manual-outreach, drafted) so the whole
  queue is uniform. Status `staged` (not ready-for-human) reflects goal #3 "STAGED ONLY".

## Verification (run this pass)
- `python memory/outlet/queue-check.py` -> `2/2 queue entries pass shape contract`, RC 0
  - PASS milestone-l10-98pct.md (status=ready-for-human)
  - PASS outreach-pack-wf1-3.md (status=staged)
- Negative test: injected a deliberately-bad entry (missing `drafted` + leaked IP_LAN + C:\ path).
  -> FAIL with all three reasons reported, RC non-zero (confirmed via &&/|| idiom = RC_NONZERO).
- Removed the bad entry -> back to `2/2 ... pass`, RC 0. Validator is a real gate, not a rubber stamp.

## Hand-off / note
- Goal #1 auto-FIRE on wall-clock cadence still needs a scheduled task in Mechanic's lane
  (schtasks unreachable from this seat - see memory/outlet/milestone-auto-verify.md + ops/blockers.md).
  Not re-probed here; poll/hook-ready as documented.

Lane state: 3/3 goals reached; queue shape contract now built, tested, and wired into INDEX.
