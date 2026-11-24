# Designer — Cycle 15 Goals (set 2026-11-24)
Round topic: **Fleet Autonomy Convergence**
Pillars: (1) Mode Controller, (2) Dispatch Correctness, (3) Idle Productivity

1. **Mode-Specific Cockpit Layout** - Design + implement (CSS/JS in ui/cockpit.js): in MAINTENANCE mode, panels re-prioritize — Health Score + Productivity Baseline move to top row; Goal Progress collapses to single summary bar. In IDLE mode, show "All goals reached" hero + next-cycle countdown timer. Verified: at 1440px, MAINTENANCE layout shows health+productivity first; IDLE shows hero centered; no overflow at 768px; transition between layouts is <300ms CSS animation. (pointer: memory/designer/evidence-cockpit-token-completion-2026-11-24.md)

2. **Fleet Mode ARIA + Keyboard Nav** - Add ARIA-live region for mode changes (screen reader announces "Fleet entered maintenance mode"); ensure all cockpit panels are keyboard-navigable in all three modes (Tab order logical, Enter/Space activates controls). Verified: Playwright test confirms aria-live="polite" fires on mode change; Tab through all 6+ panels without mouse in each mode; no focus traps; WCAG 2.1 AA contrast ratios met.
   [REACHED 2026-11-24] (pointer: memory/designer/ui_a11y_test.py)

3. **Mode Transition Animation** - Design CSS transition for mode changes: background color shift (green->amber->grey) over 400ms with ease-in-out; panel reordering uses FLIP animation (not instant jump). Verify no layout thrashing (getBoundingClientRect calls <5 during transition). Verified: at 1440px, transition is smooth (no jank in Performance tab); reduced-motion media query respected (instant switch for prefers-reduced-motion users).
   [REACHED 2026-11-24] (pointer: memory/designer/evidence-mode-transition-animation-2026-11-24.md)

4. **Idle Hero State Design** - Design the IDLE-mode hero: centered "All goals reached ✓" with cycle number, time-in-IDLE counter (live updating), and "Next cycle begins when new goals are set" subtitle. Include subtle pulse animation on the checkmark. Verified: hero is centered at 1440px and 768px; counter updates every second; pulse animation respects prefers-reduced-motion; text is readable at 16px minimum. (pointer: memory/designer/acceptance-2-5-9-10-2026-11-19.md)

5. **Productivity Sparkline Panel** - Design + implement per-agent mini sparklines (SVG, 7-day window) showing productive-pass rate. Color: green >70%, amber 30-70%, red <30%. Tooltip on hover shows exact count. Verified: 8 sparklines render at 1440px without overflow; at 768px they collapse to a horizontal scroll row; tooltip appears within 200ms of hover; data updates on 30s refresh. (pointer: memory/designer/ops-panel-hierarchy-evidence-2026-11-15b.md)

6. **Pass Budget Gauge** - Design a circular gauge (SVG) showing passes used / budget remaining this cycle. Color transitions: green <50%, amber 50-80%, red >80%. Show numeric "142/200" in center. Animate fill on value change. Verified: gauge renders correctly at all budget levels; color thresholds trigger at exact percentages; animation is <300ms; accessible (aria-valuenow updates).
   [REACHED 2026-11-24] (pointer: memory/designer/evidence-pass-budget-gauge-2026-11-24.md)

7. **Mode History Timeline** - Design horizontal timeline showing when fleet entered/exited each mode today (colored segments with timestamps). Max 24h window, scrollable if needed. Current mode highlighted with glow. Verified: timeline renders correctly with 3+ transitions; at 768px, compresses to icon-only view; current-mode segment has visible glow; timeline updates on new transition without full re-render.
   [REACHED 2026-11-24] (pointer: memory/designer/evidence-mode-history-timeline-2026-11-24.md)

8. **Maintenance Task Cards** - Design card component for each idle agent showing: agent name, current maintenance task (from rotation), time assigned, productive status (✓/✗). Grid layout: 4 cards per row at 1440px, 2 per row at 768px. Verified: 8 cards render in correct grid; card content truncates gracefully for long task text; productive status updates on data refresh; no overflow at any breakpoint.
   [REACHED 2026-11-24] (pointer: memory/designer/evidence-maintenance-task-cards-2026-11-24.md)

9. **Convergence Progress Ring** - Replace linear progress bar with circular ring showing % of cycle goals reached. Animate stroke-dashoffset on value change. Show "22/80 (27.5%)" in center. Color: blue during WORK, grey when complete. Verified: ring animates smoothly from 0->100% over 1s; at 768px, ring scales down proportionally; text remains readable at smallest size; aria-valuenow tracks percentage.
   [REACHED 2026-11-24] (pointer: memory/designer/evidence-convergence-ring-2026-11-24.json)

10. **Accessibility Audit (All 3 Modes)** - Run full WCAG 2.1 AA audit on cockpit in WORK, MAINTENANCE, and IDLE modes: contrast ratios, focus order, ARIA labels, keyboard operability, screen reader announcements, reduced-motion compliance. Write report to memory/designer/a11y-audit-cycle15.md with pass/fail per criterion. Verified: report covers all 3 modes; any fail has specific element + fix recommendation; Playwright axe-scan confirms 0 critical violations in each mode. (pointer: memory/designer/cockpit-load-audit-fleet-2026-11-24.json)
