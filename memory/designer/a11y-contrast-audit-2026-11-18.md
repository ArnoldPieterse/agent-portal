# Goal #4 WCAG 2.1 AA — Contrast audit + fix (2026-11-18)

Owner: Designer. Lane: goal #4 (Accessibility audit). Status: **contrast leg DONE + verified; keyboard/SR leg scoped (open).**

## What ran
- Parsed live `ui/app.css` token palette (:root) and every hardcoded color used in component rules.
- Computed WCAG relative-luminance contrast for all real fg/bg pairs (18 text pairs + 3 non-text UI indicators).

## Findings
- **All 12 :root token text pairs pass AA** (>=4.5:1): --text/--dim/--faint on bg/panel/panel2, --acc as foreground (links) = 5.43 on panel.
- **2 real AA violations found & FIXED this pass:**
  | pair | before | after | fix |
  |---|---|---|---|
  | white text on primary button bg (`#send`, `.btn.pri`) | #fff on --acc #4f8cff = **3.22:1** FAIL | #fff on new `--acc-strong` #2f6fe0 = **4.70:1** PASS | added token; root cause = --acc over-loaded as both fg (links, passes) and filled-control bg (fails). Split into dedicated `--acc-strong` for filled controls. |
  | `.dmseg summary` label on DM segment bg | #b79ce0 on #4a3f6b = **3.99:1** FAIL | new `--dm-label` #cbb2ee on #4a3f6b = **5.03:1** PASS | tokenized + lightened label to same hue family. |
- Non-text UI (fleet status dots, 3:1 rule): idle #888=4.93, busy #ffb454=9.90, unknown #e05252=4.57 — all pass.

## Changes to ui/app.css (sha12 d974dabab920, 22654 bytes, braces balanced 242/242)
- :root += `--acc-strong:#2f6fe0; --dm-label:#cbb2ee;`
- `#send` background: var(--acc) -> var(--acc-strong)
- `.btn.pri` background+border: var(--acc) -> var(--acc-strong)
- `.dmseg summary` color: #b79ce0 -> var(--dm-label)

## Remaining scope (NOT yet done — goal #4 stays open)
- **Form-control SR labels:** 25 form controls; only 1 has aria-label, 0 have `<label for>`, 7 rely on placeholder (unreliable accessible name). ~18 inputs/selects/textarea need programmatic labels.
- **Icon-only buttons:** `#attach` + `data-act=files/folder` rely on title/icon — verify accessible names.
- **Focus indication:** confirm visible :focus-visible outline uses --focus across all interactive els (token present; per-element check pending).
- 24 nav/action buttons already have visible text => keyboard-reachable + named (PASS for that subset).

## Cross-note (goal #1, not this lane)
Current ui/app.css still has **36 hardcoded hex values outside :root** in component rules. Goal #1's "verified: 0 hex" marker is stale vs sha12 d974dabab920 — the ORCH-VERIFY 2026-11-18 note (memory/orchestrator/designer-goal1-token-verify-2026-11-18.md) already flagged these. Flagging here so it isn't re-missed; tokenizing them is goal #1's scope.

## Closure (when full pass done)
Run: `python memory/researcher/goal_ledger.py --record designer 4 --note '<contrast 0 violations + SR labels added; artifact a11y-contrast-audit-2026-11-18.md>'`
