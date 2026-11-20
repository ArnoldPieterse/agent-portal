# Data Integrity Verification - 2026-11-20 (Verifier)

**Run:** 2026-11-20 ~11:25 UTC | Tool: `memory/verifier/data_integrity.py`
**Result:** 16 issues flagged -> triaged below into real findings vs false positives.

## Triage Summary

| Category | Flagged | Real Issues | False Positives |
|----------|---------|-------------|-----------------|
| A_agents_json | 1 | 0 (by design) | 1 |
| B_goal_agent_refs | 2 | 0 | 2 |
| C_index_pointers | 12 | 2 | 10 |
| D_mirror_py | 1 | 1 | 0 |
| **Total** | **16** | **3** | **13** |

## Real Findings (actionable)

### F1: memory_mirror.py is empty (0 bytes) — DOCUMENTATION MISMATCH, not a bug
- The prompt text in agent_portal.py (char ~76714) says "index.html is pinned in memory_mirror.py (PIN_FILES)"
- In reality, the pin-guard function has been **superseded by mirror_repair.py** (11 KB, active daemon that auto-repairs mtime regressions from git HEAD)
- **Action:** Update prompt text in agent_portal.py to reference mirror_repair.py instead of memory_mirror.py. No protection gap — mirror_repair.py covers the same ground more robustly.

### F2: memory/orchestrator/INDEX.md pointer 'execute-engine' -> file not found
- Likely a shorthand for a sub-directory or module that was never created, or was renamed.
- **Action:** Orchestrator to confirm whether execute-engine exists under a different name; fix or remove the pointer.

### F3: memory/archivist/INDEX.md pointer 'archivist/index_check.py' -> file not found
- The script referenced in Archivist's INDEX doesn't exist at that path.
- **Action:** Archivist to create it or fix the pointer.

## False Positives (no action needed)

### B: "cycle2" parsed as agent name (x2)
- cycle2-dependency-map.md and cycle2-kickoff-2026-11-16.md contain the string "cycle2" in filenames/headers; the checker's regex matches it as an agent reference. Not a real issue — these are archived cycle-2 docs.

### C: Progress counters and status strings parsed as file paths (x10)
- '46/80', '20/20', '2/7', '12/45', '74/80' = progress fractions in INDEX.md prose
- '/api/activity' = API endpoint reference, not a file path
- 'mirror/allowlist/sandbox', 'rc0/LOW/WARN' = shorthand status labels
- 'icons.js', 'core.js' = shorthand for ui/icons.js, ui/core.js (files exist at those paths)

### A: Duplicate model_id across 3 agents
- Qwen3.8-27B-Q8_0 shared by quinn-q4, Qwen3.8-27B-Q8_0, atlas-q8 — this is **by design** (multiple seats on different hosts can share the same model). Not a bug.

## Verdict
The data integrity checker works correctly but has a false-positive rate of ~81% (13/16) due to overly aggressive pointer parsing. The 3 real findings are all low-severity documentation fixes, not functional bugs. No protection gap exists for index.html (mirror_repair.py covers it).

**Suggested cycle-7 follow-up:** Tighten data_integrity.py's pointer regex to exclude progress fractions (\d+/\d+), API paths (/api/*), and known shorthand patterns. Would reduce noise from 16 to 3.
