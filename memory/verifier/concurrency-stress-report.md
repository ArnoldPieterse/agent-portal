# Concurrency Stress Test Report
Generated: 2026-11-18 20:53:18
Target: p95 < 500ms, 0 errors
Total requests: 100 (50 per endpoint)
Wall time: 0.090s
Memory (process): 27822.8 MB -> 27835.8 MB (delta: +12.9 MB)

## http://localhost:8099/api/goals
- Requests: 50
- Errors: 50 (100.0%)
- Latency ms: avg=-1.0, p50=-1.0, p95=-1.0, max=-1.0
- Sample error: <urlopen error [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions>
- **FAIL** (p95=<500ms, errors=50)

## http://localhost:8099/api/fleet/overview
- Requests: 50
- Errors: 50 (100.0%)
- Latency ms: avg=-1.0, p50=-1.0, p95=-1.0, max=-1.0
- Sample error: <urlopen error [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions>
- **FAIL** (p95=<500ms, errors=50)

## Overall: FAIL
