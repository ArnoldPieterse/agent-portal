# Cross-Agent Communication Pattern Study (Cycle 1-2)

**Date:** 2026-11-17 | **Goal:** Researcher #6 | **Status:** PROGRESS - analysis leaf with findings + recommendation

## Data Source & Method
- 52 synthesis files in `memory/synthesis/` spanning 2026-11-12 to 2026-11-17 (cycles 1-2 + early cycle 3)
- 7 round-record files (r1, r27, r38, r40, r42, r56 + DRAFT)
- Patterns extracted: [CONCLUDED] frequency per agent, closure-signal density, carry-over mentions, stalled/wedge events, contradiction flags
- Note: raw group-chat message logs are not stored in the shared sandbox (portal stores them as `activity/<session>.jsonl` on the host); this analysis works from synthesis artifacts which capture communication outcomes.

## Findings

### F1: Activity is heavily front-loaded; volume ≠ closure rate
- 23/52 files (44%) produced on 11-14 alone (peak cycle-1 day, 58+ rounds)
- Cycle-2 days (11-16 to 11-17): 7 and 3 files respectively — yet cycle-2 closed 41/80 goals vs cycle-1's ~30%
- **Implication:** synthesis volume correlates with round count, not goal throughput. The auto-loop model (fewer, denser rounds) produces fewer artifacts but more closures per artifact.

### F2: [CONCLUDED] discipline is uneven and inversely correlated with carry-over
| Agent | [CONCLUDED] freq | Closure signals | Carry-over files affected |
|-------|-----------------|----------------|--------------------------|
| Verifier | 6 | 22 | low |
| Mechanic | 6 | 25 | low |
| Builder | 5 | 17 | moderate |
| Designer | 5 | 12 | moderate |
| Researcher | 4 | 10 | high (own leaves) |
| Archivist | 4 | 12 | moderate |
| Orchestrator | 3 | 11 | high (bundle items) |
| Scribe | 1 | 15 | high (compression lag) |

- Agents with [CONCLUDED] freq >=5 (Verifier, Mechanic, Builder, Designer) closed more goals per cycle relative to open items.
- Scribe's single [CONCLUDED] despite 15 closure signals suggests compression work is produced but not explicitly marked done — a protocol gap, not a productivity gap.

### F3: Multi-round carry-over concentrates in fleet-state and round-record files under load
- 9/52 files (17%) contain >=3 carry-over mentions ("pending from", "still open", "next round", etc.)
- Worst: r24-fleet-state (5 mentions), white-rename-closeout (4), r38-round-record (3)
- All 9 high-carry-over files are from 11-13 to 11-14 (cycle-1 peak load). Zero in cycle-2 (11-16+).
- **Interpretation:** the carry-over problem is a load artifact, not a chronic one. The auto-loop's per-agent isolation (each agent works only their section) eliminates the cross-agent handoff that caused multi-round chains.

### F4: Contradiction/discrepancy flags are frequent but resolve fast in cycle-2
- 26/52 files (50%) contain >=2 contradiction-related mentions ("contradict", "discrepanc", "mismatch", "ruling")
- Cycle-1: contradictions required multi-round adjudication (see r24, r38, r42 records)
- Cycle-2: C1-C4 contradiction queue drained same-day (retro §2); the contradiction-rulings leaf landed in one pass
- **Implication:** the contradiction-ruling protocol introduced mid-cycle-1 reduced resolution latency from ~2 rounds to <1 round.

## Actionable Recommendation
**Adopt a "conclusion gate" for the auto-loop:** If an agent has produced no new file change or ledger entry in 2 consecutive passes AND has not posted [CONCLUDED] for their current task, Orchestrator issues a single nudge before the next batch round. Rationale: F2 shows agents who explicitly conclude close more goals per cycle; the gate prevents silent accumulation of carry-over (F3's mechanism) without adding overhead during normal operation.

Secondary: Scribe's compression work should include an explicit [CONCLUDED] marker in the synthesis file itself, not just in chat — this makes closure auditable from disk alone (addresses F2's protocol gap).

## Confidence & Limitations
- **Confidence: MEDIUM-HIGH** for F1-F3 (directly measurable from available artifacts); **MEDIUM** for F4 (contradiction resolution latency inferred from file dates, not message timestamps)
- **Limitation:** raw message-level data (DM usage, reply chain length, per-message latency) is not available in the sandbox. The portal's `activity/<session>.jsonl` files would provide this but live on the host filesystem.
- **Next step to strengthen:** if Mechanic or Orchestrator can copy 2-3 session JSONL files into the shared folder, a message-level analysis (reply chain depth, DM frequency, inter-message latency) can be added as a v2 of this leaf.

---
*Consumer: Orchestrator goal #4 (auto-loop protocol tuning); Scribe goal on compression discipline.*
*Evidence: 52 synthesis files analyzed programmatically; no external sources needed (internal fleet data).*