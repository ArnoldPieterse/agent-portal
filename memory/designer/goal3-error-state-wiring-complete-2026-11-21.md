# Goal 3 - Error State Wiring Complete (2026-11-21)

## What was done
Wired `UI.errorState()` into remaining panel call sites in `ui/core.js`:

| Panel | Line | Before | After |
|-------|------|--------|-------|
| Chat (stream error) | 207 | `body.textContent="error: "+o.error` | `stopBusy(); body.innerHTML=""; body.appendChild(UI.errorState({message:"Request failed",detail:o.error}))` |
| Ops status bar | 428 | `$("opsStat").textContent="error: "+e` | `s.innerHTML=""; s.appendChild(UI.errorState({message:"Git status unavailable",detail:String(e)}))` |
| Ops disk tile | 438 | `$("diskTile").textContent="error: "+e` | `dt.innerHTML=""; dt.appendChild(UI.errorState({message:"Disk data unavailable",detail:String(e)}))` |
| Ops uptime tile | 438 | `$("uptimeTile").textContent="error: "+e` | `ut.innerHTML=""; ut.appendChild(UI.errorState({message:"Uptime unavailable",detail:String(e)}))` |

## Total panels using UI.errorState() (>=3 required)
1. Activity panel (line 359) - pre-existing
2. Merge queue (line 444) - pre-existing
3. Chat panel (line 207) - **new**
4. Ops status (line 428) - **new**
5. Ops tiles (line 438) - **new**

## Remaining raw "error:" strings (intentional, not panel states)
- Line 330: activity feed event label (list item in a scrollable log)
- Line 436: disk tile success-path fallback when API returns ok but no data
- Lines 453/454/466/473: `opsSay()` log entries (append to ops log, not panel states)

These are single-line log entries where a full error-state component (with padding, border, icon) would be visually inappropriate.

## Acceptance criteria check
- [x] 4 state types have visual specs (done in prior passes)
- [x] All implemented in ui/components.js
- [x] Used in >=3 panels each (errorState: 5 panels; emptyState, skeleton, loading also present)
- [x] No raw "Error" text without context in panel-level displays

## Artifact
`ui/core.js` (edited lines 207, 428, 438)
