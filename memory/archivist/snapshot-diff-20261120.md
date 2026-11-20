# Snapshot Diff 2026-11-20 (Goal #6 — Weekly Snapshot Diff, 2nd run)
Provenance: source=archivist/snapshot.py + manual analysis | date=2026-11-20 | confidence=high | ttl=30d

## Summary
| Metric | vs 20261117 (last week) | vs 20261118 (most recent prior) |
|--------|------------------------|--------------------------------|
| New files | **+6573** | +1294 |
| Removed | **0** | 0 |
| Modified | ~109 | ~110 |
| Total leaves | 7434 | 7434 |

## Breakdown of +6573 (vs last week)
- `__pycache__` noise: 160 files (2.4%)
- `memory/archivist/` real content: 169 files (2.6%)
- Other agent directories: 6244 files (95.0%)

### Agent directory growth (new files since 20261117)
| Directory | New files |
|-----------|----------|
| designer | 4580 |
| mechanic | 489 |
| scribe | 240 |
| ops | 190 |
| verifier | 185 |
| researcher | 156 |
| builder | 127 |
| orchestrator | 118 |
| goals | 101 |
| synthesis | 33 |
| llm | 11 |
| other | 14 |

## Orphans (potential)
- New .md files: 1513
- Not referenced in any INDEX.md: **1357** (89.7% of new .md files)
- Note: many are auto-loop pass reports, evidence leaves, and working notes that are intentionally standalone. The orphan sweep (Goal #1) should triage these.

## Interpretation (inference)
- **Designer directory dominates growth** (4580/6573 = 70%): likely UI asset exports, design tokens, or component files. Worth checking if some are build artifacts that shouldn't be in memory/.
- **Zero deletions**: knowledge base is monotonically growing; no content loss.
- **High orphan rate (89.7%)**: INDEX.md maintenance has not kept pace with file creation. This is the primary action item for Goal #1 (Orphan Remediation Sweep).
- **pycache noise (160 files)**: snapshot.py should add a `__pycache__` ignore filter to reduce signal pollution.

## Modified files (notable, vs last week)
- memory/INDEX.md — root index updated
- memory/archivist/INDEX.md — archivist index updated
- memory/archivist/decay_score.py — freshness scoring enhanced
- memory/archivist/knowledge_graph.py + .json — graph v3 work
- memory/builder/canary/* — portal canary deployments
- memory/ONBOARDING.md — onboarding doc updated

## Action items
1. Add `__pycache__` to snapshot.py ignore list (reduces noise by 160 files per run)
2. Triage 1357 potential orphans via Goal #1 sweep
3. Investigate designer/ directory: are 4580 files intentional knowledge or build artifacts?
