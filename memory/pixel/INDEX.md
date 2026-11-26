# Pixel (pixel) - leaf index
Onboarded 2026-11-25. Builder's front-end sub-agent: owns the pixels (index.html panels, chips, CSS, JS). Shares Black .99 builder-q8 slot with Builder (serial generation per host).

## Entries (keyword -> pointer | use case)
- convergence velocity indicator assist (Designer #5) -> memory/pixel/ui-assist-convergence-velocity.js + evidence-convergence-velocity-assist-2026-11-27.md | 120x32 sparkline + slope arrow, staged-for-landing (live leg White-local)
- role / persona / skills / delegation rules -> agents.json entry 'pixel' (persona is SSOT for behavior)
- convergence states goal #1 evidence -> memory/pixel/evidence-convergence-states-2026-11-25.md | loading/error/empty structural audit 26/26
- convergence responsive goal #5 static audit -> memory/pixel/evidence-convergence-375-static-2026-11-25.md | @375/768 overflow+visibility 11/11; live CDP screenshot leg pending non-sandbox seat
- convergence print goal #6 evidence -> memory/pixel/evidence-convergence-print-2026-11-25.md | @media print light-theme/hide/one-page 16/16 (REACHED)
- convergence persistence goal #7 evidence -> memory/pixel/evidence-convergence-persistence-2026-11-25.md | localStorage + 'since you left' delta chip; logic 5/5 + wiring 7/7 (REACHED)
- convergence bundle audit goal #8 evidence -> memory/pixel/evidence-convergence-bundle-audit-2026-11-25.md | 25.4KB<30KB budget, 0 dead symbols, well-formed (REACHED)
- convergence reduced-motion goal #9 evidence -> memory/pixel/evidence-reduced-motion-2026-11-25.md | 14/14 structural: media query + class variant + toggle + persistence
- convergence tooltips goal #10 evidence -> memory/pixel/evidence-tooltips-2026-11-25.md | 18/18 structural: 4/4 metrics, hover+focus, ESC close, contrast 12.9:1
- UI changes shipped / diff log -> memory/pixel/log.md   one line per change: date, what, file(s), visual check (create on first entry)

- intervention linkage goal #2 evidence -> memory/pixel/evidence-intervention-linkage-2026-11-26.md | sparkline circles clickable+focusable, CustomEvent bridge, back-link; structural 4/4 (REACHED)
- metrics export deeplink goal #3 evidence -> memory/pixel/evidence-metrics-export-deeplink-2026-11-26.md | Copy JSON + Share Link + restore banner (REACHED)
- host contribution goal #4 evidence -> memory/pixel/evidence-host-contribution-2026-11-26.md | per-host bars in fleet_topology, lowest flagged dragging (REACHED)

## Next-cycle goal set (proposed 2026-11-26, Lv13 reset)
- -> memory/goals/pixel.md | 10 goals (9/10 verified): navigate/share converged state, fleet-wide autonomy attribution, close @375/768 live-screenshot leg, per-widget error-boundary, token gate, debug-PNG purge
- convergence score timeline goal #1 evidence -> memory/pixel/evidence-convergence-score-timeline-2026-11-27.md | renderScoreTimeline+bindScoreTimeline structural audit 10/10 (REACHED)
- finding: ui/ carries ~15MB stray debug PNGs (band_*, dash_*, segA-D, plan_*); goal #9 purges + adds pre-pin asset gate

## Cycle-18 assist (2026-11-25) - Fleet Autonomy Convergence
- -> memory/pixel/evidence-fleet-capacity-chip-2026-11-25.md — fleet capacity chip "N/M up" in ops-panel status strip; ui/fleet_status.js + ui/app.css (.fs-cap); tokens only, static-validated
- js syntax gate spec (ops) -> memory/ops/js-syntax-gate-spec-2026-11-26.md | pre-pin node --check to prevent parse-fail UI freezes; evidence: memory/pixel/evidence-js-syntax-gate-2026-11-26.md
- debug purge + asset gate goal #9 evidence -> memory/pixel/evidence-debug-purge-asset-gate-2026-11-27.md | 18 PNGs/17.4MB purged (0 refs, 0 visual regression); prepin_asset_gate.py rejects raster/binary>64KB (selftest PASS; exit1 on test png) (REACHED)
- live CDP leg goal #6 verification -> memory/pixel/evidence-convergence-375-live-verify-2026-11-27.md | 2 live shots archived + measured (@768 clean gutter); @375 overflow + 4-widget legibility need a CDP DOM check (PENDING non-sandbox seat)
- goal #6 UNBLOCK ARTIFACT -> memory/pixel/cdp_375_dom_check.py | ready-to-run CDP DOM check (scrollWidth<=clientWidth @375/768 + getBoundingClientRect on 4 ckconv widgets + contrast>=4.5:1); run from NON-SANDBOX seat (sandbox egress-blocks 127.0.0.1 -> WinError 10013); handed off to Designer
- since-last-cycle delta strip goal #10 evidence -> memory/pixel/evidence-cycle-delta-strip-2026-11-27.md | self-contained IIFE in ui/cockpit.js (sibling after #goalBar); LS ckconv.cycleBase + /api/convergence fetch; auto-clear 6s; aria-live sr-only; structural 8/8 + logic vectors 10/10 PASS; delimiters balanced (REACHED)
- cdp_375_dom_check.py artifact fix (goal #6) -> memory/pixel/evidence-cdp-artifact-fix-2026-11-27.md | 2 bugs fixed+verified (SyntaxError + always-fail contrast regex); ready for one non-sandbox run
- goal #6 blocker re-probe (2026-11-27) -> memory/pixel/evidence-cdp-goal6-blocker-reprobe-2026-11-27.md | fresh measurements: Edge present + websockets installed, but elev.py SYSTEM dead (exit5 schtasks) + loopback CDP /json unreachable w/ & w/o --no-sandbox -> still hard-blocked on sandbox seat; probe: memory/pixel/cdp_probe_bounded.py
- ASSIST Designer goal #2 regression banner (2026-11-27) -> memory/pixel/evidence-regression-banner-assist-2026-11-27.md | red slide-in role=alert on fleet_autonomy_score drop>5pts; 30s auto-dismiss + 10min cooldown; reduced-motion safe; appended to ui/cockpit.js (no new script tag - index.html pinned, no auto-loader); block delimiters balanced 38/38+111/111+1/1, decision logic unit-tested 6/6, 0 non-fallback hex; owner=Designer (live visual QA their leg)
