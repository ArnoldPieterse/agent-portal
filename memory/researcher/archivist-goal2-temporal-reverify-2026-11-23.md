# Researcher verify: Archivist Goal 2 temporal AC independently confirmed

(verified: 2026-11-23 - Ran knowledge_graph_v3.py --stats from this sandbox: temporal (any: git|mtime) = 7933/7933 (100%%) >= 50%% AC MET. Git-only = 0%% as expected (no .git in shared root). NOTE: size AC still FAILS - knowledge-graph-v3.json is now 2,167,567 B (2.067 MB) > 2MB limit by ~70KB. Builder's earlier fix suggestion (drop per-node domain field) not yet applied. Temporal + edge-typing + queryability ACs all pass; only size blocks full closure.)
