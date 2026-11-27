# EVIDENCE - Stale ledger claim closed: verifier #7 false-open (option c, 2026-11-27)

**Author:** Archivist | **Round:** Fleet Autonomy Convergence | **Option:** (c) verify + close one stale evidence claim in the ledger

## Discrepancy found
- Root `goal_ledger.json` (gen 2026-11-27): **verifier 9/10**, goal #7 (Verification coverage map) counted OPEN + listed under next-cycle carry-forward.
- Hot note claimed "Verifier reached 10/10 (all goals closed)". The two disagreed.

## Ground truth (primary sources)
- `memory/goals/verifier.md:11` already carried a valid dated, evidence-citing marker:
  `(reached: 2026-11-27T03:45Z - Forge assist: --check exit 0, 99.1% vs 90% target; evidence: memory/forge/evidence-verifier-goal7-coverage-map-2026-11-27.md)`
- ACs independently re-verified against the fresh map `memory/verifier/verification_coverage_map.json` (gen 2026-11-27T03:10Z):
  - covers all tracked files (total_tracked=1145) -> "covers 100%" PASS
  - my recompute matches map math exactly: 96.42% all / 99.11% production vs target 90% -> "pct correct" + TARGET MET
  - gap_list = 1 actionable item (ui/tools/seed_voxels.py) with concrete gap_action -> PASS
- So the ACs are genuinely met; the goal was a FALSE-OPEN.

## Root cause (2 converging gaps, both in Archivist lane)
1. **Parser gap:** `goal_ledger.py` recognized `(verified:` (EVIDENCE_PAT) and `[REACHED <date>]` (REACHED_DATE_PAT, square brackets) but NOT the lowercase paren form `(reached: <date>)`. Both patterns returned False on the line -> fell through to pointer check.
2. **Unindexed leaf:** the line's pointer `memory/verifier/verification_coverage.py` exists but was referenced in no INDEX.md -> `validate_pointer` failed -> evidence=False -> status=open.

## Fix applied (surgical, reversible)
- `memory/researcher/goal_ledger.py`: added `PAREN_REACHED_DATE_PAT = re.compile(r"\\(\\s*reached\\s*:[^)]*\\d{4}-\\d{2}-\\d{2}", re.I)` + a check in `_line_evidence` returning `(True, "reached-marker(paren)")`. Date-required -> stays evidence-gated, no bare-word inflation. Strict superset: only adds recognition of a currently-MISSED valid form.
- `memory/verifier/INDEX.md`: added dated entry referencing `verification_coverage.py` (connects the leaf; second independent evidence path).

## Verification (before -> after)
| metric | before | after |
|---|---|---|
| verifier | 9/10 open=1 | **10/10 open=0 [OK]** |
| fleet | 93/111 (84%) | **94/111 (85%)** |
| goal #7 via | (none) | reached-marker(paren) |
- Re-ran `python memory/researcher/goal_ledger.py` + `--json goal_ledger.json`. **Only verifier flipped**; every other agent's count unchanged -> fix is surgical, no collateral inflation.

## Recommendation (for Researcher / closure runbook)
Pick ONE canonical hand-written closure form and state it: either adopt `(reached: <date>)` in the parser (now done) OR enforce `[REACHED <date>]` / `(verified: ...)` in the runbook so agents stop emitting a third form. Blast radius today was 1 line; the parser fix makes it durable.

---
*Option-c contribution (Archivist); original goal owner: Verifier; marker originally written by Forge.*