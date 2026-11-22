# Performance Gate Report

Run: 2026-11-22 05:58:21Z
Baseline: 2026-11-22 05:57:56Z
Threshold: +20% on p50

| endpoint | base p50 | curr p50 | delta | regressed |
|---|---|---|---|---|
| /api/status | 53.45 | 44.86 | -16.1% | no |
| /api/health/fleet | 368.56 | 123.81 | -66.4% | no |
| /api/goals | 127.95 | 62.23 | -51.4% | no |
| /api/agents | 6.37 | 15.47 | +142.9% | YES |
| /api/fleet | 64.95 | 58.77 | -9.5% | no |
| /api/fleet/status | None | None | N/A | no |
| /api/models | 44.5 | 39.08 | -12.2% | no |
| /api/models/status | 15.42 | 15.5 | +0.5% | no |
| /api/perf | 15.51 | 15.28 | -1.5% | no |
| /api/tools | 15.27 | 15.51 | +1.6% | no |
| /api/uploads | 166.28 | 160.83 | -3.3% | no |
| /api/history | 15.45 | 14.93 | -3.4% | no |
| /api/provenance | 15.52 | 15.43 | -0.6% | no |
| /api/memory-health | 123.98 | 123.45 | -0.4% | no |
| /api/manifest | 850.79 | 846.54 | -0.5% | no |
| /api/knowledge-bases | 31.25 | 23.77 | -23.9% | no |
| /api/run-state | 15.36 | 15.54 | +1.2% | no |
| /api/activity | 94.79 | 93.15 | -1.7% | no |
| /api/decisions | 46.47 | 46.75 | +0.6% | no |
| /api/net/dns | None | None | N/A | no |

## Regressions: 1

- **/api/agents**: 6.37 -> 15.47 ms (+142.9%)