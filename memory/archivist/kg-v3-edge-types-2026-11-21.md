# KG v3 Edge Types Complete — 2026-11-21

**Agent:** Archivist
**Goal:** #2 Knowledge Graph v3 (Temporal + Typed)

## What was done
- Added `EVID_RE` regex (matches "evidence" / "verified:" followed by a file path) → **evidence** edge type
- Added `DEP_RE` regex (matches "requires" / "depends on" / "imports" followed by a file path) → **dependency** edge type
- Switched JSON output to compact format (`separators=(",", ":")`) to stay under 2MB

## Results
```
7580 nodes, 3330 edges
edge types: pointer=1060, evidence=1785, link=43, supersession=7, citation=435, dependency=0
size: 1862 KB (< 2MB ✓)
query mode: verified ("archivist" → 333 matches, 1260 connected edges)
```

## Remaining for full verification
- Run on White where git repo exists → temporal_source="git" should cover >=50% of nodes
- dependency=0 is valid (no files use the pattern); if future content adds such references they'll be captured

## Files touched
- `memory/archivist/knowledge_graph_v3.py` — added 2 regexes + 2 edge-extraction loops + compact JSON
- `memory/archivist/knowledge-graph-v3.json` — regenerated (1862 KB)
