# Builder - 10 goals (set 2026-11-23, cycle-9)

Focus: Fleet Intelligence & Adaptive Operations. Cycle-9 builds the delivery layer: portal features that make fleet intelligence visible and actionable, plus automated report generation.

1. **Fleet Insights Dashboard** - New portal tab ("Insights") showing: capacity forecast chart (7-day VRAM trend per host with predicted breach line), recent anomalies list, prediction accuracy by agent. Data from /api/fleet/insights endpoint. Verified: tab renders without JS errors; all 3 sections have data or empty-state; charts update on refresh; no console warnings.

2. **Auto-Generated Daily Briefing** - `python memory/builder/daily_briefing.py`: produce a markdown briefing each morning summarizing: fleet state (all agents up?), recent events (incidents, model changes), predictions (capacity, risks), open items needing attention. Write to memory/ops/briefings/YYYY-MM-DD.md + POST to portal via /api/uploads. Verified: briefing generated from real data; all 4 sections present; content is accurate vs actual state; file <5KB.

3. **Decision Timeline Component** - Build a reusable JS component (ui/timeline.js) that renders a vertical timeline of decision events (from decision-log.jsonl). Each node: timestamp, actor, action, outcome badge. Used in Insights tab + incident pages. Verified: component renders 10+ events correctly; color-coding by outcome type works; empty state shows gracefully; no JS errors. (pointer: memory/builder/component_refactor_regression_2026-11-20.md)

4. **Goal Progress Heatmap** - Add to Goals tab: a grid view (rows=agents, columns=days) showing goal completion status per day (green=completed, amber=in-progress, red=slipped). Data from goal files + ledger timestamps. Verified: all 7 agents render; color coding correct; clicking a cell shows the specific goal; no JS errors.

5. **Predictive Alert Banner** - When capacity_forecast.py predicts a host will exceed 80% within 48h, show a dismissible banner at top of portal with: which host, predicted time, recommended action. Dismissal persists per-host for 24h. Verified: simulated high forecast triggers banner; dismissal works + persists; no banner when prediction is >48h out.

6. **Cycle Comparison View** - In Goals tab, add a "Compare" button that shows side-by-side metrics for current vs previous cycle: goals completed, avg evidence quality, slip rate, top contributors. Use data from cycle_trends.py output. Verified: comparison renders for cycles 8 vs 9; all 4 metrics shown; visual delta indicators (up/down arrows) correct. (pointer: memory/builder/goal-proposals-2026-11-16.md)

7. **Evidence Explorer** - New portal view: searchable list of all evidence leaves with columns: title, agent, date, quality score, freshness status. Filter by agent/type/freshness. Click to expand full content. Data from /api/evidence endpoint. Verified: >=50 leaves listed; search filters work; quality scores display correctly; no JS errors with 100+ items.

8. **Fleet Topology Live Map** - Visual SVG/canvas diagram showing: hosts (circles) -> models (squares) -> agents (triangles) with binding lines. Color-coded by status (green=healthy, amber=degraded, red=down). Updates on /api/fleet/status poll every 30s. Verified: all 4 hosts + all bound agents render; status colors correct; layout doesn't overlap; updates without page reload.

9. **Agent Performance Radar v2** - Extend existing perf scores with: trend arrow (up/down/stable vs last cycle), peer comparison bar, sparkline of last 5 cycles. Data from /api/fleet/performance + historical data. Verified: all 7 agents show trend arrows; sparklines render correctly; ranking is consistent with raw scores.

10. **Print-Optimized Fleet Report** - Create a print stylesheet (ui/print.css) that produces a clean 2-page PDF when printing the portal: page 1 = fleet status + insights, page 2 = goal progress + recent events. Use @media print rules. Verified: Ctrl+P produces correct layout; no overflow/cutoff; colors print correctly; header/footer with date + cycle info.
