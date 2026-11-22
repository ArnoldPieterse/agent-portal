# Performance Gate Report

Run: 2026-11-22 21:00:47Z
Baseline: 2026-11-22 05:57:56Z
Threshold: +20% on p50

| endpoint | base p50 | curr p50 | delta | regressed |
|---|---|---|---|---|
| /api/status | 53.45 | 53.64 | +0.4% | no |
| /api/health/fleet | 368.56 | 156.07 | -57.7% | no |
| /api/goals | 127.95 | 46.58 | -63.6% | no |
| /api/agents | 6.37 | 14.14 | +122.0% | YES |
| /api/fleet | 64.95 | 264.42 | +307.1% | YES |
| /api/fleet/status | None | None | N/A | no |
| /api/models | 44.5 | 51.25 | +15.2% | no |
| /api/models/status | 15.42 | 14.73 | -4.5% | no |
| /api/perf | 15.51 | 15.93 | +2.7% | no |
| /api/tools | 15.27 | 14.4 | -5.7% | no |
| /api/uploads | 166.28 | 172.97 | +4.0% | no |
| /api/history | 15.45 | 12.96 | -16.1% | no |
| /api/provenance | 15.52 | 14.33 | -7.7% | no |
| /api/memory-health | 123.98 | 122.85 | -0.9% | no |
| /api/manifest | 850.79 | 922.88 | +8.5% | no |
| /api/knowledge-bases | 31.25 | 32.59 | +4.3% | no |
| /api/run-state | 15.36 | 15.39 | +0.2% | no |
| /api/activity | 94.79 | 111.03 | +17.1% | no |
| /api/decisions | 46.47 | 46.21 | -0.6% | no |
| /api/net/dns | None | None | N/A | no |

## Regressions: 2

- **/api/agents**: 6.37 -> 14.14 ms (+122.0%)
- **/api/fleet**: 64.95 -> 264.42 ms (+307.1%)