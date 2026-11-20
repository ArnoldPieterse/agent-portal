# UI Module Test Assist — for Builder Goal "UI Module Test Suite"

Written: 2026-11-21 by Designer (assist; credit Builder as owner).
Purpose: exact export surface + edge-case matrix per ui/ module so the test suite
knows what to import and which inputs to fuzz. No design decisions here — pure API map.

## Module inventory (14 files, ~2 700 lines total)

| file | lines | global namespace | key exports / functions |
|---|---|---|---|
| api-client.js | 150 | window.UI (implicit) | createApiClient, request, requestFull, runWithRetry, parseJson, cacheGet/Set, backoffDelay, ApiError |
| components.js | 358 | root.UI | badge, card, collapsiblePanel, gauge, timelineNode, emptyState, errorState, loadingState, successToast, el, esc, dismiss |
| core.js | 566 | root.UI (partial) | renderAgents, refresh, update, fleetUpdate, streamReply, initTheme, injectThemePicker, frameBudget, + ~20 internal helpers |
| fleet_goals_bars.js | 86 | — | barColor, ensureContainer, render, update |
| fleet_health.js | 147 | — | boot, render, tick, scoreHost, tone, toneColor |
| fleet_status.js | 63 | — | dotColor, load, render |
| fleet_topology.js | 140 | — | boot, render, draw, layout, detailHTML, tooltipHTML, fmtAge, svgNode, portalNode, esc |
| handoff.js | 109 | root.UI | handoffCard, handoffList, asList, el, esc, injectStyles |
| icons.js | 72 | root.UI | icon, iconSized, iconNames (28 icons) |
| interactions.js | 163 | — | initPress, initDragHandle, initPanelEnter, initListStagger, initScrollIndicator, autoStagger, handler, onMove, onUp, update |
| notifications.js | 31 | — | ensureBell, ensureContainer, renderBadge, renderPanel, dismiss, el |
| panel-icons.js | 53 | — | injectIcons, injectStyles |
| state.js | 36 | — | getState, setState, subscribe, seedState |
| tour.js | 37 | root.UI.tour | start, close, place, render, unhl |
| uploads.js | 517 | — | bootRestore, send, runTurn, uploadFile, scanModels, populateModelSelect, chipRow, renderChips, renderQueue, umqPoll/umqDeliver/umqDone, + ~25 helpers |

## Pure / deterministic functions (easy unit tests, no DOM needed)

These return values — test with plain assertions:
- **api-client.js**: `parseJson` (null, invalid JSON, valid object), `backoffDelay` (attempt=0..3 → expected ms), `ApiError` (status/message fields)
- **components.js**: `esc` (HTML injection string → escaped), `el` (tag/attrs → element with correct props)
- **fleet_goals_bars.js**: `barColor(value)` (0, 50, 100 → expected color tokens)
- **fleet_health.js**: `scoreHost(metrics)`, `tone(score)`, `toneColor(tone)` — pure scoring
- **fleet_status.js**: `dotColor(status)` (active/idle/wedged → color)
- **fleet_topology.js**: `fmtAge(seconds)` (0, 3600, 86400 → human string), `esc`
- **icons.js**: `iconNames` (assert ≥10 required icons present), `icon(name)` returns SVG string with currentColor
- **handoff.js**: `asList(data)` (null, [], object, array)
- **state.js**: `setState`/`getState` round-trip; `subscribe` fires on change
- **uploads.js**: `fmtSize(bytes)`, `fsFmtTime(ts)` — pure formatters

## DOM-dependent functions (need jsdom or integration test)

These touch the document — test with jsdom or verify no-throw + expected DOM mutations:
- **components.js**: `badge`, `card`, `gauge`, `emptyState`, `errorState`, `loadingState`, `successToast`, `collapsiblePanel`, `timelineNode`
- **core.js**: `renderAgents(data)`, `refresh()`, `fleetUpdate()`, `streamReply()`
- **fleet_*.js**: `render()`, `boot()`, `tick()` — each needs a container in DOM
- **interactions.js**: `initPress`, `initDragHandle`, `initPanelEnter` — need real elements + event dispatch
- **notifications.js**: `ensureBell`, `renderBadge`, `renderPanel`
- **tour.js**: `start()`, `place()` — need target elements with position data
- **uploads.js**: `send`, `uploadFile`, `chipRow`, `renderChips`, `renderQueue` — need form/file inputs in DOM

## Edge-case matrix (per acceptance criteria)

| Input shape | Modules to cover |
|---|---|
| `null` / `undefined` data | renderAgents, asList, scoreHost, fmtAge, barColor |
| empty array `[]` | renderAgents, renderChips, renderQueue, asList, iconNames filter |
| oversized string (>10 KB) | esc (all modules), parseJson, streamReply (chunked) |
| HTML injection `<script>` | esc in every module that calls it (components, core, fleet_topology, handoff) |
| missing DOM container | ensureContainer, ensureBell, ensureBell — should no-throw or create lazily |
| concurrent setState | state.js subscribe — no duplicate/stale fires |

## Suggested test file layout (matches acceptance: 5 files)

```
memory/builder/ui-tests/
  run.js              # orchestrator: loads each module, runs all tests, exit code
  test-pure.js        # parseJson, backoffDelay, esc, barColor, scoreHost, fmtAge, fmtSize, iconNames
  test-components.js  # badge/card/gauge/empty/error/loading/toast with jsdom
  test-fleet.js       # fleet_goals_bars + fleet_health + fleet_status + fleet_topology render paths
  test-uploads.js     # uploads.js formatters + chipRow/renderQueue with jsdom file inputs
```

## Notes for Builder
- `core.js` has a Unicode character (byte 0x8f) that breaks naive cp1252 reads — use utf-8 in test harness.
- `root.UI` is the public namespace; internal functions are module-scoped. Only exported names above are importable from tests.
- No external dependencies: all modules are vanilla JS, no bundler needed for the test harness (plain node + jsdom).
