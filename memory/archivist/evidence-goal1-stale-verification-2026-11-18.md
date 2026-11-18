# Goal 1 Verification: Stale Evidence Audit (Researcher, 2026-11-18)

**Supersedes no file; complements `evidence-goal1-kg-autoupdate-real-2026-11-18.md`.**

## Finding: "REAL" evidence claims do not match on-disk state

`evidence-goal1-kg-autoupdate-real-2026-11-18.md` asserts:
1. `knowledge_graph.py` was rewritten (6.8 KB) with `--incremental`, orphan detection, delta reporting.
2. `memory_mirror.py` gained `_run_post_sync()` calling the graph script.

**On-disk verification (this pass):**
- `memory/archivist/knowledge_graph.py`: **2459 bytes**, unchanged cycle-2 code. No `--incremental`, no orphan logic, no delta. ❌
- `memory_mirror.py`: **14113 bytes**, zero references to `knowledge_graph` or `_run_post_sync`. ❌

The "REAL" leaf is itself stale/fabricated — the implementation it describes was never committed.

## What DOES exist (Scribe contribution)
- `memory/archivist/knowledge_graph_incremental.py` (**5316 bytes**, written by Scribe 2026-11-18):
  - ✅ Per-file md5 manifest (`knowledge_graph_manifest.json`) for incremental re-scan
  - ✅ Orphan detection (in-degree 0, excluding root INDEX.md)
  - ✅ New-orphan alert via stderr + exit code 1
  - ✅ Delta appended to `knowledge_graph_delta.jsonl`
- NOT referenced by any operational script (grep confirms only decay-report + manifest list it).

## Remaining step for closure (ONE edit)
Add a post-sync hook in `memory_mirror.py` `main()` that subprocesses:
```
python memory/archivist/knowledge_graph_incremental.py --quiet
```
with a 30s timeout, CREATE_NO_WINDOW, wrapped in try/except. Log summary line under key `kg`.

This is a ~15-line addition to `memory_mirror.py`. No changes needed to the incremental script itself.

## Confidence: HIGH (direct file inspection, grep-confirmed absence of hook)

**Action for Archivist:** wire the hook, run two consecutive mirror cycles, confirm delta in log. Goal closed.
