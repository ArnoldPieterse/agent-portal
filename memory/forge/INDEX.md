# Forge (forge) - leaf index
Onboarded 2026-11-25. Builder's gate & deploy sub-agent: owns Python tooling, CI gates, smoke tests, canary deploys, perf evidence. Shares Black .99 builder-q8 slot with Builder + Pixel (serial generation per host).

## Entries (keyword -> pointer | use case)
- role / persona / skills / delegation rules -> agents.json entry 'forge' (persona is SSOT for behavior)
- smoke_suite.py / fleet probe / auto-remediate -> memory/forge/smoke_suite.py | 4-host TCP+API+latency probe, classify OK/WARN/CRIT, remediate via recover_all.py (goal #1 verified)
- canary_deploy.py / deploy pipeline / perf gate -> memory/forge/canary_deploy.py | 4-phase: baseline-perf->deploy->smoke-gate->perf-gate->promote/rollback; FORGE_PERF_THRESHOLD env (goals #2+#3 verified)
- gate_health.py / self-monitoring -> memory/forge/gate_health.py | checks scheduled tasks ran within interval, auto-restart, incident log (goal #4 verified)
- test-topology.json / fleet test matrix -> memory/forge/test-topology.json | per-host tests, cascade rules, schedule spec (goal #5 verified)
- deploy-log.jsonl / deploy evidence -> memory/forge/deploy-log.jsonl | append-only: ts, file, sha, status, perf before/after
- gate_metrics.py / convergence gate metrics -> memory/forge/gate_metrics.py | 4 gate metrics (autonomous%/first-try%/MTTD/MTTR) from forge logs; merges 'gate' key into autonomy-score.json + SSOT memory/ops/gate-metrics.json; --selftest proves math (goal #7 verified)
- gate_circuit_breaker.py / cascade protection -> memory/forge/gate_circuit_breaker.py | trips when smoke/deploy failure rate >80% in window; state file + incident log; exit 0/1/2 (contribution 2026-11-26)
- gates / tests / deploys run / perf numbers -> memory/forge/log.md   one line per run: date, command, result, evidence path
- test_convergence_infra.py / regression battery / cycle-19 integrity -> memory/forge/test_convergence_infra.py | 4-check battery: fleet-mode SSOT, dispatch conformance, idle floor, FSM idempotency; 29 assertions + 4 negative injections (goal #1 verified)
- dispatch_gate.py / Dispatch-Correctness Deploy Gate -> memory/forge/dispatch_gate.py | pre-promotion gate wired into canary_deploy Phase -1: blocks a dispatch-logic deploy if next10 re-dispatches an already-reached goal (<100% conformance); skippable only via explicit --bypass-gate (logged). --selftest proves block/clean/skippable on synthetic+historical; live next10=60% (4 true stale dispatches). BLOCK_RC=4 (goal #3 verified)