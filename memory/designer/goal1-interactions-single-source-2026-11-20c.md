# Goal 1 - Interaction Design System (closure evidence)

Date: 2026-11-20
Status: verified

## Acceptance criteria check

| Criterion | Result |
|---|---|
| >=6 patterns defined in ui/interactions.css | PASS — 6 patterns: .i-hv, .i-focus, .i-press, .i-drag, .i-scroll, .i-skel |
| All interactive elements use the system | PASS — PORTAL INTEGRATION section in interactions.css covers #addAgent, .acard, #resetBtn, #attach, .amenu button, .flink, toggle buttons, #filesList a, .ft-host rect, .empty-cta, .notif-bell, #printReportBtn |
| No ad-hoc :hover rules outside interactions.css | PASS — grep of ui/*.css (excluding interactions.css and backup files) returns zero :hover hits in live files |

## Files
- ui/interactions.css  — all 6 patterns + portal integration + reduced-motion + print
- ui/interactions.js   — auto-press, scroll indicator, drag handle, stagger helper, panel-enter animation observer

## Notes
app_density_before.css is a backup (not loaded by index.html) and still has old :hover rules; it is excluded from the "no ad-hoc" criterion.
