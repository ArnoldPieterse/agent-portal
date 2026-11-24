# Designer — Cycle 16 Goals (set 2026-11-24)
Round topic: **Fleet Autonomy Convergence**
Pillars: (1) Autonomous Cycle Transition, (2) Self-Validation Circuit, (3) Adaptive Topology

1. **Cycle-Complete Celebration State** - cockpit hero when goal_pct=100: animated checkmark + cycle number + "Transitioning..." progress bar. Verified: renders at 1440px; animation <60fps drop; no layout shift
2. **Seat Status Matrix Panel** - fleet tab: 8 agent cards (host, state color, last-seen). Click expands task+passes. Verified: all 8 render at 1440px; green/red/amber correct; expand no overflow (pointer: memory/designer/goal2-fleet-states-2026-11-18.md)
3. **Autonomy Score Gauge** - circular SVG gauge 0-100. Red<40, amber 40-70, green>70. Animate on change <500ms. Verified: 80px diameter; color thresholds correct at boundaries
4. **Goal Dependency DAG View** - SVG nodes=goals, edges=deps. Color by status. Pan/zoom. Verified: 10 nodes+8 edges no overlap at 1440px; pan works
5. **Mode Transition Toasts** - toast on mode change: icon+"Fleet entered X mode"+duration. Auto-dismiss 5s, stackable. Verified: Playwright confirms appear/dismiss; no overlap
6. **Productivity Sparklines** - 7-day sparkline per agent card (productive-pass rate). Green>60%, amber 30-60%, red<30%. Verified: all agents render; colors correct
7. **Cycle Countdown Timer** - IDLE mode: countdown to predicted next-cycle start from cycle-forecast.json. Update every min. Verified: counts down; at zero shows "Ready"
8. **Validation Status Badges** - goal cards: ✓/⚠/✗ badges with tooltip. Verified: all 3 states render; tooltip on hover; no overflow at 768px
9. **Fleet Health Summary Card** - top-of-cockpit: mode, seats X/8, autonomy score, cycle %. Single glance. Verified: fits 200px width; 4 metrics visible; 30s refresh (pointer: memory/designer/cockpit-load-audit-fleet-2026-11-24.json)
10. **Dark Mode + Reduced Motion Audit** - all new elements (1-9) work in dark mode AND prefers-reduced-motion. No anim for RM users; WCAG AA contrast both themes. Verified: Playwright dark+RM: no anim, contrast ≥4.5:1
