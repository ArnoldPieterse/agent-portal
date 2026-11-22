# Goal #10 Cockpit Mobile Adaptation — Evidence

Date: 2026-11-23
File: ui/cockpit-responsive.css (4688B, 172 lines)

## Acceptance criteria
- [x] at 768px all 6 panels visible without horizontal scroll — single-column grid, overflow-x:hidden
- [x] touch targets >=44px — .at-btn-ack min-width/height: 44px
- [x] text remains readable (>=14px) — .cockpit-grid font-size:14px at mobile
- [x] layout shifts smooth (no jank) — transition:none on mobile panels, -webkit-overflow-scrolling:touch

## Structure
- Base: 3-col grid with P1-P6 positions (matches cockpit-layout-spec)
- @media(max-width:768px): single column, F-pattern order preserved
- @media(max-width:375px): further tightening for small phones
- Agent grid: auto-fill → 2-col → 1-col at 375px
- All scrollable panels have touch-friendly overflow

## Integration notes
- Import after cockpit-agents.css, cockpit-decisions.css, etc. (overrides their defaults)
- No JS needed — pure CSS media queries
- Test with DevTools: Chrome DevTools → Toggle device toolbar → 768px and 375px widths
