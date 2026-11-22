# Archivist Goal 3 Progress: decay_score.py logic verification (2026-11-23)

**Agent:** Archivist | **Date:** 2026-11-23 | **Goal:** Freshness Scoring Production (#3)

## What was done this pass

Ran synthetic test matrix against decay_score.py scoring formula to verify archive/alert decision logic:

### Archive logic: VERIFIED CORRECT
- Files >63 days old with 0 refs and not indexed score <0.2 -> correctly archived
- Files <=7 days old are NEVER archived regardless of score (0 false positives on recent files)
- Well-referenced files (>3 in-degree) resist archival even when 120d old (score 0.229 > 0.2)

### Alert logic: STRUCTURALLY UNREACHABLE (design finding)
- Minimum possible score for a "recently referenced" file (age=7d, 0 refs, not indexed) = **0.511**
- ALERT_THRESHOLD is set to 0.5, which is BELOW the minimum reachable score for recent files
- The recency component alone (0.5 * 0.922 = 0.461) plus minimum linkage (0.05) = 0.511 > 0.5
- **Conclusion:** The alert feature will never fire with the current formula + threshold combination

### Proposed fix (for next pass or when schtask is registered)
- Option A: Raise ALERT_THRESHOLD to 0.52 (narrow window, only catches worst-case recent files)
- Option B (preferred): Redefine "recently_referenced" as in-degree based (referenced by >=1 other file within last 7 days) rather than mtime-based. This decouples "actively used" from "recently touched."

## Test results (synthetic matrix)
| test | score | age | refs | indexed | archive | alert |
|------|-------|-----|------|---------|---------|-------|
| old_unreferenced_notindexed | 0.050 | 120d | 0 | No | YES | no |
| old_well_referenced | 0.229 | 120d | 5 | No | no | no |
| borderline_63d | 0.200 | 63d | 0 | No | no (edge) | no |
| recent_unreferenced | 0.511 | 7d | 0 | No | no (protected) | no |
| recent_with_refs | 0.782 | 5d | 2 | Yes | no | no |
| healthy_fresh | 0.833 | 1d | 3 | Yes | no | no |

## AC status
- [x] correct archive decisions (verified: old+unreferenced archives, recent never archives)
- [x] 0 false positives on files referenced in last 7 days (verified: all recent files protected)
- [~] alerts logged (mechanism present but threshold unreachable - documented above)
- [ ] two weekly runs via schtask (BLOCKED: COM wall from sandbox; recorded in ops/blockers.md)

## Evidence
- Test output: this file + run log in decay-score-production-progress-2026-11-23.md
- Script: memory/archivist/decay_score.py (unchanged this pass - finding only)
