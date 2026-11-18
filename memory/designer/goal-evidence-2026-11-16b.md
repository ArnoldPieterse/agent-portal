# Designer goal evidence — 2026-11-16 (pass b)

## Goal #1: Full design token layer
**Status: DONE**
- 30 tokens in live `:root` (was 23): added --r-sm, --r-md, --shadow, --shadow-sm, --dur-fast, --dur-base, --dur-slow
- Zero hardcoded numeric border-radius values (27x8px + 2x12px to var(--r-sm)/var(--r-md))
- One box-shadow literal to var(--shadow)
- All transition durations tokenized (6x .15s to var(--dur-base), 1x .2s to var(--dur-slow))
- File: index.html, :root block

## Goal #3: Component abstraction
**Status: DONE** (2 dynamic JS template-literal styles remain - unavoidable per-agent colors)
- 27 to 2 inline style attributes (96% reduction)
- 18 new named component classes added: .panel-head__btn, .hint-sm, .hint-sm--mt6, .hint-sm--mt8, .row-stretch, .tile-fill, .hint--mt6, .field-narrow, .field-medium, .input-sm, .label--mb6, .label--mt6, .label--mb4, .input-auto, .hidden-block, .btn-sm-h, .btn-danger-text, .indent
- Remaining 2: color set via JS template literal (dynamic per-agent colors)

## Goal #4: Micro-interactions & motion budget
**Status: PARTIAL** (guard + tokenization done; new transition properties for panel expand/collapse pending)
- @media(prefers-reduced-motion:reduce) guard added to live CSS
- All 3 existing transition rules now use var(--dur-base)/var(--dur-slow)
- Max duration in play: .2s (within 200ms budget)
- TODO: add transitions for panel expand/collapse, message hover state

## Next steps (next pass)
- Goal #4: add new transition properties (.msg:hover, .panel expand, button :active)
- Goal #7: ARIA landmarks - wrap panels in section aria-label, add nav landmark
- Goal #8: typography - need 3+ font-weight steps (currently 400+600 only); add 700 for h1
