# Cycle-2 cross-agent dependency map (Orchestrator goal #4, set 2026-11-16)

Updated every round; surfaced in the Goals panel once /api exposes it. Audit 2026-11-16: all edges below verified present in memory/goals/*.md text (grep-confirmed at write time).

## Chains (A blocks/feeds B)
1. **SLO pipeline** — Mechanic#4 (load baseline, daily jsonl) -> Builder#8 (/api/perf + tiles) -> Verifier#4 (daily breach reports). All three goal lines cross-reference the chain.
2. **Fleet-state endpoint** — Mechanic#8 (GET /api/health/fleet) -> Builder#6 (parity guard consumes fleet data) + Designer#9 (topology view renders it).
3. **Supersession validator** — Archivist#5 (script `archivist/supersession_check.py`) -> Scribe#5 (policy + weekly runs + report).
4. **Memory-health** — Archivist#2 (memory_health.py + /api/memory/health) -> Scribe#9 (dashboard tiles) ; Scribe#4 schedules the sweeps.
5. **Evolution layer** — Builder#4 (fitness = test suites) | Mechanic#5 (CHG entities on outage) | Verifier#7 (illegal-transition validator). Three independent interfaces, no mutual blocking.
6. **Model governance** — Orchestrator#2 (pre-run check + /api/models/status) -> every future group run (prompt carries [MODEL LOAD STATUS]) ; Researcher#3 (benchmark) informs the per-agent model assignment recommendation.
7. **Clobber defense** — Builder#6 (sandbox<->root parity, per-turn) | Researcher#6 (daily parity audit + disk==served) | Scribe#6 (durable-copy guarantee). Three layers, same failure mode.
8. **Evidence quality** — Verifier#5 (self-cert audit v2) + Verifier#10 (scorecard) -> Orchestrator#7 (weekly spot-check standard) -> Researcher#10 (trend report).

## Single-owner items (no cross-deps, by charter)
- Designer#1-4,6-8 (design system), #5/#10 (breakpoint + QA gates) — self-contained; #9 depends on Mechanic#8.
- Archivist#1,3,4,6,7,8,9,10 — self-contained; #2 feeds chain 4.
- Mechanic#1,2,3,5,6,7,9,10 — self-contained; #1 consumes Researcher#4 leading indicators (soft dep).
- Scribe#1,2,3,7,8,10 — self-contained.
- Orchestrator#1,3,5,6,8,9,10 — self-contained; #4 is this file.
- Researcher#1,2,4,5,7,8,9 — self-contained.

## Watch items (cycle-2 mid-point review)
- Chain 1 has the longest critical path (daily baseline must exist before tiles + enforcement are meaningful). First usable state: Mechanic#4 day-1 data.
- Chain 6 is a hard gate for fleet-wide rounds while White's two seats stay unloaded (see risk register R1).
