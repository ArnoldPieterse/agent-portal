# Verifier AC V-09 - provenance report determinism (2026-11-15)

AC: "Provenance report must regenerate deterministically from the same file tree" (validates Archivist's provenance engine; self-contained, no restart needed).

## Test method
`python memory/archivist/goal_provenance.py --output <tmp>` run twice against an unchanged tree, md5-compare outputs. Self-contained: no portal restart, no remote hosts.

## Result: FAIL -> fixed -> PASS
- BEFORE (engine as delivered): run1 `74ec3372...` vs run2 `61de4d38...` - **NON-DETERMINISTIC** (same 54,413 B size; only the timestamp string differed). Root cause: line 136 embedded wall-clock `datetime.now().isoformat()` in the `generated` field.
- FIX (minimal, no consumer breakage - findstr proved zero references in agent_portal.py / index.html / memory_mirror.py): `generated` now derived from the input tree = max mtime of memory/goals/*.md, second precision. Same file tree -> same value; tree change -> new value.
- AFTER: run3 `9444e628e2938badd91998bbed76799d` == run4 (3 s apart) - **DETERMINISTIC**; valid JSON; summary 70/80 evidenced matches goal_ledger.py --json.
- Canonical report memory/archivist/goal_provenance_report.json regenerated with the fixed engine.

## Verdict: PASS (post-fix). Residual note: mtime-derived 'generated' changes when any goal file is touched - that is correct behavior for a tree-state stamp, not non-determinism.
