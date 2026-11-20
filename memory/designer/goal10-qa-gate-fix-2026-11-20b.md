<!-- PROVENANCE agent=designer created=2026-11-20 trigger=auto-loop -->
# Goal 10 - QA Gate Fix: Scales Now Derived from tokens.css
Date: 2026-11-20 (auto-loop pass)

## Problem
`design_qa.py` had hardcoded scale values (`SCALE_PX = {"12px","14px","15px","18px","24px"}`, `valid_steps = {"12","14","15","18","24"}`, `SPACING_PX = {"4px","8px","12px","16px","24px"}`) that didn't match the live 8-step type scale and 11-step spacing scale in tokens.css. Result: 2 false failures on clean portal (orphaned flags for --fs-11/13/16, gap:6px flagged off-scale).

Also found `gap:18px` in `.legend` (app.css:239) — genuinely off-scale (no --sp-18 token). Fixed to `gap:var(--sp-16)`.

## Fix
**design_qa.py**: All scale sets now derived dynamically from tokens.css at runtime:
- `fs_tokens`: parsed via regex from --fs-N definitions → {11,12,13,14,15,16,18,24}
- `sp_tokens`: parsed via regex from --sp-N definitions → {1,3,4,6,8,10,12,14,16,20,24}
- Check 1: font-size valid if it uses a defined --fs-N var OR a raw px matching a token value
- Check 2 (reframed): flags `var(--fs-N)` references where N is NOT in tokens.css (catches typos like --fs-99)
- Check 3: gap px values must be in the derived spacing set

**app.css**: `.legend` gap changed from `18px` → `var(--sp-16)` (nearest token, maintains compact legend density).

## Verification
```
$ python memory/designer/design_qa.py
RESULT: 12 passed, 0 failed / 12 total   (clean portal)

$ python memory/designer/design_qa.py  (with _zz_qa_selftest_broken.css: font-size:17px, gap:33px, var(--fs-99))
RESULT: 10 passed, 2 failed / 12 total   (exit 1 — checks 1+2 flag the broken file)
```

## Artifacts
- `memory/designer/design_qa.py` sha12=7cfa399f30e2 (scales derived from tokens.css)
- `ui/app.css` (.legend gap: var(--sp-16))
