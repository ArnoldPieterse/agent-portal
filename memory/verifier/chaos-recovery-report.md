# Chaos-Recovery Drill Report

Run: 2026-11-26T18:54:27.822007Z
SLA target: recovery < 120s (goal #2 AC).

## Real production incidents (memory/ops/recovery-times.jsonl)
These are the fleet's ACTUAL heal times, measured by Mechanic.
| type | host | ts | recovery_s | <120s SLA |
|------|------|----|-----------|-----------|
| single_seat | white | 2026-11-18T09:15:00 | 840.0 | FAIL |
| single_seat | pale | 2026-11-19T14:30:00 | 1320.0 | FAIL |
| oom | white | 2026-11-19T16:00:00 | 2100.0 | FAIL |
| single_seat | black | 2026-11-20T11:20:00 | 1650.0 | FAIL |
| cascade | white+pale | 2026-11-21T10:00:00 | 5700.0 | FAIL |
| oom | red | 2026-11-22T13:45:00 | 2880.0 | FAIL |
| single_seat | white | 2026-11-23T08:10:00 | 1140.0 | FAIL |

## Autonomy finding (Fleet Autonomy Convergence)
- 0/7 real production incidents meet the <120s auto-recovery SLA.
- Real heal-time range: 840s..5700s (min=840s, max=5700s).
- Failure mode when SLA exceeded: detection + unload/reload round-trip dominates (minutes, not seconds). To converge toward <120s the fleet must cut the reload latency or pre-stage models so recovery is a re-point, not a re-load.
- This seat could NOT run a live drill (localhost Studio firewalled: WinError 10013; no NVML). The live leg above fails closed by design and must be run from a seat that reaches a Studio (e.g. White local host).
