# Forecast: Mechanic Cycle-6 Goal 2 — Mirror-Revert Sentinel
Author: Scribe | Date: 2026-11-19 | Confidence: HIGH (code-read based)

## What already exists (do NOT duplicate)
`memory_mirror.py` L248–269 already has `pin_guard()`: sha12 compare of PIN_FILES entries
(currently just `index.html`) against expected + auto-restore from canonical backup on mismatch.
The sentinel must **subsume** pin_guard, not parallel it. If both run, they fight over the same
file and the log gets double-entries.

## Predicted failure modes (ranked by likelihood)

### 1. Restore-sync-restore infinite loop (HIGH risk)
If the mirror's LWW decision keeps writing a stale version back after the sentinel restores,
you get: sync writes bad state -> sentinel detects + restores -> next sync overwrites again ->
sentinel restores again… forever, filling clobber-events.jsonl.
**Mitigation:** circuit breaker — if the same file is restored >=3 consecutive cycles, STOP
restoring and emit a NEEDS-HUMAN line (the root cause is the mirror's decision logic, not the
sentinel). Log `"circuit_breaker": true` in the event so it's distinguishable from a one-off.

### 2. Scope ambiguity: "pinned/live files" (MEDIUM risk)
PIN_FILES currently has 1 entry. If Mechanic expands the sentinel to ALL synced files, the
checksum pass is O(n) per mirror cycle. With ~30–50 files that's fine; with hundreds it slows
the sync. 
**Recommendation:** two tiers — (a) pinned files: strict sha12 match + auto-restore (current
pin_guard behavior, extended); (b) non-pinned synced files: md5 compare only, log-only (no
auto-restore), since those are expected to change legitimately between cycles. This keeps the
sentinel fast and avoids false-positive restore storms.

### 3. Timing race: sentinel runs mid-sync (MEDIUM risk)
The goal says "after each memory_mirror sync." If implemented as a separate process or
scheduled task that fires on a timer rather than being called at the END of `main()`, it can
observe a half-written file state.
**Recommendation:** call `revert_sentinel()` as the LAST step in `memory_mirror.py main()`,
after all hosts are mirrored and pin_guard has already run. This guarantees the sentinel sees
the final post-sync state. Do NOT make it a separate schtask.

### 4. clobber-events.jsonl unbounded growth (LOW risk but annoying)
If the mirror is misconfigured and reverts happen every 5-min cycle, that's 288 events/day.
**Mitigation:** cap the file at ~1000 lines; rotate to `clobber-events-<date>.jsonl` on rollover.
Or just log to the existing mirror log (which already has a structured format) and keep
`clobber-events.jsonl` for the alert/restore events only (the interesting ones).

## Acceptance-test tip
The goal's acceptance test says "simulate a revert of a pinned file -> sentinel detects within
one cycle, restores it, logs the event." Easiest way to simulate: after a successful mirror run,
manually `echo corrupted > index.html` (or any pinned file), then re-run `python memory_mirror.py -v`
and check that the output log shows the detection + restore. This is a 2-command test, no
infrastructure needed.

## Interaction with Goal 1 (Fleet Status API)
None direct. But if the sentinel emits alerts, those should be visible in `/api/fleet/status`
health field (amber = "revert detected this cycle"). Coordinate the data contract so both goals
share a single source of truth for "last revert event" rather than each maintaining its own.

## Verdict
Goal is well-scoped and achievable. Main risk is #1 (restore loop) — add the circuit breaker
before the acceptance test, not after. Everything else is implementation detail.
