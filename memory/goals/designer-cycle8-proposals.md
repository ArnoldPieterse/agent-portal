# Designer — Cycle-8 Goal Proposals (2026-11-20)

Focus: From "polished" to "productive." Cycle-7 made the portal feel alive; cycle-8 makes it a tool you can rely on in production: fast, navigable, documented, and resilient.

1. **Performance Budget + Lighthouse Gate** — Define measurable budgets: CSS total <=15KB gzipped, JS execution <50ms TTI contribution, CLS <0.1, no layout shift on panel toggle. Create `memory/designer/perf_budget.md` with thresholds; extend `design_qa.py` to check bundle sizes and flag regressions. Verified: budget file exists with 4+ metrics; `design_qa.py` includes a `--perf` mode that reads current sizes and passes/fails against thresholds; a deliberately oversized CSS file triggers a FAIL.

2. **Command Palette (Ctrl+K)** — Implement a fuzzy-search command palette in ui/interactions.js: triggered by Ctrl+K or a keyboard shortcut, shows filtered list of actions (navigate to panel, toggle dark mode, refresh data, search goals). Max 8 results visible, keyboard-navigable (up/down + Enter), dismiss on Escape. Verified: palette opens/closes correctly; typing filters results; Enter executes the selected action; works without mouse.

3. **Keyboard-Only Navigation Audit** — Full audit: every interactive element reachable via Tab in logical order; focus-visible ring is high-contrast and consistent; skip-links jump to main content; no focus traps. Fix any gaps. Verified: `design_qa.py --keyboard` mode walks all tabbable elements, checks focus-visible styles exist, flags missing aria-labels on icon-only buttons; 0 critical issues in final run.

4. **Print Stylesheet** — Create a @media print block: hide navigation/controls, expand collapsible sections, use high-contrast black-on-white, add page numbers via CSS counters, ensure tables don't split mid-row. Verified: `design_qa.py --print` mode checks for @media print rules; CDP screenshot in print mode shows clean output; no interactive elements visible.

5. **Component Reference Page** — Build a self-documenting reference at ui/components.js + a fixture HTML (served via portal): every reusable component (card, badge, progress bar, toast, empty state, skeleton, gauge, icon) rendered with live examples, usage notes, and token dependencies. Verified: >=12 components documented; each shows 2+ variants; page renders standalone without API connection.

6. **Error Boundary + Graceful Degradation** — Design and implement error states for: API timeout (show cached data + "stale" badge), JS crash (catch-all shows friendly message + retry button), partial data load (show what loaded, flag missing sections). Verified: 3 distinct error patterns implemented; simulated network failure shows correct state; no white-screen on any failure mode.

7. **Data Viz: Sparklines + Trend Indicators** — Add lightweight inline sparklines (SVG, no library) for goal progress over time and model uptime trends. Each sparkline: 60x20px, last 7 data points, color-coded by status. Add trend arrows (up/down/flat) next to key metrics. Verified: >=4 sparklines in live portal; data updates on refresh; no external chart library dependency.

8. **Onboarding Tour (First-Run)** — Implement a lightweight guided tour (ui/tour.js already exists as stub): 5-6 steps highlighting key panels with tooltips, "Next/Skip" buttons, progress dots. Shown once per browser (localStorage flag), re-triggerable via settings. Verified: tour completes all steps; skipping persists state; tour content matches actual portal layout; accessible (screen-reader announces each step).

9. **Design Tokens Documentation + JSON Export** — Document the full token system in memory/designer/tokens-doc.md: every token's name, value, usage context, and relationships. Generate a machine-readable `tokens.json` export (script: `python memory/designer/export_tokens.py`) for use by other tools/agents. Verified: doc covers 100% of tokens in tokens.css; JSON is valid parseable output; script runs without errors.

10. **Cross-Panel Consistency Regression Suite** — Extend design_qa.py into a full regression suite that runs on every CSS/JS change: checks token usage consistency (no raw hex values outside tokens.css), interaction pattern compliance, responsive breakpoint coverage, icon set completeness. Gate: `python memory/designer/design_qa.py --full` exits 0 on clean portal, non-zero on violation. Verified: suite has >=15 individual checks; a deliberately broken CSS file fails at least one check; clean portal passes all.
