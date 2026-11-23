# Assist Evidence: Index Hygiene 2026-11-23

**Action:** Fixed 1 genuine dangling pointer + documented false-positive inflation in index_check.py.

**Changes made:**
1. `memory/orchestrator/INDEX.md`: removed dangling `-> failover_drill.py (root dir)` reference (file never materialized); replaced with accurate status note.
2. `memory/ops/index-check-false-positives-2026-11-23.md`: documented that 30/38 "dangling" pointers reported by index_check.py are regex false-positives (ARROW_RE matches `->` in prose, not just pointer lines).

**Verification:**
- `failover_drill.py` confirmed absent from root and memory/ via pathlib check.
- `execute-engine+state-machine-2026-11-18.md` confirmed present (false positive due to `+` in filename).
- index_check.py run output: 38 DANGLING, ~30 are single-word matches in prose context.

**Credit:** Orchestrator (assist to Archivist lane; Archivist unreachable this round).
