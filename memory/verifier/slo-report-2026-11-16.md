# SLO enforcement report - 2026-11-16

SLO: p95 < 2000ms, p99 < 5000ms per endpoint (source: GET /api/perf, 60-min window).

/api/user-messages | n=22 | p95=0.82ms | p99=0.88ms | OK
/api/run-state | n=7 | p95=0.51ms | p99=0.52ms | OK
/api/status | n=4 | p95=44.35ms | p99=46.0ms | OK
/api/health/fleet | n=1 | p95=101.06ms | p99=101.06ms | OK
/api/perf | n=1 | p95=0.29ms | p99=0.29ms | OK
/api/decisions | n=1 | p95=16.77ms | p99=16.77ms | OK
/api/agents | n=1 | p95=0.48ms | p99=0.48ms | OK
/api/models | n=1 | p95=465.06ms | p99=465.06ms | OK
/api/knowledge-bases | n=1 | p95=29.89ms | p99=29.89ms | OK
/api/tools | n=1 | p95=0.09ms | p99=0.09ms | OK
/api/memory | n=1 | p95=0.32ms | p99=0.32ms | OK

**Verdict: PASS**
