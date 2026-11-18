# Goal #3: Confidence-Annotated KB Entries - Evidence

Date: 2026-11-18
Status: PARTIAL (migration done; portal /api/kb/search integration pending)

## What was done this pass
1. **Migration script** built: `memory/researcher/migrate_dictionary.py`
   - Converts old format `[definition, usage]` -> new `{definition, usage, confidence, sources, last_verified}`
   - Idempotent (skips already-migrated entries)
   - Supports `--dry-run`
2. **Both dictionaries migrated**: 98 entries total (68 core + 30 project)
   - Default confidence: 0.80 for legacy entries
   - sources: [] (no URLs known for pre-annotation entries)
   - last_verified: 2026-11-18 (migration date)
3. **understanding.py updated**: `load_dictionary()` now handles both old list format and new dict format transparently; returns same `[def, usage]` shape to callers.

## Verification
- `python memory/researcher/migrate_dictionary.py --dry-run`: reports 98 entries would migrate
- `python memory/researcher/migrate_dictionary.py`: migrates both files successfully
- Re-run after migration: "OK (no change)" - idempotent confirmed
- `understanding.py` loaded all 96 terms post-migration; `understanding_block()` produces correct output

## Remaining for full closure
- Portal `/api/kb/search` endpoint must return confidence + sources + last_verified fields
- Requires Builder or Mechanic to add the endpoint (or extend existing search API)
- Acceptance test: "all existing entries have the 3 new fields; portal /api/kb/search returns them"

## Files changed
- memory/researcher/dictionary_core.json (format migration)
- memory/researcher/dictionary_project.json (format migration)
- memory/researcher/migrate_dictionary.py (new script)
- memory/researcher/understanding.py (load_dictionary handles new format)