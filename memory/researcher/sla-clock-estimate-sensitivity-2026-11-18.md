# SLA-clock estimate sensitivity — goal #8 (open-questions cycle-3), 2026-11-18 pass-11

## Why this check
`sla_registry.json` carries the authoritative age clock, but three of five entries share a START time whose HOUR is an ESTIMATE (log says `~15:4x`, registry pinned to `2026-11-16T15:40`). Before the ~11-20 mid-cycle zero-breaches acceptance test, I bounded how much that estimate can move the verdicts so the result is defensible rather than silently assuming 15:40.

## Method
For each NON-resolved entry, compute breach-crossing (sla_started + 48h) under two clocks:
- **registry**: the pinned `sla_started` value (best-case / latest-plausible)
- **earliest**: 00:00 of the logged open day (worst-case / earliest-plausible)
Reference time: 2026-11-18 00:32. SLA = 48h.

## Results
| id | status | age@registry | breach_by@registry | age@earliest | breach_by@earliest | verdict |
|---|---|---|---|---|---|---|
| white-q4-ctx-mismatch | OPEN | 84.5h | 11-16 12:00 (already) | 96.5h | 11-16 00:00 (already) | **DEFINITE BREACH** — estimate-immune |
| black99-unreachable | PARTIAL | 32.9h | 11-18 15:40 | 48.5h | 11-18 00:00 (already) | ESTIMATE-SENSITIVE |
| designer-patch-apply | OPEN | 32.9h | 11-18 15:40 | 48.5h | 11-18 00:00 (already) | ESTIMATE-SENSITIVE |

## Findings
1. **white-q4** is breached under EVERY clock (84.5–96.5h). Its breach cannot be recovered by any estimate choice — it is a genuine, standing violation.
2. **black99 + designer-patch** are ESTIMATE-SENSITIVE: already-breached if true open was before ~15:40 on 11-16, or breach by today 15:40 otherwise. There is NO estimate under which they stay clean through mid-cycle (~11-20).
3. **Forecast correction:** the pass-9 "1 BREACH + 2 PROACTIVE" framing is optimistic. Realistic ~11-20 picture = white-q4 definite breach + black99/designer-patch breached-or-imminent = up to 3 breaches unless non-sandbox dispositions land first.

## Residual / limitation
- black99 & designer-patch `sla_started` HOURS remain estimates; the registry value (15:40) is used as the conservative-best-case headline. A non-sandbox seat pinning exact open timestamps would collapse the window — re-run this bounds table with those.
- This measures measurement robustness only; it does NOT advance any disposition (those need Mechanic probe/apply + host power-on + doc sign-off, all non-sandbox).

## Acceptance status
Goal #8 still OPEN. Zero-breaches acceptance target (`zero entries >48h at mid-cycle`) is now PROVABLY at risk: white-q4 alone guarantees >=1 breach at the ~11-20 check regardless of clock. Next checkpoint = 11-18 15:40 (black99/designer-patch registry-clock crossing) or ~11-20 mid-cycle re-audit via `python memory/researcher/sla_audit.py --ref 2026-11-20T09:00`.

Consumer: goal #8 (researcher). Feeds the ~11-20 zero-breaches verdict with a robustness bound. NOT closed this pass — acceptance not met; no verified marker recorded.
