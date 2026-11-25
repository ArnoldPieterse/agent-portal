# Performance Gate Report

Run: 2026-11-25 17:00:39Z
Baseline: 2026-11-22 05:57:56Z
Threshold: +20% on p50

| endpoint | base p50 | curr p50 | delta | regressed |
|---|---|---|---|---|
| /api/status | 53.45 | 61.68 | +15.4% | no |
| /api/health/fleet | 368.56 | 138.4 | -62.4% | no |
| /api/goals | 127.95 | 45.86 | -64.2% | no |
| /api/agents | 6.37 | 15.16 | +138.0% | YES |
| /api/fleet | 64.95 | 165.93 | +155.5% | YES |
| /api/fleet/status | None | 15.5 | N/A | no |
| /api/models | 44.5 | 46.48 | +4.4% | no |
| /api/models/status | 15.42 | 15.28 | -0.9% | no |
| /api/perf | 15.51 | 30.45 | +96.3% | YES |
| /api/tools | 15.27 | 15.04 | -1.5% | no |
| /api/uploads | 166.28 | 167.66 | +0.8% | no |
| /api/history | 15.45 | 15.44 | -0.1% | no |
| /api/provenance | 15.52 | 15.12 | -2.6% | no |
| /api/memory-health | 123.98 | 154.25 | +24.4% | YES |
| /api/manifest | 850.79 | 1335.55 | +57.0% | YES |
| /api/knowledge-bases | 31.25 | 31.05 | -0.6% | no |
| /api/run-state | 15.36 | 14.8 | -3.6% | no |
| /api/activity | 94.79 | 155.1 | +63.6% | YES |
| /api/decisions | 46.47 | 61.62 | +32.6% | YES |
| /api/net/dns | None | None | N/A | no |

## Regressions: 7

- **/api/agents**: 6.37 -> 15.16 ms (+138.0%)
- **/api/fleet**: 64.95 -> 165.93 ms (+155.5%)
- **/api/perf**: 15.51 -> 30.45 ms (+96.3%)
- **/api/memory-health**: 123.98 -> 154.25 ms (+24.4%)
- **/api/manifest**: 850.79 -> 1335.55 ms (+57.0%)
- **/api/activity**: 94.79 -> 155.1 ms (+63.6%)
- **/api/decisions**: 46.47 -> 61.62 ms (+32.6%)