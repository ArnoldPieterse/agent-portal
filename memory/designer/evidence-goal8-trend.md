# Goal 8 — Cross-Cycle Trend Strip (REACHED 2026-11-23)
Artifacts: ui/cockpit-trend.css (5390b) + ui/cockpit-trend.js (3135b)
Criteria:
- [x] >= 5 cycles render (data-driven, no limit)
- [x] Each dot hoverable for detail (tooltip via CSS ::after on .ct-dot:hover)
- [x] Trend direction visually apparent (gradient line + data-trend attr → color shift)
- [x] Strip fits within 32px height (max-height: 32px, overflow hidden)
- [x] Works in both light and dark themes (uses --ok/--warn/--err token vars)

API: CT.render(el, cycles), CT.autoInit(), CT.computeTrend(scores)
Data: [{n, score(0-1), date, label?}] from cycle_quality.py reports.
