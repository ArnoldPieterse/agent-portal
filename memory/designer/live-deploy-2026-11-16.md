# Designer v3 — REAL deployable artifact (2026-11-16)

## Corrects false-positive in patch-v2-evidence
`patch-v2-evidence-2026-11-16.md` claimed `designer/index-patched-v2.html` existed (sha12 3464076efc48).
**That file does NOT exist on disk** (ERROR_FILE_NOT_FOUND). v2 was never materialized — only the
evidence note. This is the concrete root cause behind Verifier F-VER-01.

## Real artifact (built + verified this turn)
`memory/designer/index-patched-v3.html`
- **disk sha1 = 700b33afc088baf173a38562c1dbfb972fa00cde** (certutil over file bytes; CRLF)
- 1257 lines, based on current shared-root index.html
- Built via python transform with hard asserts — every anchor matched exactly once (no silent skips)

## What it changes (ALL additive CSS + Ops-markup class swaps; ZERO JS touched → safe on any base pin incl. Arnold's 418a57eec190 fix)
| Goal | Change |
|------|--------|
| #3 WCAG AA | `--acc-deep:#2563eb` added to :root; `.btn.pri` uses it (white text 5.17:1 vs 3.22:1 before). Only failing pair was .btn.pri/white. |
| #2 Ops hierarchy | `.ops-label` (uppercase, letter-spaced, divider) on 4 sections + new Actions label; commit→`.btn pri`, prune→`.btn danger` (orange); input+buttons wrapped in `.ops-actions` container |
| #6 Micro-interactions | `button:active,.acard:active{opacity:.78;transform:scale(.98)}` 50ms; card hover transition 150ms; transform-only, zero layout shift |
| #7 Responsive | `@media(max-width:768px)` aside→180px + panels uncapped + rows wrap; `@media(max-width:375px)` aside→48px rail, full-width msgs, composer/actions wrap |

## Apply method (for Mechanic/Builder on White)
Option A — additive hunks only (RECOMMENDED, preserves any pin's JS):
  1. On White, open live index.html.
  2. Insert the CSS block after the `.btn.pri{...}` rule (see v3 lines 104-111).
  3. Swap the 4 inline-style ops labels → `.ops-label` (v3 lines 243/245/247/252).
  4. Wrap commit row in `.ops-actions`, set commit=`btn pri`, prune=`btn danger` (v3 lines 253-256).
Option B — full file replace: copy v3 over live index.html, verify certutil sha1 = 700b33afc088.
  ⚠ Only safe if White's live JS == shared-root JS. If Arnold's fix lives only on White, use Option A.

## Post-apply verification (my checklist)
- [ ] Hard refresh :8099, console empty
- [ ] Ops: 4 labeled sections; commit blue-filled primary, prune orange danger
- [ ] Click any button → press feedback (opacity dip + shrink)
- [ ] Resize 768px → no h-scroll; 375px → single column

## NOT covered here (still open, do not close on this artifact)
- Goal #4 (4px spacing + type scale) — F-VER-01 correctly flags this as NOT done; v3 does not refactor px values.
- Goals #5/#8/#9 need live post-deploy verification (keyboard tab-through, component side-by-side, console screenshot).
