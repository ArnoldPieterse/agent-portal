# Performance Gate Report

Run: 2026-11-26 17:00:55Z
Baseline: 2026-11-22 05:57:56Z
Threshold: +20% on p50

| endpoint | base p50 | curr p50 | delta | regressed |
|---|---|---|---|---|
| /api/status | 53.45 | 47.13 | -11.8% | no |
| /api/health/fleet | 368.56 | 127.18 | -65.5% | no |
| /api/goals | 127.95 | 46.92 | -63.3% | no |
| /api/agents | 6.37 | 14.31 | +124.6% | YES |
| /api/fleet | 64.95 | 140.8 | +116.8% | YES |
| /api/fleet/status | None | 15.23 | N/A | no |
| /api/models | 44.5 | 46.01 | +3.4% | no |
| /api/models/status | 15.42 | 15.08 | -2.2% | no |
| /api/perf | 15.51 | 30.08 | +93.9% | YES |
| /api/tools | 15.27 | 15.19 | -0.5% | no |
| /api/uploads | 166.28 | 139.98 | -15.8% | no |
| /api/history | 15.45 | 16.46 | +6.5% | no |
| /api/provenance | 15.52 | 13.22 | -14.8% | no |
| /api/memory-health | 123.98 | 125.24 | +1.0% | no |
| /api/manifest | 850.79 | 1225.98 | +44.1% | YES |
| /api/knowledge-bases | 31.25 | 30.79 | -1.5% | no |
| /api/run-state | 15.36 | 7.07 | -54.0% | no |
| /api/activity | 94.79 | 110.95 | +17.0% | no |
| /api/decisions | 46.47 | 49.88 | +7.3% | no |
| /api/net/dns | None | None | N/A | no |

## Regressions: 4

- **/api/agents**: 6.37 -> 14.31 ms (+124.6%)
- **/api/fleet**: 64.95 -> 140.8 ms (+116.8%)
- **/api/perf**: 15.51 -> 30.08 ms (+93.9%)
- **/api/manifest**: 850.79 -> 1225.98 ms (+44.1%)