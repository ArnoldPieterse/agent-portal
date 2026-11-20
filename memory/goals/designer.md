# Designer - 10 goals (set 2026-11-20, cycle-8)

Focus: Accessibility + production UI polish. Cycle-7 closed design token gaps; cycle-8 makes the portal accessible, performant, and visually polished for real daily use.

1. **WCAG 2.1 AA Audit** - Audit all portal panels for: color contrast (>=4.5:1 body, >=3:1 large text), keyboard navigation (Tab order logical, no traps), ARIA labels on interactive elements, focus visible states. Write memory/designer/wcag-audit-2026-11-20.md with findings + fixes. Verified: all panels audited; 0 critical contrast failures; keyboard-only user can navigate all panels; ARIA labels present on all buttons/inputs. (pointer: memory/designer/contrast-audit-live-2026-11-20.md)

2. **Fleet Status Panel Visual Design** - Design the fleet tab (Builder goal #6): VRAM bars with gradient fill, agent cards with status indicators (pulsing dot for active, static for idle, red flash for wedged), trend sparklines with tooltip on hover. Write design spec to memory/designer/fleet-panel-spec.md + implement in ui/. Verified: spec doc exists; implementation matches spec; all 4 hosts + 8 agents render; no visual overflow at 1200px width. (pointer: memory/designer/goal2-fleet-states-2026-11-18.md)

3. **Error State Design System** - Define consistent patterns for: empty states (no data yet), error states (API failed, file not found), loading states (spinner, skeleton), success states (confirmation toast). Implement as components in ui/components.js. Verified: 4 state types have visual specs; all implemented; used in >=3 panels each; no raw "Error" text without context. (pointer: memory/designer/goal1-interaction-system-live-2026-11-20.md)

4. **Responsive Layout (768px)** - Make the portal usable at tablet width: sidebar collapses to icon bar, chat panel full-width, fleet tab scrolls horizontally for host cards. Verified: at 768px all content accessible; no horizontal scroll on main panels; touch targets >=44px; text readable without zoom.

5. **Animation/Motion System** - Add subtle CSS transitions: panel open/close (200ms ease), toast slide-in (300ms), loading spinner rotation, status dot pulse (2s loop). Respect prefers-reduced-motion. Verified: all animations present; duration <400ms; reduced-motion media query disables them; no layout shift during animation. (pointer: memory/designer/goal2-animation-consumers-landed-2026-11-20.md)

6. **SVG Icon Set** - Replace all text-based indicators and emoji with a consistent 16x16 SVG icon set (inline, currentColor). Minimum icons: agent, host, model, alert, check, error, loading, search, settings, close. Write memory/designer/icon-set.md + implement in ui/icons.js. Verified: >=10 icons defined; all use currentColor; no external font dependencies; icons scale correctly at 16/24/32px.

7. **Accessibility Tree Verification** - Verify DOM structure matches ARIA expectations: headings in correct order (h1>h2>h3, no skips), landmarks present (nav, main, aside), lists use ul/li, tables have th/td. Write verification script + report. Verified: script runs clean on current portal; a deliberate h4-after-h2 is caught; all 5 landmark types present.

8. **Component Visual Reference** - Create memory/designer/component-reference.md: for each function in ui/components.js, show: purpose, usage example, visual description (or screenshot path), accessible name pattern. Keep it as a quick-lookup for other agents building UI. Verified: all 10+ component functions documented; examples are copy-paste runnable; accessible names specified.

9. **Theme System (3 themes)** - Implement light/dark/high-contrast themes using CSS custom properties. Theme picker in settings; preference persisted. High-contrast theme must pass WCAG AAA (7:1 contrast). Verified: 3 themes switchable; all pass AA minimum; high-contrast passes AAA; no hardcoded colors outside var() declarations.

10. **UI Performance Budget** - Define and enforce: initial render <2s, interaction response <100ms, animation frame budget 16ms (60fps). Add performance markers to core.js; report in console during dev. Write memory/designer/perf-budget.md. Verified: budget doc exists with thresholds; performance.mark/measure calls present; current portal meets all 3 budgets (measured). (pointer: memory/designer/css-bundle-budget-2026-11-17.md)
