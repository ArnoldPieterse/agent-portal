# Goal 7 (Typography Hierarchy Audit) — findings + restated acceptance
Date: 2026-11-19 · Owner: Designer · Status: OPEN (design decision needed, not a mechanical fix)

## What I did this pass
1. Fixed a crash in `memory/designer/goal7-type-audit.py`: `int(val_px)` threw on float px
   values (`11.5`). Now parses via `float()`. Script runs clean.
2. Ran the static font-size audit against live `ui/*.css` + `ui/*.js`.

## Measurement (strict 5-step gate {12,14,15,18,24})
**60 violations.** Every one is an off-scale *micro-size*, not a structural heading error:
- tokens.css defines `--fs-11..--fs-16` (11,12,13,14,15,16) → 11/13/16 flagged off the literal set.
- app.css: literals 9/10/10.5/11/11.5/13/16/22 across ~45 lines (captions, labels, badges).
- core.js / uploads.js / fleet_status.js / components.js: injected `font-size` of 10/11 (chart labels, meta).

## Why I am NOT force-collapsing all 60 into {12,14,15,18,24}
The literal "5-step scale" is too coarse for a data-dense ops dashboard and **directly conflicts with goal #2**
(information density). Real design systems (GitHub Primer, Linear, Radix) ship micro-scales: 9–11px for
labels/captions/badges is the *correct* choice, not a bug. Collapsing them to 12px minimum would:
- increase vertical whitespace (reverses goal #2's ~20% reduction),
- make dense tables/queues less scannable.
So "0 violations of {12,14,15,18,24}" is the wrong acceptance for this product.

## Restated acceptance (proposed — needs Orchestrator sign-off to reword goal line)
> Every `font-size` in the UI resolves to a **defined `--fs-*` token** (single source of truth); the
> token set is the documented scale. Grep gate: `font-size\s*:\s*[\d.]+px` outside tokens.css = 0.

This is achievable + statically verifiable without touching readability, and it's the honest version
of "consistent type scale." Concretely:
1. Tokenize remaining literals in app.css/core.js/uploads.js/fleet_status.js/components.js into new
   `--fs-9/--fs-10/--fs-10-5/--fs-11-5/--fs-22` tokens (add to tokens.css).
2. components.js L122 dynamic size: confirm it snaps via `nearestScale()` (audit already flags this).
3. Re-run audit with ALLOWED = the token set → expect 0.

## Hand-off
- To **Orchestrator**: reword goal #7 acceptance to the token-resolution form above (or keep the strict
  gate and accept the density tradeoff — my recommendation is the former).
- Remaining work (tokenize + re-audit) is a ~30-min mechanical pass once the acceptance is settled;
  I have not started it this pass to avoid scope creep on an unresolved definition.

Evidence: `python memory/designer/goal7-type-audit.py` → exit 1, 60 violations (measurement above).