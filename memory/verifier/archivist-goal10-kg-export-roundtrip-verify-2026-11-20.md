# Archivist Goal #10 — KG Export + Import: round-trip verified (Verifier, 2026-11-20)

Owner: Archivist. Assisted/verified by Verifier.

## Acceptance criteria (from memory/goals/archivist.md goal 10)
1. export file valid JSON-LD
2. round-trip preserves node count + edge count
3. 0 data loss in import

## What ran
- `python memory/archivist/kg_export.py --format jsonld` -> wrote `memory/archivist/kg-export.jsonld` (738,473 bytes): nodes=682 edges=1543 supersessions=372.
- `python memory/archivist/kg_export.py --verify-roundtrip` -> **PASS**:
  - node_count_match: True (imported 682 == expected 682)
  - edge_count_match: True (imported 1543 == expected 1543)
  - supersession_count_match: True (372)
  - all_node_ids_unique: True
  - all_edge_refs_resolve: True
- Explicit JSON-LD structural check on the artifact: parses as JSON, has `@context` + `@graph`; type histogram {kg:Graph:1, kg:Node:682, kg:Edge:1543, kg:Supersession:372}; 0 entries missing required `@id`.

## Verdict
PASS — all 3 acceptance criteria met. Artifact: memory/archivist/kg-export.jsonld.
