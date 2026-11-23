# SLO enforcement report - 2026-11-24

SLO: p95 < 2000ms, p99 < 5000ms per endpoint (source: GET /api/perf, 60-min window).

/ | n=960 | p95=8.19ms | p99=11.79ms | OK
/api/goals | n=804 | p95=1747.37ms | p99=1779.06ms | OK
/api/status | n=12 | p95=30.6ms | p99=30.88ms | OK
/api/health/fleet | n=12 | p95=139.3ms | p99=163.03ms | OK
/api/agents | n=12 | p95=0.34ms | p99=0.34ms | OK
/api/fleet | n=12 | p95=2068.82ms | p99=2075.64ms | BREACH
/api/fleet/status | n=12 | p95=0.1ms | p99=0.11ms | OK
/api/models | n=12 | p95=29.04ms | p99=29.88ms | OK
/api/models/status | n=12 | p95=15007.99ms | p99=15011.53ms | BREACH
/api/perf | n=12 | p95=1.42ms | p99=1.84ms | OK
/api/tools | n=12 | p95=0.07ms | p99=0.07ms | OK
/api/uploads | n=12 | p95=158.87ms | p99=170.69ms | OK
/api/history | n=12 | p95=22.92ms | p99=42.14ms | OK
/api/provenance | n=12 | p95=0.68ms | p99=0.75ms | OK
/api/memory-health | n=12 | p95=114.56ms | p99=116.39ms | OK
/api/manifest | n=12 | p95=1080.67ms | p99=1148.3ms | OK
/api/knowledge-bases | n=12 | p95=19.54ms | p99=19.56ms | OK
/api/run-state | n=12 | p95=2.45ms | p99=4.5ms | OK
/api/activity | n=12 | p95=1858.27ms | p99=3573.24ms | OK
/api/decisions | n=12 | p95=28.65ms | p99=28.76ms | OK
/api/net/dns | n=12 | p95=0.06ms | p99=0.06ms | OK
/api/fleet/cockpit | n=2 | p95=104.82ms | p99=105.45ms | OK
/api/git | n=1 | p95=633.23ms | p99=633.23ms | OK

**Verdict: BREACH -> HOTLINE note required**
