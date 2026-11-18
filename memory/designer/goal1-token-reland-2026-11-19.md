# Goal #1 (Design Token System) - re-land after regression + closure evidence
Date: 2026-11-19 | Owner: Designer | Status: CLOSED (acceptance test met, re-verified live)

## Context
The 2026-11-19 tokenization pass (goal1-token-system-2026-11-19.md) was valid at write time,
but ui/app.css on disk had since regressed to a pre-tokenization state: its own inline :root
with legacy spacing (--sp-8:8px etc.) + 6-step font scale, NO @import of tokens.css, and 54
hard-coded color literal lines. index.html (pinned) loads ONLY ui/app.css, so tokens.css was
dead on disk. This pass re-applied the tokenization to the live file and verified it end-to-end.

## Changes (this pass)
1. ui/app.css
   - Replaced duplicate :root block with `@import url('tokens.css');` (single source).
   - Migrated all 54 hard-coded color lines to tokens: semantic extensions already present in
     tokens.css (--esc-sel-bg, --msg-you-*, --dm-purple-*, --warn-badge-*, --seg-active-bg,
     --queue-*, --peek-*, --spinner-*, --busy-text, --action-text, --link/-hover/-dash,
     --ok/-warn bg+border alphas, --backdrop, --shadow-card/--tooltip, --ft-stroke, dots).
   - Replaced undefined-token refs: var(--bg2,#1e2a3a)->var(--toast-bg),
     var(--r-sm)->var(--br-sm), var(--fs-sm,12px)->var(--fs-12), var(--ok,#3ddc84)->var(--ok).
   - Tokenized all border-radius literals (8/12/6/5/10px -> --br-md/lg/ss/sm/lg2; 50% -> --br-full)
     and body line-height 1.45 -> var(--lh-base) (goal-2 density value now actually applies).
   - Value-preserving: every token maps to the exact literal it replaced (no color/size change),
     EXCEPT spacing/line-height which now resolve to tokens.css's tighter density values = goal 2 intent.
2. ui/tokens.css (additions only; existing definitions untouched)
   - New tokens for literals with no home: --toast-bg, --shadow-toast, --alert-badge-bg,
     --warn-toast-border (goal-5 toast chrome).
   - Legacy off-scale tokens so refs keep resolving while goal 7 cleans them up:
     --fs-11, --fs-13, --fs-16, --br-ss(6px), --br-lg2(10px) - commented as goal-7 cleanup.
3. memory/designer/token_lint.py (Builder's gate; credit: Builder)
   - Added `--tokens <path>` option: merges definitions from the imported tokens.css into C2,
     so the gate is correct under the @import architecture (previously false-flagged all 68 refs
     as undefined because it only scanned the target file for :root scopes).

## Verification (ran this pass, deterministic)
- `grep '#[0-9a-fA-F]{3,8}' ui/app.css` -> **0 hits** (acceptance test clause 1 MET).
- var() audit: 68 distinct tokens referenced in app.css, ALL defined in tokens.css :root
  -> **0 dangling**, 0 fallback-style refs remaining (clause 2 MET).
- token_lint.py ui/app.css --tokens ui/tokens.css: C1=0, C2=0, RESULT flag OK for scope check.
  Remaining C3 off-scale font-size = 9 (18/22/11.5/10.5/10px in FleetTopology + 2 chrome spots)
  -> goal #7 territory, NOT a goal-1 failure; linter exit=1 is expected until goal 7 lands.
- JSON: memory/designer/token-lint-reland-2026-11-19.json

## Follow-ups (documented, not blockers for closure)
- Goal 7: migrate the 9 off-scale font sizes + delete legacy --fs-11/13/16 tokens when done.
- Layout flag for Verifier: FleetTopology merge block (app.css L234+) re-declares
  `body{padding:20px}` and bare `h1/code/.sub` rules that cascade into the portal shell
  (body gains 20px inset). Pre-existing since 2026-11-17 merge; needs a visual check before
  anyone "fixes" it - may be load-bearing for the standalone topology demo page.

## Repro
    python memory/designer/token_lint.py ui/app.css --tokens ui/tokens.css --json out.json
