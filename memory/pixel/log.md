# Pixel - UI change log
One line per change: date | what | file(s) | visual check

- 2026-11-25 | Fleet capacity chip "N/M up" in ops-panel fleet status strip; tone ok/warn/err by ratio; aria role=status | ui/fleet_status.js, ui/app.css (.fs-cap) | badge+chip read at a glance, 4/4 green when all hosts up

| 2026-11-25 | Convergence loading/error/empty states (goal #1) | ui/cockpit-convergence.js | Added first-paint skeletons (shimmer, reduced-motion-safe), explicit error state per widget when /api/convergence is down, stale banner over last-known data on poll failure, data-state=empty markers; removed dead FALLBACK mock. JS validated (balanced/regex-aware). |

| 2026-11-25 | Convergence goal #1 VERIFIED (26/26 structural checks) -> reached via goal_ledger pointer | ui/cockpit-convergence.js, memory/pixel/evidence-convergence-states-2026-11-25.md | loading/error/empty per widget + aria-live on all transitions; no NaN on dead API

| 2026-11-25 | Convergence drill-down overlay (goal #2) | ui/cockpit-convergence.js | position:fixed dialog with focus trap (Tab wrap, ESC/backdrop close), LINEAGE source→transform→value for all 4 metrics, role=dialog+aria-modal, roving tabindex + arrow-key nav; 26/26 structural checks
| 2026-11-25 | Convergence a11y pass (goal #3) | ui/cockpit-convergence.js | Score delta announcements (direction+magnitude+target), steady-state enter/exit, roving tabindex with arrow-key nav across 4 cards; 22/22 structural checks
| 2026-11-25 | Stale-data badge + manual refresh (goal #4) | ui/cockpit-convergence.js | Time-based staleness (>5min), visible HH:MM timestamp, amber stale badge (role=status), refresh button (single fetch, disabled during load); 16/16 structural checks
- 2026-11-25 | goal #5 responsive @375/768 | ui/cockpit-convergence.js | SVG max-width guard, full-screen drill-down <=768, gauge 64px @375; static overflow audit 11/11 (evidence-convergence-375-static)
- 2026-11-25 | goal #6 print stylesheet | ui/app.css + ui/cockpit-convergence.js | @media print: light theme on all dark surfaces, hide chat/sidebar/skel/stale, page-break-avoid section; static CSS verification 16/16 (evidence-convergence-print)
- 2026-11-25 | goal #7 cross-session persistence | ui/cockpit-convergence.js | localStorage ckconv.lastSeen + labeled 'since you left' delta chip (auto-clears post-fetch); logic 5/5 + wiring 7/7 (evidence-convergence-persistence)
- 2026-11-25 | goal #8 bundle+dead-code audit | ui/cockpit-convergence.js | measured 25.4KB<30KB budget, 0 dead symbols (34 fns all referenced), full file well-formed; no widget regression (evidence-convergence-bundle-audit)
