# Performance Gate Report

Run: 2026-11-24 17:00:47Z
Baseline: 2026-11-22 05:57:56Z
Threshold: +20% on p50

| endpoint | base p50 | curr p50 | delta | regressed |
|---|---|---|---|---|
| /api/status | 53.45 | 44.94 | -15.9% | no |
| /api/health/fleet | 368.56 | 123.24 | -66.6% | no |
| /api/goals | 127.95 | 30.82 | -75.9% | no |
| /api/agents | 6.37 | 15.26 | +139.6% | YES |
| /api/fleet | 64.95 | 154.85 | +138.4% | YES |
| /api/fleet/status | None | None | N/A | no |
| /api/models | 44.5 | 46.18 | +3.8% | no |
| /api/models/status | 15.42 | 15.09 | -2.1% | no |
| /api/perf | 15.51 | 28.86 | +86.1% | YES |
| /api/tools | 15.27 | 14.57 | -4.6% | no |
| /api/uploads | 166.28 | 108.72 | -34.6% | no |
| /api/history | 15.45 | 15.49 | +0.3% | no |
| /api/provenance | 15.52 | 15.05 | -3.0% | no |
| /api/memory-health | 123.98 | 92.73 | -25.2% | no |
| /api/manifest | 850.79 | 799.85 | -6.0% | no |
| /api/knowledge-bases | 31.25 | 5.54 | -82.3% | no |
| /api/run-state | 15.36 | 13.31 | -13.3% | no |
| /api/activity | 94.79 | 169.39 | +78.7% | YES |
| /api/decisions | 46.47 | 48.5 | +4.4% | no |
| /api/net/dns | None | None | N/A | no |

## Regressions: 4

- **/api/agents**: 6.37 -> 15.26 ms (+139.6%)
- **/api/fleet**: 64.95 -> 154.85 ms (+138.4%)
- **/api/perf**: 15.51 -> 28.86 ms (+86.1%)
- **/api/activity**: 94.79 -> 169.39 ms (+78.7%)