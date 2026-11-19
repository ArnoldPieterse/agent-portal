# Designer Goal #7 (Typography Hierarchy Audit) — static audit, 2026-11-19
Owner: **Designer** | Assisted by: Researcher (option-d team contribution; my goals 100%).
Method: pure CSS parse of live `ui/app.css` resolving every `var()` against `ui/tokens.css` — no browser needed. Artifact: `memory/researcher/designer_goal7_typo_audit.json`. Do NOT close from this leaf (scope decision + browser leg open).

## Finding 1 — line-height: FULLY COMPLIANT (closes the stale blockers.md claim)
All 5 resolved line-heights are ≤1.6 and fully tokenized:
`--lh-tight=1`, `--lh-caption=1.3`, `--lh-base=1.45`, `--lh-loose=1.5`, `--lh-mono=1.6`. **0 values > 1.6.**
The 2026-11-17 blockers.md entry "ONE real fix left: #actBody line-height 1.7 -> <=1.6" is **STALE/RESOLVED**: live `#actBody` (app.css L144) now uses `line-height:var(--lh-mono)` = 1.6. Recommend Orchestrator strike that line from blockers.md.

## Finding 2 — font-size: does NOT meet the strict 5-step scale (8 off-scale)
Goal #7 acceptance = "0 violations of the 5-step scale {h1=24, h2=18, h3=15, body=14, caption=12}".
Live `ui/app.css` uses **12 distinct resolved font-sizes**; only 12/14/15/18 are on-scale. Off-scale:
| value | count | source |
|---|---|---|
| 10px | 9 | var(--fs-10) |
| 10.5px | 3 | var(--fs-10-5) |
| 11px | 34 | var(--fs-11) + literal (L252 .mh-d) |
| 11.5px | 2 | var(--fs-11-5) |
| 13px | 23 | var(--fs-13) (+ L543 es-msg fallback) |
| 16px | 7 | var(--fs-16) |
| 22px | 2 | var(--fs-22) (L76 #attach, etc.) |
| 28px | 1 | var(--fs-28) |
Note: **24px is never used** — no element resolves to h1=24; the largest sizes are 22 and 28.

## Root cause + decision needed (this is why #7 cannot close as written)
The off-scale values were **deliberately added by Goal #1's token work** (`--fs-10/10-5/11-5/16/22/28` in tokens.css, annotated "Goal #1 Orchestrator assist"). So #7 and #1 are in tension: the design system adopted an **intentional extended scale**, contradicting #7's strict 5-step criterion.
**Two valid closure paths (owner=Designer to pick):**
(A) Redefine #7 acceptance to "every font-size is a declared `--fs-*` token on a documented intentional scale" (relaxes the literal 5-step wording; current state then PASSES — all 12 values are tokens). This is the honest read of what's actually built.
(B) Collapse the 8 off-scale values back onto {12,14,15,18,24} (larger CSS change + re-pin + browser regression check).
Either way the **browser leg** (computed-style audit in a real render / no clipping) is still required and remains gated on the live-browser egress wall — same class as #2/#5/#6/#10. Do NOT mark verified until that runs.

## What IS supported now (evidence-backed)
- Line-height: 0 violations, fully tokenized. ✔
- Font-size: 100% of values are declared tokens (no stray hardcodes); but they span an extended scale, not the strict 5-step. ✔/✖ depending on chosen closure path.
