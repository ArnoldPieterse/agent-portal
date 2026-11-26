# Forge run log

| date | event | result | evidence |
|------|-------|--------|----------|
| 2026-11-25 | Red host powered on (human broadcast) | ACK - red reachable; unblocks Scribe+Mechanic home seats, restores 4-host probe coverage for smoke suite | user message um-20261125-125759 |
| 2026-11-25 13:08 | smoke_suite: smoke_suite: PROBE FAILED (elev.py or network error) |
| 2026-11-25 13:12:18 | smoke_suite: FAILURES (4 hosts, 4 issues) |
| 2026-11-25 14:16:00 | smoke_suite: FAILURES (4 hosts, 4 issues) |
| 2026-11-25 14:18:23 | canary_deploy: START canary=White file=_canary_test.txt sha=1c7de0d250b63b2c |
| 2026-11-25 14:18:25 | canary_deploy: SUCCESS: _canary_test.txt deployed to all 4 hosts (canary=White) |
| 2026-11-25 14:32:52 | smoke_suite: FAILURES (4 hosts, 4 issues) |
| 2026-11-25 14:36:15 | canary_deploy: START canary=White file=_perf_test_file.txt sha=2bb644d7127d0892 |
| 2026-11-25 14:36:17 | canary_deploy: SUCCESS: _perf_test_file.txt deployed to all 4 hosts (canary=White) |
| 2026-11-25 14:37:49 | gate_health: ALL GATES HEALTHY |
| 2026-11-25 14:45:56 | smoke_suite: REMEDIATING White - TCP: PermissionError: [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions |
| 2026-11-25 06:53 | gate_metrics (goal #7): SELFTEST PASS (4 metrics exact) + live merge into autonomy-score.json 'gate' key; clobber-loop check OK |

## 2026-11-26 ~23:59 - gate_circuit_breaker.py built + live-tested
Command: `python memory/forge/gate_circuit_breaker.py --window 5 --threshold 0.8`
Result: EXIT 1 (CIRCUIT_BREAKER) - correct: all 4 smoke runs show 100% TCP-fail (sandbox permission). Breaker trips, incident logged to memory/ops/incidents.jsonl, state written to gate-breaker-state.json. Prevents canary_deploy.py from auto-promoting on false CRIT signals.
| 2026-11-26 21:04:54 | canary_deploy: DISPATCH GATE BLOCKED file=next10.json -> 60.0% conformance (6/10 clean) |
| 2026-11-26 21:06:13 | canary_deploy: DISPATCH GATE BLOCKED file=next10.json -> 60.0% conformance (6/10 clean) |
| 2026-11-26 21:06:15 | canary_deploy: DISPATCH GATE BYPASSED (explicit --bypass-gate) file=next10.json |
| 2026-11-26 21:06:15 | canary_deploy: START canary=White file=next10.json sha=d5dc0a3158e5b5b2 |
| 2026-11-26 21:06:15 | canary_deploy: SUCCESS: next10.json deployed to all 4 hosts (canary=White) |
| 2026-11-26 21:07:24 | canary_deploy: DISPATCH GATE BLOCKED file=next10.json -> 60.0% conformance (6/10 clean) |
| 2026-11-26 21:07:42 | canary_deploy: DISPATCH GATE BLOCKED file=next10.json -> 60.0% conformance (6/10 clean) |
| 2026-11-26 21:07:51 | canary_deploy: DISPATCH GATE BYPASSED (explicit --bypass-gate) file=next10.json |
| 2026-11-26 21:07:51 | canary_deploy: START canary=White file=next10.json sha=d5dc0a3158e5b5b2 |
| 2026-11-26 21:07:51 | canary_deploy: SUCCESS: next10.json deployed to all 4 hosts (canary=White) |

| 2026-11-26 21:10 | dispatch_gate (goal #3): gate built + wired into canary Phase -1; selftest EXIT 0 (block/clean/skippable); BLOCK_RC=4 on stale next10, BYPASS_RC=0 explicit flag, live conformance 60% (4 true stale dispatches) | memory/forge/evidence-dispatch-gate-2026-11-26.md |
