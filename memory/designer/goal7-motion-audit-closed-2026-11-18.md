# Goal #7 — Motion & animation audit (CLOSED 2026-11-18)

Parent: memory/goals/designer.md · Sibling: goal7-motion-audit-complete-2026-11-17.md (earlier partial pass)

## Acceptance test (both pass)
1. **No interactive transition > 200 ms.** Grep of `ui/app.css` finds only `.15s` (150 ms) and `.2s`
   (200 ms) transitions — all within the cycle-2 motion budget.
2. **`prefers-reduced-motion` block present in `app.css`.** Added this pass (was MISSING; the
   earlier "complete" leaf only covered the duration audit, not the media query).

## Findings
- Exactly 2 ambient animations exist, both `infinite`: `.busyspan` (`pulse 1.3s`) and
  `.qspin` (`qspin .9s`). A prior audit regex mis-parsed `.15s`/`.9s` as `15s`/`9s` (missed the
   leading dot) — corrected; those are within budget.
- Spinners/pulses are indefinite indicators, not interaction transitions, so they legitimately run
  longer than 200 ms by design. The reduced-motion block handles them.

## Change (ui/app.css, appended at EOF)
```css
@media (prefers-reduced-motion: reduce){
  .busyspan{animation:none}        /* busy text stays readable, stops pulsing */
  .qspin{animation-duration:2s}    /* keep loading visible, calm the spin */
  *{transition-duration:.01ms !important;scroll-behavior:auto !important}
}
```
Rationale: WCAG 2.1 AA SC 2.3.3 (Animation from Interactions). Non-essential motion is disabled;
the functional loading indicator is slowed rather than removed so the "working" signal survives.

## Verify
`grep -c 'prefers-reduced-motion' ui/app.css` → 1 · transition-duration audit → 0 hits >200 ms.