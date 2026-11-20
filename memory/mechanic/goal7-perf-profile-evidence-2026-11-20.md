# Goal 7: Performance Profiling - Evidence (2026-11-20)

## Status: script built + selftest PASS; live 1h run needs non-sandbox :8099 egress

### Verified in sandbox:
- `python perf_profile.py --selftest` -> ALL ASSERTIONS PASS (p50=50.5, p95=95.05, p99=99.01 on 1..100; edge cases single/two-value correct)
- JSON output structure valid (generated_at, duration_s, samples_collected, metrics with p50/p95/p99 per endpoint)
- Script measures: portal_health, fleet_status, goals_api, llm_models endpoints at 5s intervals
- Percentile computation uses linear interpolation (correct for the acceptance criterion)

### Blocked (sandbox egress):
- `python perf_profile.py --duration 3600` cannot reach localhost:8099 (WinError 10013, same class as all other :8099 probes from sandbox)
- Live run requires non-sandbox White seat with portal reachable

### Unblock (one-time, non-sandbox White):
```
python memory/mechanic/perf_profile.py --duration 3600
```
Then verify `memory/mechanic/perf-profile.json` has p50/p95/p99 for all 4 metrics with status=ok.

### Artifact:
- Script: memory/mechanic/perf_profile.py (production-ready)
- Output target: memory/mechanic/perf-profile.json (written after live run completes)