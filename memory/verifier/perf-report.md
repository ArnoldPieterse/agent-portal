# Performance Gate Report

Run: 2026-11-23 17:01:02Z
Baseline: 2026-11-22 05:57:56Z
Threshold: +20% on p50

| endpoint | base p50 | curr p50 | delta | regressed |
|---|---|---|---|---|
| /api/status | 53.45 | 45.85 | -14.2% | no |
| /api/health/fleet | 368.56 | 125.14 | -66.0% | no |
| /api/goals | 127.95 | 30.9 | -75.8% | no |
| /api/agents | 6.37 | 15.42 | +142.1% | YES |
| /api/fleet | 64.95 | 291.51 | +348.8% | YES |
| /api/fleet/status | None | None | N/A | no |
| /api/models | 44.5 | 44.97 | +1.1% | no |
| /api/models/status | 15.42 | 15.54 | +0.8% | no |
| /api/perf | 15.51 | 15.45 | -0.4% | no |
| /api/tools | 15.27 | 15.4 | +0.9% | no |
| /api/uploads | 166.28 | 155.67 | -6.4% | no |
| /api/history | 15.45 | 15.24 | -1.4% | no |
| /api/provenance | 15.52 | 15.45 | -0.5% | no |
| /api/memory-health | 123.98 | 123.92 | -0.0% | no |
| /api/manifest | 850.79 | 999.26 | +17.5% | no |
| /api/knowledge-bases | 31.25 | 30.78 | -1.5% | no |
| /api/run-state | 15.36 | 15.48 | +0.8% | no |
| /api/activity | 94.79 | 109.64 | +15.7% | no |
| /api/decisions | 46.47 | 45.86 | -1.3% | no |
| /api/net/dns | None | None | N/A | no |

## Regressions: 2

- **/api/agents**: 6.37 -> 15.42 ms (+142.1%)
- **/api/fleet**: 64.95 -> 291.51 ms (+348.8%)