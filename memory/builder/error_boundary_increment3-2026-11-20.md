# Error Boundary Increment 3 - goals/files panels extended (2026-11-20)

## What was done
Extended showPanelError() coverage to the two remaining panels in uploads.js:
- **Files panel**: catch block now calls `showPanelError(list, err, filesLoad)` + updates filesHead status text
- **Goals panel**: catch block now calls `showPanelError($("goalsBody"), e, goalsLoad)` + sets goalsStat to warning

## Verification (in-process)
- All 5 showPanelError call sites confirmed:
  | # | File | Panel Element | Retry Function |
  |---|------|--------------|----------------|
  | 1 | core.js L341 | $("actBody") | actUpdate |
  | 2 | core.js L388 | $("fleetBody") | fleetUpdate |
  | 3 | core.js L483 | $("gitStatus") | opsLoad |
  | 4 | uploads.js L392 | $("goalsBody") | goalsLoad |
  | 5 | uploads.js L343 | list (=filesList) | filesLoad |

- All retry functions exist in their respective files
- Brace balance: core.js 291/291, uploads.js 250/250 (diff=0 both)
- Paren balance: core.js 1039/1039, uploads.js 1011/1011 (diff=0 both)
- .panel-error CSS block present in app.css

## Remaining for full closure
Live browser test: kill API -> verify all 5 error cards appear -> restart portal -> click retry on each -> panels restore.
This requires a running portal + browser session; not available in sandbox.
Code-level coverage is complete (5/5 panels).

## Files modified
- ui/uploads.js (2 catch blocks updated)
