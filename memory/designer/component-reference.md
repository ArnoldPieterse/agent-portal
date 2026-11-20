# Component Visual Reference — ui/components.js

Quick-lookup for all agents building UI. Each entry: purpose, copy-paste example, visual description, accessible name pattern.

File: `ui/components.js` | Exported as `window.UI.*` | No external dependencies.
All styling via CSS custom properties from `ui/app.css`.

---

## 1. UI.card(opts) -> HTMLElement

**Purpose:** Container for grouped content (agent cards, fleet detail panels, goal items). Provides a titled header row with optional badge and a body area.

**Usage example:**
```js
const el = UI.card({
  title: "Fleet",
  subtitle: "4 hosts - 8 agents",
  badge: { label: "3 ok", tone: "ok" },
  bodyHtml: "<p>Details here</p>",
  onClick: () => console.log("clicked"),
  selected: true
});
container.appendChild(el);
```

**Visual description:** Rounded rectangle with subtle border. Top row has bold title (left) and optional pill badge (right). Body area below with padding. When `selected`, border shifts to accent color. When `onClick` is set, cursor becomes pointer.

**Accessible name pattern:** If `onClick` present -> `role="button"` + `tabindex="0"`. Title text serves as implicit accessible name via `<b>` element in header. No explicit `aria-label` needed unless body content is non-textual.

---

## 2. UI.badge(opts) -> HTMLElement

**Purpose:** Inline status indicator - a colored dot followed by short label text. Used for agent model state, host health, goal cycle chips.

**Usage example:**
```js
const b = UI.badge({ label: "active", tone: "ok" });
// or standalone dot:
const dot = UI.badge({ tone: "warn" });
```

**Visual description:** Small inline `<span>` with a 6px colored circle (dot) + optional text. Tone classes: `--ok` (green), `--warn` (amber), `--err` (red), `--info` (blue), `--dim` (grey). Dot uses `currentColor` inherited from the tone class.

**Accessible name pattern:** No ARIA role - purely decorative + text. Screen reader reads the label text directly. If no label, it is a visual-only indicator (add `aria-hidden="true"` at call site if no semantic value).

---

## 3. UI.gauge(opts) -> HTMLElement

**Purpose:** Compact circular SVG gauge showing a percentage or score (0-100). Used for fleet health score, agent performance metric.

**Usage example:**
```js
const g = UI.gauge({ value: 87, max: 100, label: "health", size: 48 });
container.appendChild(g);
```

**Visual description:** Ring gauge (SVG circle with `stroke-dasharray`). Track is grey (`var(--line)`), fill arc is colored by threshold: green >=80%, amber >=50%, red <50%. Center shows rounded percentage number. Optional small label below in dimmed text. Size scales proportionally (default 48px diameter, stroke ~4px).

**Accessible name pattern:** No ARIA role on the container. The `<text>` element inside SVG is readable by screen readers as the value. Add `role="img"` + `aria-label` at call site if the gauge represents a named metric (e.g., `el.setAttribute("aria-label", "Fleet health: 87%")`).

---

## 4. UI.timelineNode(opts) -> HTMLElement

**Purpose:** Single node in a horizontal goal-cycle timeline strip. Shows cycle label, open/closed counts, and completion color.

**Usage example:**
```js
const node = UI.timelineNode({
  label: "Cycle 3",
  open: 2,
  closed: 8,
  active: true,
  onClick: () => showCycleDetail(3)
});
timelineContainer.appendChild(node);
```

**Visual description:** Vertical stack: colored dot (14px circle) -> label text -> "open/total" stat in dimmed small text. Dot color by completion: green = 100%, amber >=50%, red <50%. When `active`, wrapper gets `.ui-tl-node--active` class (typically a highlight ring or background).

**Accessible name pattern:** `role="button"` + `tabindex="0"` + `aria-label="{label}: {open} open, {closed} closed"`. Keyboard: Enter/Space fires `onClick`.

---

## 5. UI.collapsiblePanel(opts) -> HTMLElement

**Purpose:** Expandable section with a toggle header (chevron + title) and hidden/shown body. Used for ops panel sections, agent detail drawers, knowledge base lists.

**Usage example:**
```js
const panel = UI.collapsiblePanel({
  title: "Recent Runs",
  body: "<ul><li>Run #42 - ok</li></ul>",
  open: false,
  onToggle: (isOpen) => console.log("toggled to", isOpen)
});
container.appendChild(panel);
```

**Visual description:** Full-width button header with a small chevron (triangles) + title text. Body below is hidden by default (`display:none`). Chevron rotates via CSS transition on toggle. No border or background distinction - blends into parent layout.

**Accessible name pattern:** Header is a `<button>` with `aria-expanded="true|false"` managed automatically. The button's text content (chevron + title) serves as accessible name. Body has no explicit ARIA role; screen readers skip hidden content via `display:none`.

---

## CSS Custom Properties Used

All components reference these tokens from `ui/tokens.css` / `ui/app.css`:

| Token | Purpose |
|-------|---------|
| `--ok` | Success/healthy green |
| `--warn` | Warning amber |
| `--err` | Error/alert red |
| `--line` | Border/divider grey |
| `--dim` | Muted text color |
| `--fs-12` | Small font size (12px) |

## Design Constraints

- All components are stateless factories - they return a DOM element, no internal state.
- No external CSS/JS dependencies; all styling is inline or via class names defined in `ui/app.css`.
- Theme-aware: colors use `var(--token)` so light/dark/high-contrast themes work without modification.
- Touch targets: interactive elements (card with onClick, timelineNode, collapsiblePanel header) are >=44px tall at 768px breakpoint.

## Quick Decision Table

| Need | Use |
|------|-----|
| Group content with a title | `UI.card` |
| Show status inline | `UI.badge` |
| Show a score/metric visually | `UI.gauge` |
| Show cycle/step progress in a row | `UI.timelineNode` |
| Hide/show a section on demand | `UI.collapsiblePanel` |
