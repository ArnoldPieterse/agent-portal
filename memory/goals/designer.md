# Designer - 10 goals (set 2026-11-20, cycle-7)

Focus: Interaction design + visual polish. Cycle-5 established the token system; cycle-7 makes the portal feel alive: smooth transitions, clear hierarchy, and a consistent interaction language across all panels.

1. **Interaction Design System** - Define standard interaction patterns in ui/interactions.css + ui/interactions.js: hover states, focus rings, click feedback (scale 0.98), drag handles, scroll indicators, loading skeletons. Document each pattern with when-to-use guidance. Verified: >=6 patterns defined; all interactive elements in portal use the system; no ad-hoc :hover rules outside interactions.css.

2. **Animation/Motion System** - Add a restrained animation layer: panel transitions (fade+slide 150ms ease-out), list item entrance (stagger 30ms), gauge fill (600ms ease-in-out), notification slide-in. All animations respect prefers-reduced-motion. Verified: >=4 animations implemented; no layout shift during animation; reduced-motion preference disables all; 60fps on mid-range hardware.

3. **Information Hierarchy Audit** - Review all portal panels for visual hierarchy: primary data (large, high-contrast) vs secondary (medium) vs metadata (small, muted). Fix any panel where the most important number isn't the most visually prominent. Verified: audit report documents 5+ fixes applied; before/after screenshots show improved scannability; no information lost in re-styling. (pointer: memory/designer/goal7-typography-audit-2026-11-19.md)

4. **Icon System** - Create ui/icons.js with an inline SVG icon set (>=20 icons: agent, model, host, alert, success, warning, info, settings, search, refresh, download, upload, link, external, chevron-down/up/left/right, plus, minus, close, check, clock). All icons: 16x16 viewBox, currentColor fill, consistent stroke weight. Verified: all 20+ icons render correctly at 16/24/32px; used in >=3 panels each; no external icon library dependency.

5. **Typography Scale Refinement** - Audit and refine the type scale: ensure body text is 14-16px, headings follow a consistent ratio (1.25 or 1.333), line-height appropriate per size, monospace for code/paths. Fix any inconsistent sizing across panels. Verified: all font-size values in CSS are from the defined scale; no orphaned sizes; readability improved (line-length <75ch enforced). (pointer: memory/designer/goal7-typography-audit-2026-11-19.md)

6. **Responsive Design Hardening** - Test and fix all portal panels at 320px, 768px, 1024px, 1440px widths. Ensure: no horizontal scroll, touch targets >=44x44px on mobile, content reflows logically (not just shrinks). Verified: CDP screenshots at all 4 breakpoints show no overflow; touch targets pass; layout is usable at each width.

7. **Color Contrast + Accessibility** - Audit all text/background pairs for WCAG 2.1 AA contrast (>=4.5:1 body, >=3:1 large text). Fix failures by adjusting token values (not per-component overrides). Verified: automated contrast check passes for all visible text; no new issues introduced; dark mode also passes AA. (pointer: memory/designer/contrast_audit.py)

8. **Notification/Toast Design** - Design and implement a toast notification system: success (green), error (red), warning (amber), info (blue). Auto-dismiss after 5s, stackable (max 3 visible), dismissible by click. Used for: model load complete, goal verified, connection lost/restored, form errors. Verified: >=4 toast types implemented; stacking works; auto-dismiss timer correct; used in >=3 real scenarios in portal.

9. **Empty States + Loading Patterns** - Design and implement consistent empty states (icon + message + CTA) for all panels that can have no data, and loading skeletons (shimmer effect) for async content. Verified: all 8+ data panels have proper empty states; skeleton shows during >=500ms loads; no "undefined" or blank white space in any state.

10. **Design QA Checklist + Regression** - Create memory/designer/design-qa-checklist.md (visual, interaction, responsive, accessibility). `python memory/designer/design_qa.py` runs automated checks: contrast ratios, touch targets, font scale compliance, icon consistency. Verified: checklist has >=20 items; script automates >=10 of them; a deliberately broken panel is flagged; clean portal passes all checks. (pointer: memory/designer/regression-measurement-r69-2026-11-14.md)
