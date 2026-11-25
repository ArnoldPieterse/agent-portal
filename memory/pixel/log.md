# Pixel - UI change log
One line per change: date | what | file(s) | visual check

- 2026-11-25 | Fleet capacity chip "N/M up" in ops-panel fleet status strip; tone ok/warn/err by ratio; aria role=status | ui/fleet_status.js, ui/app.css (.fs-cap) | badge+chip read at a glance, 4/4 green when all hosts up

| 2026-11-25 | Convergence loading/error/empty states (goal #1) | ui/cockpit-convergence.js | Added first-paint skeletons (shimmer, reduced-motion-safe), explicit error state per widget when /api/convergence is down, stale banner over last-known data on poll failure, data-state=empty markers; removed dead FALLBACK mock. JS validated (balanced/regex-aware). |
