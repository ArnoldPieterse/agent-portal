# Designer - 10 goals (set 2026-11-23, cycle-13)

Focus: Production Hardening & Self-Sustaining Operations. Cycle 13 makes the cockpit production-grade: accessible, performant, and self-documenting.

1. **Cockpit Accessibility Audit** - `python memory/designer/a11y_audit.py`: audit the portal UI for WCAG AA compliance: contrast ratios >=4.5:1, all interactive elements keyboard-navigable, ARIA labels on icon buttons, focus visible states. Emit report to memory/designer/a11y-<date>.md with pass/fail per criterion. Verified: >=20 checks defined; a low-contrast element is detected; all P0 issues have CSS fix suggestions.

2. **Portal Performance Budget** - Define and enforce performance budgets: initial load <2s, LCP <2.5s, CLS <0.1, JS bundle <200KB. `python memory/designer/perf_budget.py`: measure against budget using Playwright; emit PASS/FAIL per metric. Verified: 4 metrics measured; a >100KB CSS file causes bundle size FAIL; report includes waterfall timing.

3. **Dark Mode Contrast Fix** - Audit dark mode color pairs for contrast compliance; fix any <4.5:1 in ui/app.css. Verified: all text/background pairs in dark mode >=4.5:1 (measured via Playwright computed styles); screenshot evidence at memory/designer/dark-contrast-<date>.png.

4. **Cockpit Panel Layout Stress Test** - `python memory/designer/layout_stress.py`: test the cockpit at 6 viewport widths (768, 1024, 1200, 1400, 1920, 2560) and 3 content densities (empty, normal, overflow); verify no element overflows its container or overlaps another. Verified: 18 combinations tested; 0 overflow/overlap violations; screenshots archived.

5. **UI Component Library Doc** - Document every reusable CSS class/component in the portal: name, purpose, usage example, accessibility notes. Emit memory/designer/ui-components.md (one section per component). Verified: >=15 components documented; each has a usage example that renders correctly; new developers can build a panel using only the doc.

6. **Notification System UX** - Design and implement the notification bell panel: unread badge, click-to-expand, individual dismiss, mark-all-read, keyboard shortcut (B). Verified: all 5 interactions work in Playwright; badge count updates on new event; Esc closes panel; no layout shift on expand.

7. **Print-Ready Report Layout** - Create a print stylesheet (@media print) for the cockpit: hide nav/toggles, full-width content, page breaks between sections, readable font sizes. Verified: window.print() in Playwright produces a clean PDF (no clipped content, no dark backgrounds); screenshot evidence.

8. **Cockpit Empty States** - Design and implement empty states for: no goals yet, no recent activity, search with no results, agent offline. Each should have an icon, helpful text, and a CTA button. Verified: 4 empty states implemented; each renders when its condition is true (tested via Playwright); no "undefined" or raw JSON visible.

9. **Responsive Breakpoint Audit** - `python memory/designer/breakpoint_audit.py`: test all portal panels at mobile (375px), tablet (768px), desktop (1024px+); verify text doesn't overflow, buttons remain tappable (>=44px touch target), and layout is usable without horizontal scroll. Verified: 3 breakpoints x 5 panels = 15 combinations; 0 horizontal scroll violations; all tap targets >=44px.

10. **Cockpit Tour & Onboarding** - Implement a first-visit tour: 5-step overlay highlighting key cockpit areas (goal bar, agent list, activity feed, settings, help). Skippable, resumable, stores completion in localStorage. Verified: tour appears on first visit; all 5 steps render correctly; skip button works; doesn't reappear after completion (verified via Playwright localStorage check).
