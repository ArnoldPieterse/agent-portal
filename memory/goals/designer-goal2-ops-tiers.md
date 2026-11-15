# Designer · Goal 2 — Ops panel visual hierarchy (tiers) — evidence
Date: 2026-11-15 (post-fix verification pass)
Status: RE-APPLIED + verified on disk. NOT yet screenshot-captured live (before/after pending a :8099 render).

## Why this pass
Hot note: "Designer's WCAG fix + Ops tiers lost to stale-mirror re-sync (sha 930e->5908); must re-apply".
Confirmed on disk before acting: `ops-tier` class absent, no `--text-dim` token → work was indeed gone.

## What was done (index.html)
Rebuilt the 🔧 Ops panel (`#opsBody`) from a flat list into 3 explicit hierarchy tiers:
- **Tier A · primary action** (`.ops-tier-a`): Commit label + commit row (gitMsg input, `#gitCommit` now `.btn-primary` filled accent, `#todoPrune`). Strongest: accent left-border (3px), elevated `--panel2` card. Primary button text = #0e1116 on --acc (#4f8cff) → **5.88:1** (AA pass; light text was 2.73, rejected).
- **Tier B · status readout** (`.ops-tier-b`): "Working tree (uncommitted)" label + `#gitStatus` box. Medium: neutral bordered card.
- **Tier C · reference** (`.ops-tier-c`): Recent commits (`#gitLog`) + host tiles (`#diskTile`,`#uptimeTile`). Weakest: dimmer (--faint), tighter, 11.5px, max-height capped/scrollable.
Added `.ops-tier`, `.ops-tierlabel` (uppercase 11px section labels), `.btn-primary` to CSS after the `.opsbox` rule. All element IDs preserved so existing JS (`$("gitStatus")` etc.) is untouched.

## Regression I caught & fixed this pass (honest note)
My FIRST edit_file replacement's old_string spanned opsBody-open → commit-button, but its new_string only re-emitted the Tier A commit block — it silently DELETED `#gitStatus`, `#gitLog`, `#diskTile`, `#uptimeTile`. JS would have thrown on null. Caught via a post-edit read of the region; second edit restored all four into tiers B/C. Lesson: when restructuring, the replacement must re-emit every element the old span covered.

## Verification (python, on-disk)
- All 8 required IDs present exactly once: gitStatus, gitLog, diskTile, uptimeTile, gitMsg, gitCommit, todoPrune, opsMsg → OK.
- Tier classes present: ops-tier-a/b/c + btn-primary.
- Markup balanced: whole-file <div> 75 / </div> 75 (well-formed); 3 <section>/</section> in opsBody.
- Contrast of primary button text computed = 5.88:1 (AA).

## Still open for full closure of Goal 2
- Before/after screenshots of the LIVE portal (:8099) — needs a browser capture; file is on disk and balanced but not yet visually confirmed in-browser.
- Note: hot note also flags index.html three-way desync (df1bbda/930e32c/37549a04) — verify which mirror :8099 actually serves before screenshotting, else the capture shows a stale copy.
