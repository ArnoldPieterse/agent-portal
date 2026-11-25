# SLO enforcement report - 2026-11-26

SLO: p95 < 2000ms, p99 < 5000ms per endpoint (source: GET /api/perf, 60-min window).

/api/user-messages | n=2407 | p95=1.42ms | p99=2.66ms | OK
/api/scheduler | n=1800 | p95=1.67ms | p99=7.85ms | OK
/api/fleet | n=1032 | p95=2075.29ms | p99=2091.13ms | BREACH
/api/run-state | n=968 | p95=1.34ms | p99=3.5ms | OK
/ | n=960 | p95=9.12ms | p99=12.16ms | OK
/api/goals | n=924 | p95=2291.02ms | p99=2371.78ms | BREACH
/api/status | n=252 | p95=56.27ms | p99=69.75ms | OK
/api/agents | n=132 | p95=1.48ms | p99=1.86ms | OK
/api/models | n=132 | p95=4345.82ms | p99=7480.36ms | BREACH
/api/knowledge-bases | n=132 | p95=29.55ms | p99=31.64ms | OK
/api/tools | n=132 | p95=0.12ms | p99=0.19ms | OK
/api/fleet/cockpit | n=123 | p95=661.92ms | p99=749.6ms | OK
/api/memory | n=120 | p95=0.38ms | p99=0.4ms | OK
/api/file | n=107 | p95=3.9ms | p99=9.62ms | OK
/api/history | n=26 | p95=3.57ms | p99=3.73ms | OK
/api/health/fleet | n=12 | p95=123.99ms | p99=129.07ms | OK
/api/fleet/status | n=12 | p95=13.96ms | p99=27.52ms | OK
/api/models/status | n=12 | p95=11.38ms | p99=22.36ms | OK
/api/perf | n=12 | p95=6.48ms | p99=6.51ms | OK
/api/uploads | n=12 | p95=171.96ms | p99=183.11ms | OK
/api/provenance | n=12 | p95=0.87ms | p99=0.87ms | OK
/api/memory-health | n=12 | p95=133.79ms | p99=134.43ms | OK
/api/manifest | n=12 | p95=1418.4ms | p99=1428.19ms | OK
/api/activity | n=12 | p95=2497.88ms | p99=4808.41ms | BREACH
/api/decisions | n=12 | p95=39.9ms | p99=40.23ms | OK
/api/net/dns | n=12 | p95=0.13ms | p99=0.14ms | OK
/api/git | n=1 | p95=986.33ms | p99=986.33ms | OK

**Verdict: BREACH -> HOTLINE note required**
