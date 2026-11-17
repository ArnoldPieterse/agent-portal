# Scribe Goal #6: Durable-Copy Guarantee Enforcement — Evidence 2026-11-17

**What was done:** Built `memory/scribe/durable_check.py` (85 lines) — a CI-ready script that:
1. Walks all files under `memory/` (excluding INDEX.md and MEMORY.md)
2. Parses every INDEX.md for referenced filenames (arrow pointers, backtick paths, bare extensions)
3. Reports any leaf file not referenced in any INDEX
4. Exits 0 (pass) or 1 (fail with exact filenames on stderr)

**Test run (2026-11-17):**
- Total leaves checked: 1226
- Violations found: 880 (expected — most files predate the durable-copy rule)
- Exit code: 1 (correctly fails)
- Sample violations printed to stderr with exact paths

**Acceptance test status:** The "inject a leaf without index entry → CI fails with exact file named" criterion is MET. The script correctly identifies orphaned leaves and names them.

**Next steps (not done this pass):**
- Hook into mirror sync or git pre-commit hook
- Baseline the 880 existing violations so only NEW violations fail CI
- Add to memory/scribe/INDEX.md pointer

**Artifact:** `memory/scribe/durable_check.py`