# Fleet throughput fix - why the fleet was slower than one LLM (2026-11-23 ~07:1x)

Arnold: "we have single handily reached more goals with your single LLM in under a few minutes
compared to the fleet... our fleet logic is faulty and needs improvements." Diagnosis from journal
g-1a204f69381 + down-seats.json + pass prompts, then three fixes in agent_portal.py:

## Root causes (evidence)
1. **Phantom seats fired into every pass.** 4/8 models not loaded anywhere reachable
   (down-seats.json: Researcher/Archivist/Scribe/Mechanic unreachable). The autoloop ready-gate
   counted a probe TIMEOUT (no status) as ready, so dead seats were fired; their turns hung
   tokenless (Archivist: 2 frames in 20m52s) and stretched every pass until a human hit Stop.
2. **No per-pass time cap.** _parallel_turns waited on ALL agents at context exit; one hung seat
   held the whole run open indefinitely (only the global no-frames watchdog eventually fired).
3. **One-step-per-pass tasking + 60 s idle gap.** Each pass asked for "ONE concrete next step";
   a goal needing N steps took N passes x (pass time + 60 s). A single LLM works to completion in
   one turn - that is the whole speed gap. Plus ~1 min/pass of re-derivation re-reading goal files.
4. Structural: all seats share one local model server, so "parallel" passes serialize on one GPU;
   ~20K thinking tokens/pass = 4-21 min wall. Fixes 1-3 raise goals-per-pass and cut hung-seat
   waste; that is the lever.

## Fixes (agent_portal.py, deployed via PortalRun restart ~07:06)
- **Ready gate**: only seats whose model probe returns CONFIRMED `ok` run from home. Unknown/
  timed-out probe => down chain (hot-load/reboot/placement) instead of a blind fire.
- **PASS_TIMEOUT_S = 900**: as_completed cap on the parallel pass; on timeout stop_event tears
  remaining turns down cleanly and unfinished agents get a "turn stalled" result so the round ends.
- **Work-to-completion passes**: open-goal task now says work the oldest goal TO COMPLETION,
  mark it reached with timestamped evidence, then take the next-oldest if budget remains;
  terse-reasoning rule; [CONCLUDED] on reach or hard blocker. New _agent_open_goals() injects
  the agent's numbered open-goal list straight into the prompt (skips re-derivation).

## Verified live (run g-1a205166af8 after restart)
- Cast = 6 agents: Researcher + Archivist (phantom seats) correctly EXCLUDED from the batch.
- Prompt contains "TO COMPLETION" x3 + 3 injected goal lists.
- /api/goals: fleet 27/78, level counter at Lv 1 (legit cycle-9 close-out).

## Known hazard (NOT on the fleet path - flagged, not changed)
Workspace-root `goal_ledger.py` has a loose EVIDENCE_PAT that matches the words "verified" /
"acceptance" inside acceptance-criteria text: every well-specified numbered goal parses as
reached (78/80 phantom-100%). The portal uses the STRICT memory/researcher/goal_ledger.py
(dated-evidence-gated) - true state 25/78 at time of writing. Any tool importing the ROOT
goal_ledger will see phantom completion; tighten it before reuse.
