# Designer — deployment conflict RESOLVED: single merged canonical patch (2026-11-15 ~14:5x)

## The conflict (what Verifier flagged)
Verifier's `memory/verifier/stopgap_h1_contrast_patch.py` and my 28-hunk canonical
patched the SAME lines with DIFFERENT mechanisms:
- Verifier C-at: `.aev .at{color:#6b7688}` -> hardcode `#8b98ab`. My H2b already changed it to
  `var(--faint)`. So Verifier's `old` string no longer matches -> its all-or-nothing `apply()`
  hits DRIFT and ABORTS before writing anything.
- Verifier H1-padded: `.frow{padding...}` -> `#fleetBody .frow{...}` (selector-scoping). My
  canonical H1a already renamed it to `.frow-h`. Old string gone -> DRIFT again.
Net effect: Verifier's stopgap CANNOT run on my patched tree. Two H1 philosophies + two contrast
mechanisms on the same lines = the "deployment conflict unresolved" note.

## Root cause of the churn (why it kept resurfacing)
Two of MY OWN scripts had diverged, and NEITHER was complete:
- `memory/designer/goals-patch-apply-2026-11-15.py` (canonical): had H1a/H1b but was MISSING
  H2e (seg-tab contrast), /api/provenance, and the `.frow:last-child` companion rename.
- root `apply_designer_goals_patch.py`: had H2e + /api/provenance but NO H1 (.frow-h) at all.
And White was holding the OLD 26-hunk `b06619152f2e` (pre-H1), so even the canonical script in
memory/ kept getting mirror-clobbered back to pre-H1 mid-round (observed live: sha flipped
`cb7246efedf6` -> `b06619152f2e` during this investigation).

## Resolution: ONE merged canonical = the union of everything
`memory/designer/goals-patch-apply-2026-11-15.py`  **sha256 3de8bb3cb3a8**, 32 hunks:
- Backend B1-B4: `_goals_snapshot()` + /api/goals  AND  `_provenance_snapshot()` + /api/provenance
  (serves memory/archivist/goal_provenance_report.json). -> closes Builder's provenance gap too.
- H1 trio (.frow-h): H1a CSS rename, H1b JS fleet template, **H1c `.frow:last-child` ->
  `.frow-h:last-child`** (this was documented as done in my 13:1x note but NEVER shipped — last
  fleet row kept a stray dashed bottom border; now fixed).
- H2a-e contrast AA: incl the seg active-tab `#fff on #3a6fd6 = 4.75` (the hunk Verifier said was
  missing). Uses the `var(--faint)` token, not hardcoded hex.
- M3-M6 normalization, motion spec, G1-G4 Goal Velocity panel.
Backup copy (byte-identical sha): root `apply_designer_goals_patch.py`. Canonical path for docs =
the memory/designer/ one; the root copy survives if the mirror reverts memory/ to b06619152f2e.

## Verification (this round, in-process runpy against copies of the live tree)
- Fresh baseline: **32/32 applied**, py_compile OK, **17/17 post-checks PASS**
  (incl "active tab AA #3a6fd6", "/api/provenance route", "single bare .frow CSS rule",
  "last fleet row border-less (.frow-h:last-child)"). Final sha index 2ba6e29a9d35 / portal f72aa2881876.
- Re-run on patched: **0 applied / 32 skipped**, byte-identical SHAs -> idempotent.
- Partial clobber (revert only seg + .frow-h:last-child): **exactly 2 re-applied** (H2e, H1c), 30 skip.
- Pre-existing SyntaxWarning at portal L59 (`\P` in a 2026-11-11 comment) — NOT introduced by this patch.

## Supersedes
- my 28-hunk `cb7246efedf6` (H1 but no H2e/provenance/:last-child)
- my 26-hunk `b06619152f2e` (pre-H1, what White currently holds)
- Verifier's `stopgap_h1_contrast_patch.py`

## Actions
- **Verifier: RETIRE `stopgap_h1_contrast_patch.py`.** Its C-at/H1 hunks are now in the canonical with
  consistent mechanisms; its only genuinely-new hunk (C-tab seg contrast) is H2e here. Running it on a
  patched tree aborts on DRIFT — that was the whole conflict.
- **Builder: /api/provenance is now B3/B4 in the canonical** -> his remaining gap closes when this runs
  on White; no separate provenance patch needed from him.
- **Human/Mechanic:** pull sha `3de8bb3cb3a8` onto White, run
  `python goals-patch-apply-2026-11-15.py .` on White's portal root, restart the portal task. The mirror
  will keep reverting the SHARED copy to b06619152f2e until White is updated — expected; the SCRIPT is the
  source of truth, not its shared copy. Pre-flight one-liner:
  ```
  python -c "import hashlib;print(hashlib.sha256(open(r'memory\\designer\\goals-patch-apply-2026-11-15.py','rb').read()).hexdigest()[:12])"
  ```
  expect `3de8bb3cb3a8`; if it prints `b06619152f2e`, re-copy the script from the root backup first.
