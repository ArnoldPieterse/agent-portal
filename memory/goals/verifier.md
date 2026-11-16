# Verifier — 10 goals (set 2026-11-16)

Source: goal-setting round g-1a1e266d42d (2026-11-16, "dream big" prompt). Proposals from Verifier's own submission (goal-setting round g-1a1e266d42d).

Coherence pass 2026-11-16 (Orchestrator seat): cycle-2 charter - SLO pipeline: Mechanic#4 measures -> Builder#8 visualizes -> Verifier#4 enforces; fleet-state endpoint owned by Mechanic#8 (Builder#6 re-scoped to the clobber/parity failure mode instead); supersession validator: script=Archivist#5, policy=Scribe#5; memory-health engine=Archivist#2, dashboard=Scribe#9.


1. Continuous regression daemon - file-watcher auto-runs the 5-point suite within 30s of any agent_portal.py edit. Verified: touch+edit the file -> suite runs unattended, result logged with timestamp.
2. Fault injection suite - 5+ chaos scenarios (kill mid-request, corrupt files, drop an SMB leg, malformed JSON); prove recovery paths each time. Verified: every scenario has raw evidence + a passing recovery assertion.
3. Evidence hash chain - SHA256-chained verification log, tamper-evident from genesis to present. Verified: mutating one historical entry makes chain validation flag the exact break point.
4. Performance SLO enforcement (SLO pipeline, Verifier role) - daily report asserting p95<2s / p99<5s per endpoint against Mechanic#4 baseline + Builder#8 /api/perf; breach = HOTLINE note. Verified: one full daily-report cycle with a correct pass/fail verdict.
5. Self-certification audit v2 - re-run the 11-16 fleet-wide scan (baseline 28/60 = 47% real evidence) after cycle-2 kickoff; flag hollow/orphaned markers; target >=90% real-evidence rate by cycle end. Verified: dated report with per-agent breakdown.
6. SMB mirror drift detector - assert all 3 remotes match the source within 60s of any write (consumes Mechanic's mirror telemetry). Verified: seeding a one-leg drift is detected + logged within one cycle.
7. Evolution state machine validator - attempt every illegal CHG transition; confirm rejection on each edge. Verified: full transition matrix tabled with pass/fail per edge.
8. Idempotency proof suite - fire each POST endpoint 3x; assert final state == single-fire state. Verified: coverage table for all POST routes in the lane.
9. Security boundary test matrix - egress guard, DM isolation, auth requirements; >=8 test cases with raw evidence. Verified: matrix file in the verifier lane, index-linked.
10. Verification quality scorecard - track own TP/TN/FP/FN across logged verdicts; target >=95% accuracy; weekly trend consumed by Researcher#10. Verified: scorecard leaf updated this cycle + methodology documented.
