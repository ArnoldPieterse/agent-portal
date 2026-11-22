# Stale Citation Triage Workflow
Agent: Archivist | Created: 2026-11-22 | Source: citation-map.json (348 stale edges)

## Problem
`citation-map.json` flags 348 citations where the cited file's mtime > citing file's mtime.
Most are benign (archived docs referencing live files that evolved). A small subset may be
genuinely broken references that mislead retrieval.

## Triage Criteria (apply in order)
1. **Citing file is archived** (path contains `/archive/` or date-stamped >7 days old) → DISMISS.
   Rationale: historical docs are snapshots; their pointers were valid at write-time.
2. **Cited file still exists and content is superset** (cited grew, not shrank) → DISMISS.
   Rationale: the reference is still valid, just points to a richer document now.
3. **Cited file was deleted/renamed** → ACTION: update pointer or add redirect in INDEX.md.
4. **Citing file is live (non-archived, <7 days old) and cited content materially changed**
   (size delta >20% or title changed) → ACTION: re-verify the claim; update or annotate.

## Batch Cadence
- Run `python memory/archivist/citation-map.py --stale-only` weekly (piggyback on freshness scoring schtask).
- Triage only category 3+4 items; log dismissals to `memory/archivist/stale-dismissal-log.jsonl`.
- Target: <20 actionable stale citations at any time (current estimate: ~15 of 348 after criteria 1+2 filter).

## Ownership
- Archivist: runs the scan, applies criteria 1-2 auto-dismiss.
- Owner of cited file: fixes category 3-4 items (or delegates to Archivist for pointer-only fixes).

## Quick Command
```
python memory/archivist/citation-map.py --stale-only --min-severity actionable
```
(Not yet implemented; current fallback: filter citation-map.json stale_citations list by the criteria above in a one-liner.)
