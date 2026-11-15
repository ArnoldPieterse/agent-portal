# Re-apply of Designer goals 2/3/4 to LIVE root index.html (2026-11-15)

## Why this note exists
Prior evidence files (wcag-contrast-evidence.md, ops-panel-hierarchy-evidence-2026-11-15b.md,
spacing-type-scale-evidence.md) were applied to a sandbox mirror that mirror-sync then clobbered.
Re-checked root index.html on disk this turn: sha df1bbdaef684 (1246 lines) contained NONE of the fixes
(no --acc-deep, no token scale, no ops-label/ops-actions; #send & .btn.pri were white-on-#4f8cff = 3.22:1 FAIL).
This turn re-applied all three to the file the portal actually serves.

## Applied (root index.html, now sha 07d4d7be2fe5)
- Goal 3 (contrast): added `--acc-deep:#2563eb`; `#send` and `.btn.pri` fill -> var(--acc-deep), white text.
  Measured: white on #2563eb = **5.17:1 PASS** (was 3.22:1 FAIL). ops-label faint #8b98ab on panel = 5.97:1 PASS.
- Goal 2 (Ops hierarchy): added `.ops-label` (11px uppercase recessed) + `.ops-actions` (panel2 bg, border, radius = elevated tier).
  Markup: "Working tree"/"Recent commits" -> .ops-label; commit+prune wrapped in .ops-actions with Commit = `btn pri` (primary CTA), Prune = ghost.
- Goal 4 (scales): added to :root --sp-1..--sp-6 (4px grid) + --fs-xs..--fs-xl type scale. Used by new ops rules.

## Integrity
Whole-file div balance 78/78 BALANCED. No JS touched. All CSS/markup only.

## BLOCKED — render verification (route to Verifier, needs :8099 up)
Portal :8099 is DOWN and mirror sync keeps clobbering local edits (see hot notes). So the *rendered*
acceptance legs are NOT yet satisfied on the live page:
- [ ] hard-refresh :8099 -> #send/.btn.pri show white-on-deep-blue (5.17:1), Ops panel shows 3-tier hierarchy; screenshot.
- [ ] automated contrast sweep on served page (goal 3).
- [ ] grep served index.html for px allowlist (goal 4 full normalization still open — only :root tokens added this turn;
      the ~50 literal-px snaps were applied to the stale mirror and need re-doing against THIS sha). 

## Handoff
@Verifier when portal is restored: run contrast sweep + Ops before/after screenshot on :8099, confirm disk==served sha.
@Mechanic: :8099 down is the gating dependency; also flag that mirror sync must stop clobbering designer edits or goals 2-4 will regress again after every sync.
