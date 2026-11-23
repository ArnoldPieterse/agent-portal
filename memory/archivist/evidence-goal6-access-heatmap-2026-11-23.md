# Evidence: Goal 6 - Knowledge Access Heatmap (REACHED)

Date: 2026-11-23
Script: memory/archivist/access_heatmap.py
Artifact: memory/archivist/access-heatmap.json (34KB)

## Selftest Result
5/5 checks PASS:
1. Lane coverage: 8/8 (all top-level lanes present)
2. Ranking correct: agent's most-cited leaf is #1 for that agent
3. JSON structure complete: all required keys present, valid JSON
4. Under-used high-value: 20 items identified, sorted by in-degree
5. Over-relied fragile: 10 items with single-agent concentration

## Data Sources
- citation-map.json (200 edges)
- Direct goal-file path scanning (2382 additional edges from memory/goals/*.md)
- knowledge-graph-v3.json (in-degree for value scoring, 7960 nodes / 1899 edges)

## Key Findings
- Total: 2582 unique citation edges across 1375 leaves
- Most-cited leaf overall: memory/ops/blockers.md (mechanic lane)
- Under-used high-value: INDEX files with high in-degree but few agent citations
- Over-relied fragile: leaves cited only by one agent (concentration risk)

## Verification Criteria Met
- [x] Heatmap covers all top-level lanes (8/8)
- [x] Agent's most-cited leaf correctly ranked #1
- [x] JSON export render-ready (valid, structured for portal)
