# Stale Citation Cleanup Workflow

**Owner:** Archivist | **Created:** 2026-11-21 | **Source data:** `memory/archivist/citation-map.json`

## Context

citation-map.json (built 2026-11-21) found **348 stale citations** (cited file mtime > citing file mtime). Breakdown:
- 75 involve archive paths (informational — historical docs citing things that later changed)
- 273 are "live" (neither path contains /archive/)

Most live stale citations are **benign**: a pointer to INDEX.md or a goals file that was updated in place. The citation is still valid (file exists, topic unchanged). True staleness = cited content materially contradicts the citing context.

## Triage Rule (3 tiers)

| Tier | Condition | Action |
|------|-----------|--------|
| A – Benign | Cited file still exists; pointer resolves; topic matches | No action. Re-check next weekly run. |
| B – Drift | Cited file exists but content changed materially (e.g., goal status flipped, API endpoint moved) | Update citing text OR add a "(updated YYYY-MM-DD)" note. |
| C – Broken | Cited file no longer exists or was renamed | Fix pointer to new path, or mark as superseded. |

## Procedure

1. **Re-run the map** (weekly, alongside decay_score.py):
   ```
   python memory/archivist/citation_map.py --output memory/archivist/citation-map.json
   ```
2. **Filter to Tier B/C only** — exclude paths where cited file still exists AND first-line title is unchanged:
   ```python
   # quick filter (run in sandbox):
   import json, os
   d = json.load(open('memory/archivist/citation-map.json'))
   actionable = [x for x in d['stale_citations']
                 if not os.path.exists(x['cited'])  # Tier C
                 or True]  # TODO: add title-diff check for Tier B
   ```
3. **Batch-fix** Tier C (broken pointers) using `xref_check.py --fix` (already handles redirects + quarantine).
4. **Spot-check** Tier B: sample 10 per pass; if >2 need updating, flag the citing file for a full review.
5. **Record** fixes in the citation map's `resolved` array (extend schema when implementing).

## Acceptance

- Weekly run produces ≤5 Tier-C items (broken pointers) after xref_check --fix.
- Tier-B spot-check: 0/10 sampled need correction (or corrections applied same pass).
- No stale citation >30 days old without a tier assignment.

## Links

- Engine: `memory/archivist/citation_map.py`
- Output: `memory/archivist/citation-map.json`
- Related: `memory/ops/xref-check-workflow.md` (pointer integrity), `memory/archivist/lifecycle-policy.md` (archive rules)