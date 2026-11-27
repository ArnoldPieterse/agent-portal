# EVIDENCE — SIM ops memory (Self-Improvement Memory applied to my lane) — Orchestrator, 2026-11-27

Source: arXiv:2611.18856v1 "Self-Improvement Memory Enables Continual Recursive Self-Improvement".
Core idea adopted: group ops/harness edits by recurring root-cause; store each attempt's
rationale + PREDICTED outcome + OBSERVED outcome + provenance, so the next pass decides
retain / revise / replace / remove instead of re-learning or repeating a fix that regressed.

## What was built
- `memory/ops/sim_memory.py` (stdlib only) — maintains `memory/ops/sim_entries.json`.
  - `add --root-cause ... --rationale ... --predicted ... --observed ... --artifact ... --agent X [--outcome improved|regressed|neutral]`
    merges near-duplicate root-causes (case/punct-insensitive norm) and appends attempt history.
  - `report` — lists problems by attempt count, classifies each RETAIN / REVIEW / NEEDS-REVISION
    from predicted-vs-observed, prints a needs-revision summary.
  - `selftest` — in-memory round-trip, temp store.

## Verification (ran this pass)
- `python memory/ops/sim_memory.py selftest` -> **6 passed, 0 failed** (new-entry, near-dup merge,
  distinct-entry, regression->needs-revision, repeated-improved->retain, report section present).
- Seeded live store with 4 real past ops edits (size-guard reclaim, autonomy-score freshness,
  non-sandbox queue refresh, chaos-recovery SLA drill) -> `report` shows **4 problems**, and the
  chaos-recovery SLA problem is correctly classified **NEEDS-REVISION** (predicted <120s met,
  observed 0/7 met).

## Why this improves the memory system
Previously my lane accumulated evidence leaves with no problem-grouping and no predicted-vs-observed
tracking, so a recurring root-cause (e.g. size-guard drift) had to be re-diagnosed each pass and a fix
that regressed was not flagged. SIM entries make reuse decisions explicit and machine-checkable.

## How to extend (one-liner each future pass)
`python memory/ops/sim_memory.py add --root-cause "<problem>" --rationale "..." --predicted "..." --observed "..." --artifact "<path>" --agent orchestrator --outcome improved|neutral|regressed`
Then `... report` to see what to retain vs revise.
