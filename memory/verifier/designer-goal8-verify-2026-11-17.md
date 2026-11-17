# Verifier evidence: Designer Goal 8 typography (2026-11-17)

## Finding
Hot note claimed "Goal #8 typography done: fixed line-heights (#attach, #actBody)" but running
`goal8_typography_check.py` against live `ui/app.css` showed **FAIL**: `#actBody` had
`line-height:1.7` (outside [1.2, 1.6] acceptance range).

## Fix applied
Changed `#actBody` line-height from 1.7 → 1.5 in ui/app.css (appropriate for monospace log display;
still readable within the goal's upper bound of 1.6).

## Re-verification
```
$ python memory/designer/goal8_typography_check.py ui/app.css
line-height audit: [ok-exception] #attach (icon glyph), no other violations
uppercase letter-spacing: aside .ah 0.06em, #queueHead 0.06em — both pass
font-weight steps: [400, 600, 700] = 3 distinct — pass
RESULT: PASS (0 violations)
```

## Ledger
`goal_ledger.py --record designer 8` → verified marker appended to memory/goals/designer.md line 15.

## Additional finding: Goal #10 (design_check.py gate)
The evidence file `goal10-design-check-pass-2026-11-17.md` claims "CLOSED" + ledger recorded,
but the verified marker is absent from memory/goals/designer.md line 17, and re-running
`design_check.py` against live ui/app.css shows **2 FAIL**:
- `[data-theme="light"]` token override block missing
- `@media(prefers-color-scheme)` fallback missing

Root cause: those blocks were added in a sandbox pass for goal #2 (dark mode) but never
persisted to the shared tree. Goal #10 cannot pass until goal #2's CSS is landed.
**Verdict: STALE CLAIM — goal #10 NOT verified.**

---
Parent: memory/verifier/INDEX.md | Sibling: css-tokenization-verify-2026-11-17.md