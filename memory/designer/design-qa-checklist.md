# Design QA Checklist
Updated: 2026-11-20 (auto-loop pass, cycle-7)

Automated checks run via `python memory/designer/design_qa.py`.
Manual items require browser inspection.

## Visual
1. [ ] All panels use tokens from ui/tokens.css (no hardcoded colors)
2. [ ] Typography uses only the 5-step scale: 12/14/15/18/24px
3. [ ] Spacing uses only the 5-step scale: 4/8/12/16/24px
4. [ ] Border radius consistent (var(--br-sm), --br-md, --br-lg)
5. [ ] No orphaned/off-scale font-size or spacing values in any CSS file

## Interaction
6. [ ] All :hover rules live in ui/interactions.css (PORTAL INTEGRATION section)
7. [ ] Focus rings visible on all interactive elements (keyboard nav test)
8. [ ] Click feedback (scale 0.98) on buttons and cards
9. [ ] Touch targets >=44x44px on mobile breakpoints
10. [ ] Drag handles have grab/grabbing cursor states

## Responsive
11. [ ] No horizontal scroll at 320px, 768px, 1024px, 1440px
12. [ ] Sidebar collapses gracefully at 768px
13. [ ] Content reflows logically (not just shrinks) at each breakpoint
14. [ ] Chat composer stays usable at 320px width
15. [ ] Fleet topology diagram scales without clipping

## Accessibility
16. [ ] All text/background pairs pass WCAG 2.1 AA (>=4.5:1 body, >=3:1 large)
17. [ ] Dark mode passes AA for all visible text
18. [ ] Light mode passes AA for all visible text
19. [ ] prefers-reduced-motion disables all animations
20. [ ] ARIA labels present on icon-only buttons
21. [ ] Color is not the sole indicator of state (icons/text accompany)

## Animation
22. [ ] Panel transitions: fade+slide 150ms ease-out
23. [ ] List item entrance stagger: 30ms per item
24. [ ] Gauge fill: 600ms ease-in-out
25. [ ] No layout shift (CLS) during any animation

## Icons
26. [ ] All icons from ui/icons.js (no external library)
27. [ ] Consistent stroke weight (1.5px) across all icons
28. [ ] Icons render correctly at 16px, 24px, 32px sizes
29. [ ] currentColor inheritance works in all contexts

## Empty States & Loading
30. [ ] All 8 data panels show proper empty state when no data
31. [ ] Skeleton shimmer visible during >=500ms loads
32. [ ] No "undefined", "null", or blank white space in any panel state
