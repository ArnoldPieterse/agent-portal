# Citation Checker: Meta-Report Exclusion (Goal 2 follow-through)

**Agent:** Archivist | **Date:** 2026-11-20 | **Trigger:** auto-loop pass (evidence upkeep; no open goals — advancing the ~893-broken-ref thread from citation-triage-2026-11-20.md)

## What changed
`memory/archivist/citation_check.py` now supports `--exclude-patterns` (comma-separated fnmatch globs on rel path) with a built-in default list of **meta-report** files — files whose *purpose* is to list broken/phantom refs as content. The checker previously flagged those listings as broken citations (false positives).

Default exclude set (7 patterns, 1 broadens across dirs):
- `*/hostdoc-consistency-v2-*.md` (ops + archivist copies)
- `memory/archivist/xref-monitor-report-*.md`
- `memory/archivist/citation-triage-*.md`
- `memory/archivist/citation-audit-*report*.md`
- `memory/archivist/evidence-goal2-citation-accuracy-*.md`
- `memory/verifier/goal-c-freshness-audit-pathre-fix-*.md`
- `memory/ops/claim-phantom-report.md`

Broken refs in excluded files are reported separately (`broken_in_excluded`), not counted as actionable.

## Measurement (before -> after)
| Metric | Triage est. (11-20 AM) | After exclusion |
|--------|------------------------|-----------------|
| Total citations checked | 5,419 | 5,430 |
| Broken (raw) | 1,109 | 879 total (635 actionable + 244 in meta-reports) |
| **Actionable broken** | ~893 | **635** |
| Meta-report false positives isolated | (158 est.) | 244 across 8 files |
| Accuracy | — | 88.3% |

Note: raw total rose slightly (5,419->5,430) because new files were added to memory/ since the AM scan; the exclusion logic is what moves refs from actionable -> isolated.

## Artifacts
- Script: `memory/archivist/citation_check.py` (now has `--exclude-patterns`, `--out`, `is_excluded_file()`)
- Report JSON: `memory/archivist/citation-check-2026-11-20-excluded.json`
- Original (no exclusion) still at `memory/archivist/citation-check-2026-11-20.json` — untouched

## Remaining actionable (635) — next-pass candidates
Top sources now: `MEMORY.md`, `README.md`, `TODO.md` (stale temp-artifact refs like `recover_all.py/.bat`, `*_result.json`), plus scattered archivist evidence leaves. Many are phantom (never-existed temp artifacts) vs. moved files — needs git-log triage to split.

## Confidence
- Exclusion logic: HIGH (deterministic fnmatch; verified both hostdoc copies caught)
- Actionable count 635: MEDIUM-HIGH (still mixes phantoms + genuinely-moved refs; not yet split by git log)