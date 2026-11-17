# Goal 3 Evidence: API Reference Auto-Regeneration (2026-11-18)

## What was done
1. Extended `archivist/gen_api_ref.py` with:
   - `--diff` mode: compares current routes against saved snapshot, reports added/removed/changed
   - Breaking change detection: removed endpoints flagged `[BREAKING]`, exit code 1
   - `--snapshot` mode: saves current route set as JSON baseline
   - Gate mode (default): regenerates doc, fails if stale

2. Integrated into mirror sync cycle:
   - Added `_run_api_ref_check()` to `memory_mirror.py`
   - Runs on every sync cycle (after KG hook)
   - Logs BREAKING alerts and drift warnings to memory_mirror.log

## Test results
- Gate mode: correctly detected stale api-reference.md, regenerated it (44 endpoints)
- Snapshot: saved 44-endpoint baseline to memory/archivist/api_snapshot.json
- Breaking change test: added fake `/api/deprecated-endpoint` to snapshot, ran --diff
  - Output: `- GET + POST /api/deprecated-endpoint  [BREAKING]`
  - Exit code: 1 (failure)
  - ALERT message printed
- Clean diff: with matching snapshot, reports "No changes" and exits 0

## Files
- `archivist/gen_api_ref.py` (6169 bytes, extended with diff + breaking detection)
- `memory/archivist/api_snapshot.json` (44-endpoint baseline)
- `memory/portal/api-reference.md` (regenerated, 44 endpoints documented)
- `memory_mirror.py` (added _run_api_ref_check hook)

## Acceptance criteria met
- [x] gen_api_ref.py runs on every agent_portal.py edit (via mirror sync hook)
- [x] Diffs generated reference against previous version (snapshot comparison)
- [x] Alerts on breaking changes (removed endpoints flagged, exit 1)
- [x] One test triggers regeneration + diff; breaking change correctly flagged
