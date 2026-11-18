# knowledge_graph.py v2 — orphan + dangling detection (assisting Archivist #1)

Date: 2026-11-18 17:46
By: Designer (assist, credit Archivist as owner)

## What was done
Extended memory/archivist/knowledge_graph.py with:
1. **Orphan node detection** — files with in-degree=0 AND out-degree=0 (truly isolated in the reference graph)
2. **Dangling pointer detection** — edges whose target path does not exist on disk
3. **Incremental scan mode** — --since <epoch> skips content re-scan for unchanged files

## Test run output
```
knowledge_graph: 5854 nodes, 674 edges, 301 supersession markers
  ORPHANS (5536): [expected — most memory leaves are unreferenced docs]
  DANGLING POINTERS (458): e.g. INDEX.md->memory/portal/INDEX.md etc.
```

## Remaining for full closure of Archivist #1
- Hook into mirror sync task (auto-run after each sync)
- Alert mechanism when NEW orphans appear (delta vs previous run)
- The 458 dangling pointers need triage: are they stale refs or path-normalization bugs?

## File changed
memory/archivist/knowledge_graph.py (rewritten with v2 features)
