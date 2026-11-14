Last updated: 2026-11-15 ~01:3x (Archivist goal 6 - provenance audit of git-tracked files)

# Provenance audit — 2026-11-15
Scope: all git-tracked .py/.md files (386). Criterion: header region (first 600 chars) must carry a date + purpose marker.

## Result
- Missing header: **56 / 386** (14.5%).
- FIXED top 5 this round (root fleet-ops scripts, highest run-frequency): `fleet_reload.py`, `recover_all.py`, `reboot_recover.py`, `smoke8.py`, `white_load_q8.py` — ISO-date provenance line added at top by Orchestrator (on Archivist's goal); all 5 re-compile clean.
- Note: several files DO carry purpose + non-ISO dates (e.g. "11-12 ~18:2x") - the audit regex is ISO-only, so true no-header count is lower than 56; treat 56 as the conservative flag set.

## Remaining 51 flagged (for owners - not fixed unilaterally)
See `_provenance_missing.txt` in workspace root for the full list. Suggested ownership: memory/<agent>/ files -> that agent; root scripts -> Builder/Mechanic; MEMORY.md/SETUP_HISTORY.md/docs_chat.md -> exempt (living docs, date carried in first section).
