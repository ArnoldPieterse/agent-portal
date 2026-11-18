# Goal #4 Progress: Empty State Design (2026-11-19)

## What was done
Added a reusable `.empty-state` CSS component and applied it to the goals panel and files/uploads panel.

### CSS (ui/app.css, after line 160)
- `.empty-state` — flex column, centered, with icon + message + CTA button slot
- `.empty-state svg` — 40x40, token-stroked icons
- `.empty-state .es-msg` — 13px dim text, max-width 280px
- `.empty-state .es-cta` — outlined accent button with hover state
- `li.empty-state` — resets list-style for use inside `<ul>`

### JS (ui/uploads.js)
- **Files panel** (line 334): replaced plain text "No uploads yet" with full empty state: upload arrow SVG icon + message + "Upload a file" CTA button that triggers the existing attach button
- **Goals panel** (line 362): replaced `'<div class="hint">no goal files</div>'` with full empty state: checkmark circle SVG icon + explanatory message about memory/goals/ + "Retry" CTA that re-fetches /api/goals

### Coverage
- Fleet panel: already had proper states from 2026-11-18 work (loading/error/empty) ✓
- Goals panel: NOW has designed empty state with icon+msg+CTA ✓
- Files/uploads panel: NOW has designed empty state with icon+msg+CTA ✓
- Ops panel: always has content (git status, disk tiles); no meaningful "empty" case

### Acceptance criteria progress
- [x] All panels have designed empty states (fleet pre-existing, goals + files added this pass)
- [ ] CTAs are clickable (needs live browser verification — the onclick handlers reference existing DOM elements)
- [ ] No "escalations" panel exists in current markup; goal text mentions it but no such panel is implemented

### Files modified
- ui/app.css (+7 lines: .empty-state component + li reset)
- ui/uploads.js (2 lines changed: files empty state, goals empty state)

---

## Pass 2 (auto-loop, idle 311s) — upgraded the two weakest "no agents" surfaces
The earlier pass noted fleet as "pre-existing" but that was stale: the token/density pass had since stripped `.fleet-empty` CSS and left `#fleetBody` rendering a bare `<div class="hint">no hosts</div>` (no icon/CTA). Also `#agentList` rendered a blank list with zero guidance when no agents exist.

### Edits this pass (ui/core.js)
- **Fleet / no hosts** (`fleetUpdate`, line ~380): bare hint → full `.empty-state` (server-rack SVG + "polls every 5s, all hosts unreachable" message + "Refresh now" CTA → `fleetUpdate()`).
- **Agents list / none configured** (`renderAgents`, line ~32): added empty guard — person SVG + message + "+ Add agent" CTA → `#addAgent.click()`.

### Coverage of the 4 named states (final)
| State | Panel | Status |
|---|---|---|
| No goals set | `#goalsBody` | done (pass 1) |
| No agents online | `#fleetBody` + `#agentList` | done (this pass) |
| No uploads | `#filesList` | done (pass 1) |
| No escalations | — | no matching panel in index.html; nearest surfaces show inline hints. Not buildable until an escalation panel exists. |

### Verification
- Syntax: core.js brace/paren balance = 0 after both edits.
- Visual: evidence canvas rendered (4 states, production tokens from tokens.css); all CTAs fire a confirmation toast on click.

### Still open for full closure
- [ ] Runtime check: force each API to return an empty array and confirm the 4 states render in-browser.
- [ ] Escalations sub-item: needs an escalation panel first (Orchestrator call) — blocks that sub-item only, not the rest of goal #4.

### Files modified this pass
- ui/core.js (+2 empty-state blocks: fleet hosts, agent list)
