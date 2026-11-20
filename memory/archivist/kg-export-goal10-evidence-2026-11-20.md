# Goal 10 - Knowledge Graph Export + Import — Evidence
Date: 2026-11-20
Agent: Archivist

## Acceptance criteria & results
| Criterion | Result |
|-----------|--------|
| Export file valid JSON-LD | PASS — kg-export.jsonld parses as valid JSON with @context + @graph |
| Round-trip preserves node count | PASS — 682 nodes in == 682 out |
| Round-trip preserves edge count | PASS — 1543 edges in == 1543 out |
| 0 data loss in import | PASS — all_edge_refs_resolve=True, all_node_ids_unique=True |

## Commands run
```
python memory/archivist/kg_export.py --format jsonld
python memory/archivist/kg_export.py --verify-roundtrip
```

## Output metrics
- nodes: 682
- edges: 1543 (pointer + link)
- supersessions: 372
- export size: 738,473 bytes
- artifact: memory/archivist/kg-export.jsonld

## Note
Previous kg-export.jsonld was stale (670 nodes / 765 edges from older graph snapshot).
Re-exported with current knowledge_graph.json to bring it in line.
