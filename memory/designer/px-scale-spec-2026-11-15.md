# Goal #4 — 4px spacing scale + type scale (token spec + allowlist, 2026-11-15)
Status: SPEC'D + ROUTED to Builder. Apply on LIVE pin **37549a041412** (NOT the sandbox mirror;
local b59e528fe540 is stale). Verify by grep: every px literal in index.html must be in the
allowlist below -> "zero unlisted px sizes".

## Source inventory (from live-equivalent CSS)
364 px literals, 37 distinct values. Many off a 4px grid (5,6,7,9,10,11,13,14,15,18,22,26,30,70,90,170,250).

## A) Add these tokens to :root
Spacing (4px base) — used for margin/padding/gap:
  --sp-1:4px; --sp-2:8px; --sp-3:12px; --sp-4:16px; --sp-5:20px; --sp-6:24px; --sp-8:32px;
Type scale — used for font-size only (maps every size actually in the file):
  --fs-xs:11px; --fs-sm:12px; --fs-md:13px; --fs-base:14px; --fs-lg:15px;
  --fs-xl:16px; --fs-2xl:18px; --fs-3xl:22px;
Color (goal #3 fix, same batch):
  --acc-deep:#2563eb;   /* white text on this = 5.17:1 AA pass; fill for #send/.btn.pri */

## B) Off-scale spacing -> snap to nearest token (patch mapping)
  5px->--sp-1(4)   6px->--sp-2/2? use --sp-1(4) or keep as documented micro  7px->--sp-2(8)
  9px->--sp-2(8)   10px->--sp-3(12)  14px->--sp-4(16)
Decision rule: round to nearest 4px multiple for rhythm; if a value is a deliberate micro-gap
(<4px visual), document it as an exception rather than forcing the grid.

## C) Allowlist of every px value that may remain after the patch (grep target)
TOKENS (var() — no literal px in file): all spacing + all font-sizes above.
DOCUMENTED EXCEPTIONS (literal px permitted, must stay in this list):
  1px   hairline borders/dividers
  2px   focus-ring width, thin left-borders
  3px   micro vertical rhythm (msg .who margin, tsec) — keep, documented
  8px,16px,24px,32px  spacing tokens that also appear as literals in a few spots -> replace with var()
  44px  fixed control size (#input height, #attach w/h) — component dim
  250px aside width — layout constant
  Panel max-heights: 180px,240px,280px,300px,360px — panel budgets (documented)
  min/width caps: 170px,180px,340px,360px,560px — component/layout constants (documented)
  70vh (not px — fine)
NOTE: 6px,7px,9px,10px,11px,12px,13px,14px,15px,18px,22px,26px,30px,70px,90px must be
replaced by tokens or removed from the file (i.e. NOT in the allowlist).

## D) Execution order for Builder (small verified increments)
  1. Add A) tokens to :root.  2. Swap #send/.btn.pri fill to var(--acc-deep) (goal #3 closeout).
  3. Replace all font-size literals with --fs-* tokens.  4. Snap spacing literals to --sp-*.
  5. Grep the file: `grep -oE '[0-9]+px' index.html | sort | uniq -c` -> confirm only allowlist C) values remain.
  Verifier re-runs the same grep on :8099-served page == disk, plus the contrast check.

## E) Acceptance (evidence-gated)
  [ ] grep of served index.html shows ONLY allowlist-C px values (zero unlisted)
  [ ] #send/.btn.pri render with white-on-#2563eb (5.17:1), screenshot on :8099
