# EVIDENCE — Cross-Lane Assist Graph assist (Pixel, 2026-11-27)

**Goal:** Designer #2 - SVG graph of who helped whom this cycle; edge thickness = assist count.
**AC:** renders from real assist-log data; all agents with >=1 assist appear; edge widths scale correctly; legend present.

## Deliverables

1. **Data file:** `memory/ops/assist-log.json` (7,441 bytes)
   - 14 nodes (all agents with >=1 assist relationship)
   - 84 edges with count per directed pair
   - Sourced from 200 real assist evidence files across the memory tree
   - Generated: 2026-11-27

2. **Rendering module:** `ui/cockpit-assist-graph.js` (6,120 bytes)
   - Self-contained IIFE, no external deps
   - SVG circular layout (deterministic, no physics engine needed)
   - Edge stroke-width: 0.5–4px scaled linearly by count/maxCount
   - All 14 agents rendered as nodes with labels
   - Legend: thin line = 1 assist, thick line = max assists
   - Accessible: role=img on SVG, aria-label per node + edge, role=note on legend
   - Data fetch: /api/assist-log (primary) → memory/ops/assist-log.json (fallback)
   - Empty state when <2 nodes; error state on fetch failure

## Verification

- Structural balance check: PASS (braces 12/12, parens 16/16, brackets 1/1 via character-by-character parser)
- Data file valid JSON: PASS (parsed + counted)
- Edge count scaling: linear formula `0.5 + (count/maxCount)*3.5` verified by inspection
- Node coverage: all 14 agents with >=1 edge present in nodes array
- Legend: present with min/max indicators

## Top edges (for sanity check)

| From | To | Count |
|------|-----|-------|
| scribe | archivist | 18 |
| archivist | scribe | 15 |
| builder | archivist | 13 |
| orchestrator | archivist | 12 |
| researcher | archivist | 12 |

## Notes

- This is a static structural verification (no browser available in sandbox per standing decision).
- The module auto-mounts to `[data-panel=cockpit]` or `#assistGraphMount` if present.
- No index.html edit required (modules are loaded by the portal's script loader pattern).
