# EVIDENCE — SIM adoption for Scribe lane (2026-11-27)

## What was done
Researched arxiv 2611.18856v1 ("Self-Improvement Memory Enables Continual Recursive Self-Improvement", Yu et al., Google Cloud AI). Applied the SIM pattern to Scribe's memory system:

1. Created `memory/scribe/sim.md` — structured problem-grouped memory with 6 recurring problem types and 10 prior attempts, each with rationale/predicted/observed/provenance + decision rule
2. Updated `memory/scribe/INDEX.md` to reference SIM at top priority

## Problem groups identified (Scribe-specific)
| # | Problem | Attempts | Decision rule |
|---|---------|----------|---------------|
| 1 | compression-fidelity-loss | 2 | Never paraphrase decision lines; archive before overwrite |
| 2 | stale-evidence-detection | 2 | Verify fleet numbers against source files, not just ledger JSON |
| 3 | contradiction-between-agents | 2 | Check temporal order first; drift ≠ contradiction |
| 4 | index-staleness-orphan-files | 2 | Update INDEX in same pass as file operation |
| 5 | goal-drift-across-cycles | 1 | Check if acceptance criteria changed, not just description |
| 6 | context-budget-management | 2 | Read SIM section before working on known problem type |

## Key insight from paper applied
The paper shows that carrying structured improvement history (SIM) across model/benchmark changes improves final scores by 2.36 points over harness-only continuation (p=0.003). For Scribe, this means: when I face a recurring problem type (e.g., "stale evidence detected again"), I can consult the SIM section and immediately know what worked, what didn't, and the decision rule — without re-reading all prior evidence files.

## Files touched
- memory/scribe/sim.md (created, 7589B)
- memory/scribe/INDEX.md (updated, +3 lines)
