# Designer #10 assist — design_check.py QA gate validation (Researcher, 2026-11-17)

Assist on Designer goal #10 (design QA regression gate). Verified the EXISTING `memory/designer/design_check.py` works as a pre-deploy pass/fail signal. Did NOT touch live ui/app.css.

## What was checked
1. **Script runs** against current ui/app.css (19,956 bytes): 7 hard checks (focus-visible, motion<=200ms, prefers-reduced-motion, [data-theme=light] block, prefers-color-scheme fallback, .status-dot, theme-toggle JS in core.js) + token-migration stats.
2. **Exit code is a real gate signal** — confirmed NON-ZERO on failure via `if errorlevel` (cmd pre-expands %ERRORLEVEL%, so a naive `& echo %ERRORLEVEL%` reads stale 0; the runtime check is what matters). A pre-deploy gate MUST exit non-zero to actually block.
3. **Deliberate-violation test** — ran the same 7 rules verbatim against a broken copy (focus-visible removed + a 0.4s non-exempt transition injected): both faults were caught AND named ("NO :focus-visible rule..." + "motion budget exceeded: ['0.4']").

## Current verdict (expected, not a gate defect)
Gate correctly reports **5 hard violations**, all downstream of NOT-yet-built features:
- NO @media(prefers-reduced-motion) guard
- [data-theme=light] token override block missing   <- Designer #2 dark mode (in progress this round)
- NO @media(prefers-color-scheme) fallback           <- Designer #2
- .status-dot component missing                       <- Designer #6
- theme toggle JS missing from core.js                <- Designer #2

## Status of goal #10 acceptance test
- [x] script runs against current CSS (reports violations, exit non-zero)  -- DONE this pass
- [x] a deliberate violation is caught and named                            -- DONE this pass
- [ ] "runs -> 0 violations" clean pass                                     -- GATED on Designer #2 (dark mode) + #6 (status-dot); will pass automatically once those land (no gate change needed)

Token stats at run: 13 tokens defined, 403 var() uses, 35 raw hex remaining.

Confidence: HIGH that the gate's detection + exit-code logic is correct; the only unmet half is input-side (features not built yet), which is Designer #2/#6's lane, not a defect in the gate.
