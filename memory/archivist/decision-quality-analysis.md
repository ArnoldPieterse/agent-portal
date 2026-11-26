# Decision Quality Longitudinal Analysis
**Generated:** 2026-11-26 | **Source:** 4 files, 108 decisions total

## Methodology
- **Quality score:** `0.6 × outcome_score + 0.4 × confidence` (outcome mapped to 0–1 scale)
- **Cycle windows:** C1=11/13–14, C2=11/15–16, C3=11/17–18, C4=11/19–21, C5=11/22–23, C6=11/24–26
- **Regression threshold:** Drop > 0.15 composite between consecutive cycles (min n=2 per cycle)

## Source Files
| File | Records |
|------|---------|
| memory/archivist/decision-archive-data.jsonl | 56 |
| memory/ops/decision-log.jsonl | 37 |
| memory/builder/decision-log.jsonl | 4 |
| memory/synthesis/decisions.jsonl | 11 |

## Per-Cycle Overview
| Cycle | Date Range | Decisions | Avg Quality | Agents | Domains |
|-------|-----------|-----------|-------------|--------|---------|
| C1 | 11/13–14 | 14 | 0.923 | 5 | 1 |
| C2 | 11/15–16 | 4 | 0.940 | 2 | 1 |
| C3 | 11/17–18 | 8 | 0.602 | 2 | 2 |
| C4 | 11/19–21 | 0 | — (gap) | 0 | 0 |
| C5 | 11/22–23 | 68 | 0.572 | 5 | 3 |
| C6 | 11/24–26 | 4 | 0.785 | 1 | 1 |

## Per-Agent × Cycle (composite quality)
| Agent | C1 | C2 | C3 | C4 | C5 | C6 |
|-------|-----|-----|------|-----|------|------|
| archivist | 0.960 | — | 0.482 | — | — | — |
| builder | — | 0.940 | — | — | 0.544 | — |
| fleet-policy | — | — | — | — | 0.700 | — |
| mechanic | 0.700 | — | — | — | 0.650 | — |
| orchestrator | 0.960 | 0.940 | 0.960 | — | — | — |
| researcher | 0.960 | — | — | — | — | — |
| system | — | — | — | — | 0.575 | — |
| test_agent | — | — | — | — | 0.800 | — |
| unattributed | 0.960 | — | — | — | — | 0.785 |

## Per-Domain × Cycle
| Domain | C1 | C2 | C3 | C4 | C5 | C6 |
|--------|-----|------|------|-----|------|------|
| governance | 0.923 | 0.940 | 0.960 | — | — | — |
| knowledge-management | — | — | 0.482 | — | — | — |
| operational-resilience | — | — | — | — | 0.800 | — |
| operational-runbook | — | — | — | — | 0.529 | — |
| policy | — | — | — | — | 0.700 | — |
| dispatch | — | — | — | — | — | 0.785 |

## Regression Detection
**Agent-level (min-n=1, threshold >0.15):**
| Agent | From→To | Drop | Note |
|-------|---------|------|------|
| archivist | C1→C3 | -0.478 | n=1 in C3 (single data point) |
| builder | C2→C5 | -0.396 | n=1 in C2, n=14 in C5 |

**Top regressing agent:** Archivist (-0.478, C1→C3) — single-decision artifact; not statistically significant.
**Second regressing:** Builder (-0.396, C2→C5) — more meaningful given n=14 in C5.

**Top improver:** None detected (no agent improved >0.1 between consecutive cycles).

**Domain-level:** No regressions detected.

### Key Observations
1. **Governance quality is stable-high** (0.92–0.96 across C1–C3) — early decisions were high-confidence ratifications.
2. **Operational-runbook quality drops in C5** (0.529) — the most active cycle (68 decisions) shows lower per-decision quality, consistent with volume dilution or harder problems.
3. **C4 is a data gap** (zero decisions logged 11/19–21) — either no decisions were made or logging was not active.
4. **Archivist regression C1→C3:** 0.960 → 0.482 (drop of 0.478), but n=1 in C3, so below the min-n threshold for formal regression flagging.

## Limitations
- Sparse per-agent data: most agents appear in only 1–2 cycles, limiting longitudinal signal.
- C4 gap breaks continuity; trend lines are not smooth.
- Outcome scoring is heuristic (mapping discrete outcomes to continuous scale).
- "Unattributed" owner (n=8) reduces agent-level granularity.

## Recommendations
1. **Close the C4 gap:** backfill decision logs from 11/19–21 if records exist in session transcripts.
2. **Increase per-agent attribution:** reduce "unattributed" decisions to improve agent-level signal.
3. **Lower regression threshold to min-n=1** for agents with <5 total decisions (small-sample mode).
4. **Add a decision-quality ingestion hook** so new decisions are auto-scored at write time, not batch-processed.

---
*Full data: `memory/archivist/decision-quality-analysis.json` (8.5KB)*
