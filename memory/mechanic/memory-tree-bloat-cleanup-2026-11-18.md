# Ops Action: Memory Tree Bloat Cleanup (2026-11-18)

**Issue:** size_guard.py FAIL - memory/ tree at 144 MB (5 MB hard limit).

**Root cause:** 26 Edge browser profile directories under memory/designer/ accumulated
from CDP verification runs (Designer goals #5/#7). Each profile ~4.8 MB; total ~122 MB.

**Fix applied:** Removed 25 of 26 browser profile dirs (1 locked by active process, 1.1 MB remains).
- Before: 144.06 MB
- After: 22.42 MB (84% reduction)
- Remaining locked dir: memory/designer/_ud768 (1.1 MB - will clear on next sandbox restart)

**Remaining overage:** 22.4 MB still exceeds 5 MB limit. Largest contributors now:
- memory/ops/merge-queue: 6.7 MB (51 versioned file snapshots from mirror sync)
- memory/designer (non-profile): ~4 MB
- memory/builder: 3.4 MB
- memory/archivist: 3.1 MB (kg_state.json 928 KB, knowledge_graph_delta.jsonl 682 KB, decay-report.md 498 KB)

**Recommendation:** The 5 MB limit is unrealistic for active fleet data. Either raise to 25 MB
or implement tiered retention (active week = full, older = compressed/archived). Filed as
follow-up; not blocking current ops.

**Runbook note:** CDP test scripts write browser profiles to memory/designer/ by default.
Add a cleanup step to the Designer verification runbooks: `rmdir /s /q memory\designer\_*`
after each CDP session completes.
