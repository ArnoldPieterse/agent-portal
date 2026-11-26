# SLO enforcement report - 2026-11-27

SLO: p95 < 2000ms, p99 < 5000ms per endpoint (source: GET /api/perf, 60-min window).

/api/user-messages | n=2404 | p95=3.19ms | p99=6.32ms | OK
/api/scheduler | n=1800 | p95=2.67ms | p99=6.93ms | OK
/api/voxel/pulse | n=1799 | p95=0.35ms | p99=1.7ms | OK
/api/goals | n=1469 | p95=3638.61ms | p99=4338.3ms | BREACH
/api/fleet | n=1034 | p95=2717.75ms | p99=2732.25ms | BREACH
/api/run-state | n=941 | p95=7.16ms | p99=11.79ms | OK
/api/agents | n=852 | p95=2.54ms | p99=6.57ms | OK
/ | n=798 | p95=8.55ms | p99=12.49ms | OK
/api/status | n=252 | p95=82.75ms | p99=121.64ms | OK
/api/models | n=133 | p95=6473.4ms | p99=12258.04ms | BREACH
/api/knowledge-bases | n=133 | p95=28.98ms | p99=31.01ms | OK
/api/tools | n=133 | p95=0.27ms | p99=0.94ms | OK
/api/fleet/cockpit | n=123 | p95=3113.38ms | p99=4624.53ms | BREACH
/api/memory | n=121 | p95=2.21ms | p99=3.87ms | OK
/api/file | n=53 | p95=14.4ms | p99=18.95ms | OK
/api/history | n=19 | p95=11.25ms | p99=11.91ms | OK
/api/health/fleet | n=12 | p95=122.14ms | p99=122.42ms | OK
/api/fleet/status | n=12 | p95=9.31ms | p99=18.34ms | OK
/api/models/status | n=12 | p95=15023.14ms | p99=15026.27ms | BREACH
/api/perf | n=12 | p95=8.16ms | p99=8.21ms | OK
/api/uploads | n=12 | p95=133.02ms | p99=133.78ms | OK
/api/provenance | n=12 | p95=1.76ms | p99=2.8ms | OK
/api/memory-health | n=12 | p95=133.31ms | p99=147.78ms | OK
/api/manifest | n=12 | p95=1266.95ms | p99=1267.45ms | OK
/api/activity | n=12 | p95=2568.62ms | p99=4967.81ms | BREACH
/api/decisions | n=12 | p95=48.41ms | p99=52.0ms | OK
/api/net/dns | n=12 | p95=0.08ms | p99=0.08ms | OK
/api/git | n=1 | p95=953.71ms | p99=953.71ms | OK

**Verdict: BREACH -> HOTLINE note required**
