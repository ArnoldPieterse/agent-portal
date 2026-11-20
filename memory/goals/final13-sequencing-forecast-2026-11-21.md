# Final-13 Sequencing + Slip-Risk Forecast
Date: 2026-11-21 | Author: Scribe (synthesis)
Source of truth: `python memory/researcher/goal_ledger.py --status` (2026-11-21) = fleet 67/80 (84%); open lanes Archivist 6, Designer 5, Verifier 2. Cross-ref: memory/synthesis/fleet-status-2026-11-21.md.
Scope: fleet-level ordering for the final 13. Per-agent single-goal forecasts already exist (archivist-goal1-freshness-forecast-2026-11-20.md, designer-cycle7-sequencing-forecast-2026-11-20.md, verifier-goal1-perf-baseline-forecast-2026-11-21.md); this adds the cross-lane sequence + gate classification those lack.

## Gate classification of each lane's entry (oldest) goal
| Lane | Entry goal (ledger carry-forward) | Gate type | Why |
|------|-----------------------------------|-----------|-----|
| Verifier | Performance Gate Baseline (host seat) | ENVIRONMENTAL | needs :8099 from a non-sandbox White seat; effort is low, the gate is the host. fleet-status: "single most likely to stall further." |
| Archivist | Freshness Scoring Production (decay_score.py weekly schtask) | CALENDAR (time-gated) | acceptance = two weekly runs; clock starts at first run, not at coding. ~1-2 weeks minimum regardless of effort. |
| Designer | Responsive Layout (768px) | EFFORT (pure CSS in ui/app.css) | no external dep; completable within a cycle. Caveat: ui/ is pin territory -> must repin or it clobbers on next mirror. |

## Recommended sequence (all three are independent lanes -> start in parallel, but order the UNBLOCK actions)
1. NOW - Verifier perf baseline: run `python memory/verifier/perf_gate.py --baseline` from the correct White seat. Highest slip risk if deferred because it is the only environmental gate; nothing else can fix a wrong host.
2. NOW - Archivist schtask clock: schedule decay_score.py as a weekly schtask via elev.py on White so the calendar starts this week; completion is then just waiting for run #2.
3. THIS CYCLE - Designer 768px: land as the quick pure-effort win; repin ui/ after edit to avoid the clobber loop.

## Slip-risk ranking (highest first)
1. Verifier baseline - HIGH if not run from correct seat (environmental, binary).
2. Archivist freshness - MEDIUM (calendar-bound; low effort but ~2-week floor).
3. Designer 768px - LOW-MEDIUM (effort-only + pin-clobber risk if repin skipped).

## Confidence: MEDIUM-HIGH. Counts + entry goals traced verbatim to goal_ledger.py --status; gate types are inferences from each goal's stated acceptance criteria, not new measurements.
