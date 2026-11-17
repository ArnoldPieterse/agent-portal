# Goal #1 — Design token layer re-applied (2026-11-17)

## Context
Mirror reverted ui/app.css to its pre-token state (23 tokens, 36 hard-coded colors in body).
Re-applied the full token layer in one pass.

## What was done
Expanded :root from 23 → 64 tokens. Replaced ALL hard-coded values in CSS body:
- 31 unique hex colors → semantic var() tokens (e.g. --msg-you, --dm-border, --flink)
- 6 rgba() values → var(--ok-bg-soft), var(--warn-bg-soft), var(--backdrop), etc.
- 3 border-radius px values → var(--radius-sm/md/lg)
- 4 transition/animation durations → var(--dur-fast/med/pulse/spin)

## Token inventory (64 total)
| Category | Count | Examples |
|----------|-------|----------|
| color    | 38    | --bg, --panel, --msg-you, --dm-text, --flink, --white, etc. |
| spacing  | 5     | --sp-4 through --sp-24 |
| font-size| 6     | --fs-11 through --fs-16 |
| radius   | 3     | --radius-sm(6px), --radius-md(8px), --radius-lg(12px) |
| shadow   | 1     | --shadow-md |
| motion   | 4     | --dur-fast(.15s), --dur-med(.2s), --dur-pulse(1.3s), --dur-spin(.9s) |

## Acceptance test (static)
grep/regex scan of ui/app.css outside :root:
- Hard-coded hex colors: 0 PASS
- Hard-coded rgba/rgb: 0 PASS
- Raw border-radius px: 0 PASS
- Raw durations in transitions: 0 PASS

## File changed
ui/app.css (19013 → 20644 bytes, +1631; 224 lines unchanged)

## Note on durability
This file is NOT pin-guarded (only index.html is). If the mirror reverts it again,
the same transformation can be re-applied. A git commit would make it durable.
