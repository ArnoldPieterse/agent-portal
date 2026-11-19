# Designer goals #2/#5/#10 — closure booked 2026-11-19 (auto-loop)
parent: memory/goals/designer.md (#2, #5, #10)

## Why this pass
Ledger showed designer 7/10 with #2/#5/#10 open, but the browser acceptance that
closed them had ALREADY run on the White seat (headless Edge, host has :8099 access —
sandbox egress wall does not apply to it). The artifacts were on disk; only the
ledger record was missing.

## Verification done this pass (artifact integrity)
- memory/designer/density_before.png / density_after.png: valid PNG 1280x900 (matches doc claim, same viewport).
- memory/designer/notify.png: valid PNG 1280x900.
- memory/designer/print_report.pdf: valid PDF-1.4, 425,521 bytes — EXACT byte match with the acceptance doc's stated size (strong consistency signal).
- browser_evidence_summary.json shows an earlier stage (PNGs MISSING, pdf bytes 0) — superseded by the later successful captures; not contradictory.

## Acceptance vs evidence (per memory/designer/acceptance-2-5-9-10-2026-11-19.md)
- #2: live panel scrollHeight before/after fleetBody 227->142 (-37.4%), goalsBody -31.1%, filesList -48.4% vs -20% target; no clipping (intended scroll containers).
- #5: 3 toasts rendered top-right, bell badge "3", panel 3 items; 4/4 triggers wired live.
- #10: --print-to-pdf produced clean 3-page PDF from live portal; @media print block + Print button present in current ui/app.css / ui/core.js (re-checked this pass: both still present locally).

## Action
gl_ledger --record designer 2/5/10 with note+leaf => ledger now designer 10/10, fleet 93/93.
