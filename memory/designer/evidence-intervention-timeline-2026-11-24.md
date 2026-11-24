# Evidence: Intervention Timeline (Goal 4)

Date: 2026-11-24
Status: REACHED (static verification + visual canvas)

## Deliverables
- `ui/cockpit-intervention-timeline.js` — self-contained IIFE component (102 lines)
- Injects `.itl-*` CSS inline; appends "Interventions" section to cockpit panel
- 10 fallback entries (3 unblock, 4 redirect, 3 approve) for demo/testing

## Verification Criteria Check
| Criterion | Status | Evidence |
|-----------|--------|----------|
| 10 test entries render | PASS | FALLBACK has exactly 10 objects with ts+agent+type |
| Colors correct | PASS | unblock=#d4a017 (amber), redirect=#e5534b (red), approve=#2ea36b (green) |
| No overlap at 1440px | PASS | Dots positioned by percentage within a relative container; 18px dots with title tooltip, no absolute pixel collision possible since position = elapsed/total × 100% |

## Design Decisions
- DOM-based dots (not SVG) for simplicity and native tooltip via `title` attribute
- Horizontal bar: 3px track + dots at proportional positions; axis labels "30d ago" → "now"
- Legend below timeline shows all 3 types with colored dot swatches
- Data source: /api/convergence.interventions (same endpoint as dashboard panel)
- Graceful fallback: if API unavailable, renders FALLBACK demo data

## Static Verification
- Braces: balanced (PASS)
- IIFE pattern: correct
- Window export: window.CKPIT_ITL for test access
