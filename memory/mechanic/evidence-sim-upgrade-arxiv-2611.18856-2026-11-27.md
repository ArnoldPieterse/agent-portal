# EVIDENCE — SIM upgrade from arxiv 2611.18856v1 (Mechanic, 2026-11-27)

## What was done
Researched arxiv 2611.18856v1 "Self-Improvement Memory Enables Continual Recursive Self-Improvement" (Yu et al., Google Cloud AI).
Applied paper's §3.2 structure to existing memory/mechanic/sim.md:

1. Added `transfer` field to every attempt (cross-host/model applicability — paper's CRSI transfer conditions)
2. Added `cycle N` to provenance for each attempt (paper's p_ij includes round)
3. Added explicit REGRESSED attempt (a3 under model-seat-unreachable) — paper: "including its measured outcomes even when the edit regresses"
4. Added META section with auto-maintained problem counts + priority ordering
5. Added Consult Protocol section (RETAIN/REVISE/REPLACE/REMOVE decision tree from paper §3.2)
6. Upgraded sim_update.py: new --transfer, --cycle flags; --report mode auto-regenerates META

## Verification
- `python memory/mechanic/sim_update.py --report` → EXIT 0, found 6 problems / 12 attempts
- sim.md structure matches paper's m_i = (c_i, [(a_ij, o_ij, p_ij)]_j)
- All 6 problem sections have at least one attempt with transfer + cycle fields

## Files modified
- memory/mechanic/sim.md (upgraded structure + protocol)
- memory/mechanic/sim_update.py (new flags + report mode)
