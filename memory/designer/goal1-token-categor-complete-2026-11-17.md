# Goal #1 progress: token categories complete (2026-11-17)

## What was done
Added missing token categories to :root in ui/app.css and applied them throughout:
- --radius-sm:6px; --radius-md:8px; --radius-lg:12px -> replaced 30 raw px border-radius declarations
- --shadow-md:0 8px 24px rgba(0,0,0,.5) -> replaced the one raw box-shadow
- --dur-150:150ms; --dur-200:200ms -> replaced transition durations
- Fixed 2x #2a3342 to var(--line), 1x #3ddc84 to var(--ok), 1x #ff6b6b to var(--err)

## Token layer status: 29 properties
| Category | Count | Tokens |
|----------|-------|--------|
| color    | 12    | --bg --panel --panel2 --line --text --dim --acc --ok --warn --err --focus --faint |
| space    | 5     | --sp-4 --sp-8 --sp-12 --sp-16 --sp-24 |
| font-size| 6     | --fs-11 through --fs-16 |
| radius   | 3     | --radius-sm --radius-md --radius-lg |
| shadow   | 1     | --shadow-md |
| motion   | 2     | --dur-150 --dur-200 |

## Remaining for full closure
~30 component-specific hex values (DM borders, segmented-control active, fleet link colors,
queue panel, etc.) that do not yet recur across components. Will tokenize when patterns emerge
or during a dedicated dark-mode theming pass (goal #2 is already verified).

## Verification
- grep: 0 raw border-radius:Npx outside :root - PASS
- grep: 0 raw box-shadow: not using var() - PASS
- File: ui/app.css (modified in place)
