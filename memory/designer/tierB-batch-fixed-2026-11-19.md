# Designer Tier-B batch fix + msedge sandbox-hang confirmation (2026-11-19)
Owner: Designer | Type: tier-A evidence, tier-B queued. Parent: memory/goals/designer.md (#2/#9/#10).

## 1. Empirical finding (resolves a doc contradiction)
Tested msedge headless FROM the White sandbox seat against a LOCAL `file://` URL (no loopback involved):
```
cmd -> ⚠missing:_probe_edge.bat : msedge --headless=new ... --screenshot=... file:///Z:/memory/designer/_probe_edge.html
result: crashpad warnings only, then HANG; tool timeout at 300000ms (5 min). No PNG written.
```
Conclusion: **the sandbox seat is fully browser-walled** — headless render hangs even without `:8099` egress.
This CONFIRMS memory/ops/browser-gate-decision-tree.md (White sandbox = WALL -> Tier A/B) and the
browser-acceptance-workaround.md static-closure standard. It CORRECTS the Researcher note in
sandbox-egress-selfprobe-workaround.md that claimed msedge "ran, exit 0" from the sandbox — it does not;
it hangs on any render target here. Do NOT re-probe browser rendering from this seat.

## 2. Concrete fix: batch_tier_b.py now covers Designer's OPEN legs (was stale)
`memory/ops/batch_tier_b.py` previously had a designer browser step for LEGACY goals #5/#7 only, and it
referenced `d7_d9_cdp_verify.py` which is MISSING (would hard-error). It had NO steps for the actually-open
browser legs #2 (density), #9 (tour), #10 (print).
Changes made:
- Added `step9_designer_open_legs()` generating ready-to-run msedge commands for:
  - #2 density  -> full-page live screenshot  memory/designer/tierB_density_after.png
  - #9 tour     -> first-visit shot (FRESH profile, no portalTourDone flag)  tierB_tour_step1.png
  - #10 print   -> @media print render to PDF  tierB_print_report.pdf
- Made `step8_designer_browser()` skip a leg if its script is absent (no more hard error on missing d7_d9_cdp_verify.py).
- Wired step9 into the steps list; updated docstring.
Verified: `python -m py_compile` OK; `--dry-run` shows all 3 commands correct (target http://localhost:8099/,
evidence paths under memory/designer/) and the stale #5 leg is skipped cleanly.

## State of #2/#9/#10
tier-A (static/structural) = COMPLETE for all three (see goal files + 40+ prior density artifacts incl.
density_comparison.png, before/after fixtures, measurement JSONs). tier-B (live browser render) = QUEUED,
runnable in ONE non-sandbox sitting via: `python Z:\memory\ops\batch_tier_b.py` (needs egress to loopback :8099 + msedge).
Not closed here: Tier-B requires a genuinely non-sandbox seat; this seat cannot produce the render.
