# SLO enforcement report - 2026-11-25

SLO: p95 < 2000ms, p99 < 5000ms per endpoint (source: GET /api/perf, 60-min window).

/api/user-messages | n=2406 | p95=1.1ms | p99=1.91ms | OK
/api/scheduler | n=1800 | p95=1.46ms | p99=6.44ms | OK
/api/fleet | n=1032 | p95=2047.29ms | p99=2066.43ms | BREACH
/api/run-state | n=960 | p95=6.24ms | p99=9.0ms | OK
/ | n=960 | p95=7.85ms | p99=11.63ms | OK
/api/goals | n=924 | p95=1643.55ms | p99=1668.41ms | OK
/api/status | n=252 | p95=60.89ms | p99=76.19ms | OK
/api/agents | n=132 | p95=0.84ms | p99=0.99ms | OK
/api/models | n=132 | p95=3851.74ms | p99=8441.85ms | BREACH
/api/knowledge-bases | n=132 | p95=28.68ms | p99=88.84ms | OK
/api/tools | n=132 | p95=0.11ms | p99=0.14ms | OK
/api/fleet/cockpit | n=122 | p95=198.93ms | p99=212.75ms | OK
/api/memory | n=120 | p95=0.38ms | p99=0.96ms | OK
/api/file | n=102 | p95=8.65ms | p99=10.45ms | OK
/api/history | n=23 | p95=58.04ms | p99=65.93ms | OK
/api/health/fleet | n=12 | p95=108.73ms | p99=112.69ms | OK
/api/fleet/status | n=12 | p95=0.11ms | p99=0.11ms | OK
/api/models/status | n=12 | p95=15045.62ms | p99=15056.0ms | BREACH
/api/perf | n=12 | p95=5.74ms | p99=5.8ms | OK
/api/uploads | n=12 | p95=98.54ms | p99=102.94ms | OK
/api/provenance | n=12 | p95=0.82ms | p99=0.89ms | OK
/api/memory-health | n=12 | p95=72.38ms | p99=72.38ms | OK
/api/manifest | n=12 | p95=1288.17ms | p99=1292.1ms | OK
/api/activity | n=12 | p95=222.31ms | p99=271.84ms | OK
/api/decisions | n=12 | p95=40.22ms | p99=41.41ms | OK
/api/net/dns | n=12 | p95=0.09ms | p99=0.1ms | OK
/api/git | n=1 | p95=776.9ms | p99=776.9ms | OK

**Verdict: BREACH -> HOTLINE note required**
