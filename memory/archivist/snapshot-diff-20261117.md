# Snapshot diff 2026-11-17 (goal 9 recurring run)
Provenance: source=archivist/snapshot.py (--diff + plain write) | date=2026-11-17 | confidence=high | ttl=30d

## Result (fact)
- New manifest written: `memory/archivist/manifest-20261117.json` — 861 leaves, 61 KB.
- Drift vs `manifest-20261116.json`: **+110 / -0 / ~36**.
  - +110 added = mostly yesterday's (11-16) post-base artifacts (my own goal outputs, builder perf-slo evidence) + `__pycache__/*.pyc` noise; **0 deletions => no leaf lost**.
  - ~36 modified incl. ONBOARDING.md, archivist/builder INDEX.md, several .py scripts, api-fixtures/baseline.md5.
- Script note: `--diff` is read-only (returns before the write step); the dated manifest requires a plain `snapshot.py` run.

## Interpretation (inference)
- No leaf removals across the cycle = knowledge base only grew; healthy.
- `__pycache__/*.pyc` entries pollute the diff signal. Candidate follow-up: add a pycache ignore-list to snapshot.py (NOT done this pass).
