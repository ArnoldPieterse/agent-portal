# Evidence - Milestone Auto-Draft Trigger (goal #6) reached 2026-11-26

## What was built
`memory/outlet/milestone_trigger.py` — watches two live sources and, when one crosses an
UPWARD threshold since the last draft, stages a milestone post into the queue in fleet
default voice. No invented numbers.

Live sources (single source of truth):
- fleet level  -> memory/levels.json        {"level": N, history[]}
- goal pct     -> memory/goals/next10.json   {"fleet":{"done","total","pct"}, "level_up_eta"}

Trigger rules: NEW-LEVEL (current > last-seen) OR PCT-STEP (floor(pct/10) band crossed up).
State file `memory/outlet/milestone_trigger_state.json` makes it idempotent (one post per
milestone; first run uses baseline level=0/step=0).

## Verification (all run 2026-11-26, commands + output below)
1. `python memory/outlet/milestone_trigger.py selftest` -> SELFTEST PASS
   - run1 fires (NEW-LEVEL + PCT-STEP) and writes a post
   - run2 idempotent: same state -> nothing drafted
   - run3 re-fires when level bumps 12->13 (new file written)
2. `python memory/outlet/milestone_trigger.py` (real, live data) ->
   drafted `queue/2026-11-26-milestone-level-12-90pct.md` from level 12 + 108/116=93.1%.
   Body states the real figure; math VERIFIED inline (108/116 = 93.1%);
   status=ready-for-human; fact-check section present; no IPs/paths/keys/secrets in body.
3. `python memory/outlet/queue_check.py` -> 3 entries, 0 violations; INDEX regenerated.
4. `python memory/outlet/voice_lint.py` -> 3 entries, 0 fails.

## Lane-hygiene fix made this pass (keeps goal #2 '0 violations' honest)
Pre-existing `queue/2026-11-25-red-host-restored.md` used a non-conformant `- **key:**` list
format and failed every queue_check key/section check (10 violations). Rewrote it to the
standard preamble-key + ##-sections shape, preserving its content. After the rewrite,
queue_check = 0 violations across all 3 entries.

## Hard-line compliance
Body contains no internal IPs, paths, keys or secrets. Post is staged only; nothing ships
without a human approving the queue entry.
