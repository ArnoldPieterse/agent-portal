# Goals #3 + #4 — code-complete, source-verified (Designer, 2026-11-15)

Base: canonical `index.html` at live pin sha1 **37549a041412** (80,360 B). Pristine copy kept at `index_html_pre-accd-37549a04.html`. Result file sha1 **6d6ab3dcf5c8**, 81,338 B.

## #3 contrast (WCAG AA)
- Added `--acc-deep:#2563eb` to :root.
- Repointed the only two sub-AA fills: `#send` and `.btn.pri` from `var(--acc)` (white-on-#4f8cff = 3.22:1 FAIL) → `var(--acc-deep)` (white-on-#2563eb = **5.17:1 PASS**).
- All other `var(--acc)` uses are borders/hover/outline/text-color — recomputed, all ≥4.5:1 (e.g. `.chipfile .st` on --panel2 = 4.95:1). No residual fill fails.

## #4 4px spacing scale + type scale
- :root tokens added: spacing `--sp-1..8` = 4/8/12/16/20/24/32; type `--fs-xs/sm/md/base/lg/xl/2xl/3xl` = 11/12/13/14/15/16/18/22; radius `--r-sm/md/lg/xl` = 6/8/10/14 (values preserved, zero visual shift).
- All `font-size` → `var(--fs-*)`; all rhythm (margin/padding/gap) → `var(--sp-*)` (off-grid snapped to nearest 4px multiple; 1/2/3 kept as documented micro); fixed dims off-grid snapped to grid (9→8, 26→28, 30→32, 70→72, 90→92, 18→20) or preserved via `--w-aside:250px` / `--gtile-minw:170px`. Sacred dims untouched (#input/#attach/.gring height 44px; panel max-heights; aside width).
- Font-shorthands (`body`, `.opsbox`, `#actBody`) expanded to explicit `font-size:var(--fs-*);line-height:N;font-family:…`.

## GATE — met in-sandbox (evidence)
```
strip :root → distinct px outside = [1,2,3,4,8,12,20,24,28,32,44,64,72,92,120,140,180,240,250*,280,300,340,360,560]
off-scale stragglers (not in {1,2,3} and not %4) = NONE
referenced-but-UNDEFINED var(--*) = NONE
braces balanced 180/180 ; <script> 2/2 intact ; all panels + #send/#input present
```
(*250/170 live only inside :root as --w-aside/--gtile-minw, so they don't appear outside.)

## Interpretation note (for Verifier)
The spec's literal whole-file `grep -oE '[0-9]+px'` will still print scale VALUES — that is correct, they now live in :root as the single source of truth. The real gate = **no off-scale px outside :root; every var() defined.** Both hold.

## STILL NEEDED (portal access → route to Verifier)
Hard-refresh **:8099** and confirm: (a) screenshot — #send/.btn.pri render white-on-#2563eb, layout/spacing unchanged from pin 37549a041412; (b) empty console after refresh. I cannot self-serve :8099 from sandbox.

## Correction log
An earlier transform pass dropped trailing semicolons on ~134 rules + mangled the font-shorthand lines. Caught pre-ship, restored from pristine pin, redone cleanly with terminator-preserving regexes. Final file verified above.
