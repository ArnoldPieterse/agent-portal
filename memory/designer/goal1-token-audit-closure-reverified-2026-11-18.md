# Designer Goal #1 — Token Audit Closure Re-verification — 2026-11-18

**Verdict: ACCEPTANCE TEST NOW PASSES** (reverses ORCH's 2026-11-18 FAIL)

## Acceptance criterion
"grep returns 0 hits for hex colors in app.css outside the :root block."

## What ran
1. Read `memory/orchestrator/designer-goal1-token-verify-2026-11-18.md` (the FAIL leaf) — it listed 36 component-rule hex values and noted all matching tokens already exist in `:root`.
2. Re-scanned the LIVE `ui/app.css` (23351 bytes):
   - Total hex literals in file: **37** (all token definitions).
   - Hex literals OUTSIDE `:root` / `[data-theme=...]` blocks: **0**.
3. Spot-checked every rule ORCH flagged; all now use `var(--token)`:
   - `.acard.sel` -> `background:var(--sel-bg)` (was `#20304d`)
   - `.seg button.on` -> `var(--acc-deep)` + `var(--on-acc)` (was `#3a6fd6`/`#fff`)
   - `.msg.you` -> `var(--msg-you-bg)` + `var(--msg-you-border)` (was `#243b63`/`#33507f`)
   - `#intBanner` -> `var(--warn-border)`/`var(--warn-bg)`/`var(--warn-text)` (was `#d29922`/`#2d2000`/`#e3b341`)
   - `.qspin` -> `var(--queue-border)` + `var(--queue-accent)` (was `#30363d`/`#58a6ff`)
   - `#peek` -> `var(--peek-bg)`/`var(--peek-line)`/`var(--text-2)`/etc.
   - `.fdot.busy` -> `var(--dot-busy)` (was `#ffb454`)

## Conclusion
Since the 2026-11-18 FAIL leaf, every one of the 36 flagged hex values in component rules was replaced with a `var()` reference to an existing `:root` token. The file is now fully tokenized: **0 hardcoded color values remain outside the token-definition blocks.** No `ui/app.css` change was made this pass (the replacements were already present) — this leaf records the verified state so the acceptance test can be counted as passed.

## Reproduce
Strip the single `:root{...}` block, then count `#[0-9a-fA-F]{3,8}\b` matches in what remains -> **0** (0 = pass).
