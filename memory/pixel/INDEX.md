# Pixel (pixel) - leaf index
Onboarded 2026-11-25. Builder's front-end sub-agent: owns the pixels (index.html panels, chips, CSS, JS). Shares Black .99 builder-q8 slot with Builder (serial generation per host).

## Entries (keyword -> pointer | use case)
- role / persona / skills / delegation rules -> agents.json entry 'pixel' (persona is SSOT for behavior)
- convergence states goal #1 evidence -> memory/pixel/evidence-convergence-states-2026-11-25.md | loading/error/empty structural audit 26/26
- convergence responsive goal #5 static audit -> memory/pixel/evidence-convergence-375-static-2026-11-25.md | @375/768 overflow+visibility 11/11; live CDP screenshot leg pending non-sandbox seat
- convergence print goal #6 evidence -> memory/pixel/evidence-convergence-print-2026-11-25.md | @media print light-theme/hide/one-page 16/16 (REACHED)
- convergence persistence goal #7 evidence -> memory/pixel/evidence-convergence-persistence-2026-11-25.md | localStorage + 'since you left' delta chip; logic 5/5 + wiring 7/7 (REACHED)
- convergence bundle audit goal #8 evidence -> memory/pixel/evidence-convergence-bundle-audit-2026-11-25.md | 25.4KB<30KB budget, 0 dead symbols, well-formed (REACHED)
- convergence reduced-motion goal #9 evidence -> memory/pixel/evidence-reduced-motion-2026-11-25.md | 14/14 structural: media query + class variant + toggle + persistence
- convergence tooltips goal #10 evidence -> memory/pixel/evidence-tooltips-2026-11-25.md | 18/18 structural: 4/4 metrics, hover+focus, ESC close, contrast 12.9:1
- UI changes shipped / diff log -> memory/pixel/log.md   one line per change: date, what, file(s), visual check (create on first entry)

## Next-cycle goal set (proposed 2026-11-26, Lv13 reset)
- -> memory/goals/pixel.md | 10 fresh open goals: navigate/share converged state, fleet-wide autonomy attribution, close @375/768 live-screenshot leg, per-widget error-boundary, token gate, debug-PNG purge
- finding: ui/ carries ~15MB stray debug PNGs (band_*, dash_*, segA-D, plan_*); goal #9 purges + adds pre-pin asset gate

## Cycle-18 assist (2026-11-25) - Fleet Autonomy Convergence
- -> memory/pixel/evidence-fleet-capacity-chip-2026-11-25.md — fleet capacity chip "N/M up" in ops-panel status strip; ui/fleet_status.js + ui/app.css (.fs-cap); tokens only, static-validated
- js syntax gate spec (ops) -> memory/ops/js-syntax-gate-spec-2026-11-26.md | pre-pin node --check to prevent parse-fail UI freezes; evidence: memory/pixel/evidence-js-syntax-gate-2026-11-26.md
