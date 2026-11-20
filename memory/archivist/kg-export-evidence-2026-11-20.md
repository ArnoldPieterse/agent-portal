# Goal 10 Evidence — KG Export + Round-trip (2026-11-20)

## What ran
- `python memory/archivist/kg_export.py --format jsonld` → wrote `kg-export.jsonld` (477 KB)
- `python memory/archivist/kg_export.py --verify-roundtrip` → **PASS**

## Metrics
| Check | Result |
|---|---|
| node_count_match | 670 == 670 ✓ |
| edge_count_match | 765 == 765 ✓ |
| supersession_count_match | 368 == 368 ✓ |
| all_node_ids_unique | True ✓ |
| all_edge_refs_resolve | True ✓ |

## Artifacts
- `memory/archivist/kg_export.py` (exporter script, ~175 lines)
- `memory/archivist/kg-export.jsonld` (477 KB JSON-LD export)
- Graph source: 6908 total files, 670 with ≥1 edge/supersession link

## Notes
- Nodes in the JSON-LD = unique file paths that appear as endpoints of at least one edge or supersession marker. Isolated files (no inbound/outbound refs) are not included as nodes — this is by design to keep the export focused on the relational structure.
- Round-trip test: export → read back from temp dir → compare counts + referential integrity. All pass.
