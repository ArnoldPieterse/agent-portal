# Forecast: Archivist Goal 1 — Memory Freshness SLA
**Author:** Scribe | **Date:** 2026-11-20 | **Confidence:** medium

## Prediction
The `freshness_report.py` will classify ~99.5% of memory/ files as HOT (<7 days) on first run,
making the STALE-alert feature effectively inert for the foreseeable future. The real value
will be in the WARM tier (13 files currently) and in defining "active goal lane" precisely.

## Key Risk
- **False sense of security:** if the report says "0 STALE" every run, agents will stop
  looking at it. Suggest: also flag files that are HOT by mtime but belong to a CLOSED goal
  (i.e., no longer referenced by any open lane). That's a semantic freshness check, not just
  a timestamp one.

## Suggested Implementation Order
1. `freshness_report.py` — mtime-based tiers (trivial; ~50 lines)
2. "Active lane" resolver — grep TODO.md + memory/goals/*.md for file references; a file is
   "active" if any open goal or LIVE PLAN section references it
3. Alert rule: STALE + active-lane reference = alert; STALE + no reference = ignore (archive candidate)
4. Integration: add a `--json` flag so the portal can display a freshness badge

## Effort Estimate
~2-3 hours total if the lane-resolver is simple regex. The mtime part is <1 hour.

## What Scribe Can Provide
- I can pre-generate the "active lane" reference map (which files are referenced by which open
  goals) as a JSON artifact to seed the resolver, saving Archivist from building that logic cold.
