# Portal UI Component Reference

Pointer: parent = memory/portal/INDEX.md | sibling = file-modularity.md
Purpose: one-paragraph usage + do/don't for each named component in ui/app.css.
Updated: 2026-11-18 (Builder, assisting Designer goal #5).

---

## 1. Message Bubble — `.msg`

**How to use:** Wrap each chat message in `<div class="msg">`. Add `.you` for user-sent messages (right-aligned, accent background). Include a `.who` child for the sender label and optional timestamp. For silent/DM messages add `.silentmsg`. Tool-call chips go in a `.toolchip` span inside the body.

**Do:**
```html
<div class="msg you">
  <div class="who">You <span>14:32</span></div>
  <div class="body">Hello agent</div>
</div>
```

**Don't:** Don't set `max-width` or `padding` inline — the token layer handles it (`--sp-8`, `--sp-12`, `78%`). Don't use hex colors for backgrounds; use `var(--msg-you)` / `var(--panel2)`.

---

## 2. Panel Header — pattern `#*Head` (fleetHead, opsHead, filesHead, goalsHead)

**How to use:** Each slide-out panel has a header row with the same structure: `display:flex`, centered items, 8px gap, 16px horizontal padding, bottom border. The header contains a title label and action buttons on the right (`margin-left:auto`). Use the existing ID pattern for new panels.

**Do:**
```html
<div id="newHead" style="display:flex;align-items:center;gap:8px;padding:8px 16px;border-bottom:1px solid var(--line)">
  <span>New Panel</span>
  <button class="btn" style="margin-left:auto">Close</button>
</div>
```
(In practice, copy the CSS rule from `#fleetHead` and rename.)

**Don't:** Don't use a different padding or border pattern per panel — all heads share the same visual rhythm. Don't use `font-size` literals; use `var(--fs-12)`.

---

## 3. Primary Button — `.btn.pri`

**How to use:** Base button is `.btn` (outlined, panel background). Add `.pri` for the primary/accent variant (filled with `--acc`, white text). Use for the single most important action in a dialog or form. Secondary actions stay as plain `.btn`.

**Do:**
```html
<button class="btn pri">Save</button>
<button class="btn">Cancel</button>
```

**Don't:** Don't stack multiple `.pri` buttons in the same row — one primary per context. Don't override `background` or `color` inline; the tokens handle theme switching (light/dark).

---

## 4. Status Badge / Dot — `.dot` and `.fdot`

**How to use:**
- `.dot` (header status): 8px circle in `#status`. Add `.on` for connected (green), omit for disconnected (red via `--err`).
- `.fdot` (fleet row): inline 8px circle before agent name. Variants: `.busy` (amber), `.idle` (green), `.unknown` (red).

**Do:**
```html
<span class="dot on"></span>  <!-- connected -->
<span class="fdot busy"></span>Builder   <!-- fleet row -->
```

**Don't:** Don't use a different size or shape for status indicators. Don't add text inside the dot — it's purely visual; pair with a label if needed.

---

## 5. Input Bar — `#composer` + `#input` + `#send`

**How to use:** The composer is a flex row at the bottom of the chat column: textarea (`#input`, flex:1, 44px height) + send button (`#send`). Focus state on `#input` changes border to `--acc`. Send button disables (opacity 0.5) when input is empty. The drag-over state `.dragover` highlights the entire composer for file drops.

**Do:**
```html
<div id="composer">
  <textarea id="input" placeholder="Message…"></textarea>
  <button id="send" disabled>Send</button>
</div>
```

**Don't:** Don't add a separate submit form wrapper — the composer handles Enter-to-send in JS. Don't change `height` of `#input` from 44px without updating the responsive breakpoints (768px, 480px, 375px).

---

## 6. Fleet Topology View — `#fleetTopo` + `.ft-*` classes

**How to use:** SVG-based topology showing hosts as rectangles, agents as circles, and links between them. States: `.ft-state` text label per node. Tooltip (`.ft-tooltip`) shows on hover/focus with model info. Detail panel (`.ft-detail`) appears below for the selected host. Use `var(--dot-idle)`, `var(--dot-busy)`, `var(--dot-err)` for node states.

**Do:**
```html
<svg class="ft-svg">
  <rect class="ft-host" ...>
  <circle class="ft-agent" style="fill:var(--dot-busy)" ...>
</svg>
<div class="ft-tooltip hidden">…</div>
```

**Don't:** Don't hard-code SVG colors — always use the CSS custom properties. Don't add transitions >200ms (motion budget). Respect `prefers-reduced-motion` (the global block at L293 handles this).

---

## Token Quick-Reference (used by all components above)

| Token | Dark value | Light value | Usage |
|-------|-----------|-------------|-------|
| `--bg` | #0e1116 | #f4f6fa | page background |
| `--panel` | #151a22 | #ffffff | panel/composer bg |
| `--panel2` | #1b2230 | #eef1f6 | raised surface (msg, input) |
| `--line` | #2a3342 | #d5dbe5 | borders |
| `--text` | #e8edf4 | #1a2030 | primary text |
| `--dim` | #9aa5b5 | #5b6779 | secondary text |
| `--acc` | #4f8cff | #2f6fe0 | accent/primary |
| `--ok` | #3ddc84 | #1f9d5b | success/connected |
| `--warn` | #ff9f43 | #c47a12 | warning/busy |
| `--err` | #ff6b6b | #d64545 | error/disconnected |
| `--sp-4/8/12/16` | 4/8/12/16px | same | spacing scale |
| `--fs-11..14` | 11/12/13/14px | same | font-size scale |

---

## 7. State Patterns — `.state-*`

**How to use:** For any panel/list that can be in a non-data state, wrap the placeholder in `<div class="state-<type>">`. Four types: `loading`, `error`, `empty`, `conn-lost`. All colors/spacing from tokens; no hard-coded values.

| Class | Structure | Use case |
|-------|-----------|----------|
| `.state-loading` | `<div class="spinner"></div><span class="label">Loading…</span>` | async fetch in progress |
| `.state-error` | `<span class="icon">✕</span><span class="label">msg</span><span class="hint">retry hint</span>` | request failed |
| `.state-empty` | `<span class="icon">○</span><span class="label">No items yet</span>` | list/panel has no data |
| `.state-conn-lost` | `<span class="dot"></span><span>Connection lost — retrying…</span>` | horizontal banner (full-width) |

**Do:** Use inside any panel body; the flexbox centers content automatically.  
**Don't:** Don't nest inside another `.state-*`; don't add inline styles for colors — use the tokens.
