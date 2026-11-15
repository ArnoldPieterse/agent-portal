# Goal 5 — Keyboard a11y (in progress, 2026-11-15)

**SHA:** `5b228d745716` (local index.html; not yet synced to shared root pin df1bbdaef684)

## What was implemented

1. **Initial focus** — added `autofocus` attribute to `<textarea id="input">` so keyboard users land in the composer on page load.
2. **Focus-on-open** — new `focusFirst(panel)` helper (L1245) finds first interactive element in a panel and focuses it via `setTimeout(…,0)`. Wired into ops, files, and goals panel toggle handlers. Fleet panel is async-loaded so focus would race the fetch; left for follow-up.
3. **Escape-close** — global `keydown` listener (L1246-1250): on Escape, closes the first `.open` panel among [opsPanel, fleetPanel, filesPanel, goalsPanel] and refocuses its toggle button. Skips if a `<dialog[open]>` is present (native dialog handles its own Escape).

## Already working before this change
- Enter to send (L1079), Shift+Enter newline (implicit)
- `<dialog>` with `.showModal()` gives native focus-trap + Escape-close for the agent editor
- Panels use `display:none` when closed → hidden panels don't pollute tab order
- Focus-visible styles on ops panel buttons/inputs (L143-148)

## Remaining to close goal
- Manual tab-through test on :8099 (need live portal access)
- ~~Fleet panel focus-on-open~~ ✓ done: `focusFirst($("fleetPanel"))` called after `await fleetUpdate()`
- Sync file to shared root (SMB mirror or git commit)