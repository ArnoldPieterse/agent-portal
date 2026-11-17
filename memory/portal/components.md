# Portal UI Component Reference

Owner: Designer | Updated: 2026-11-17
Parent: memory/portal/INDEX.md
Purpose: Onboard any agent's UI work from this file alone. Each component lists its selector, when to use it, and do/don't examples.

---

## 1. Message Bubble — `.msg`

**Selector:** `.msg` (base), `.msg.you` (user-sent), `.msg.silentmsg` (suppressed/system)

**Usage:** Every chat message in the main panel. The container flexbox aligns `.you` to the right; others left.

**Structure:**
```html
<div class="msg [you|silentmsg]">
  <div class="who"><span>AgentName</span><time>12:04</time></div>
  <div class="body">Message text here.</div>
  <!-- optional tool chips -->
  <span class="toolchip">web_search</span>
</div>
```

**Do:** Use `var(--panel2)` background, `var(--line)` border. Keep `max-width:78%` for readability.
**Don't:** Don't add inline styles for margins — the flex parent handles spacing. Don't use `.msg.you` for agent messages.

---

## 2. Panel Head — `header` / `.dhead` / panel titlebar pattern

**Selector:** Top-level `header` (app bar), `.dhead` (detail panel header), or the implicit first child of any `#*Panel` element.

**Usage:** Every collapsible panel (Goals, Fleet, Ops, Memory) has a clickable head row that toggles open/close. The pattern is: flex row with title on left, action button on right (`margin-left:auto`).

**Structure:**
```html
<div class="dhead" role="button" tabindex="0" aria-expanded="false">
  <span>Fleet Topology</span>
  <button aria-label="Close panel">×</button>
</div>
```

**Do:** Always include `role="button"` + `tabindex="0"` on the head div for keyboard access. Keep font at `var(--fs-13)` weight 600.
**Don't:** Don't nest interactive elements (links, inputs) inside the head — it breaks click-to-toggle.

---

## 3. Primary Button — `.btn` / `.btn.pri`

**Selector:** `.btn` (secondary/neutral), `.btn.pri` (primary/accent)

**Usage:** Action buttons that trigger a discrete operation (Send, Reset, Attach). The primary variant uses the accent token for high-visibility CTAs.

**Structure:**
```html
<button class="btn pri" id="send">Send</button>
<button class="btn" id="resetBtn">Reset</button>
```

**Do:** Use `.btn.pri` for at most ONE button per visible panel (the main CTA). All other actions use plain `.btn`. Focus ring is automatic via `:focus-visible` rule.
**Don't:** Don't use `.btn.pri` for destructive actions — those should use a custom danger variant (not yet defined; file an issue).

---

## 4. Status Badge / Chip — `.toolchip` / `.chipfile`

**Selector:** `.toolchip` (inline tool-use indicator), `.chipfile` (attached file chip in input bar)

**Usage:** Small inline labels that convey metadata without breaking text flow. Tool chips appear below messages to show which tools an agent called. File chips appear in the input area for uploaded attachments.

**Structure:**
```html
<!-- tool chip (inside .msg) -->
<span class="toolchip">web_search</span>

<!-- file chip (in input bar) -->
<span class="chipfile">
  <span>report.pdf</span>
  <button aria-label="Remove report.pdf">×</button>
</span>
```

**Do:** Keep text at `var(--fs-11)` (smallest scale step). Use `var(--warn)` color for tool chips to signal non-textual metadata.
**Don't:** Don't use chips for actionable content that needs a full button — they're too small for reliable tap targets (<32px).

---

## 5. Input Bar — `#input` + send/attach row

**Selector:** `#input` (textarea), the containing flex row with `#send` and `#attach` buttons.

**Usage:** The main message composition area at the bottom of the chat panel. Auto-grows via JS (`resize:none` + height set dynamically). Enter sends; Shift+Enter newlines.

**Structure:**
```html
<div class="ibar">
  <button id="attach" aria-label="Attach file">📎</button>
  <textarea id="input" placeholder="Type a message…" rows="1"></textarea>
  <button class="btn pri" id="send">Send</button>
</div>
```

**Do:** Keep `border-radius:8px` matching the token. Focus state uses `var(--acc)` border — don't override with outline.
**Don't:** Don't add a visible placeholder in production if the input has content; it causes layout shift on first keystroke.

---

## 6. Status Dot — `.dot` / `.fdot`

**Selector:** `.dot` (global connection indicator, top-right), `.fdot` (per-host dot in fleet topology rows)

**Usage:** Tiny 8px circles indicating live status. The global dot shows studio connectivity; fleet dots show per-host state (busy/idle/unknown).

**Structure:**
```html
<!-- global connection dot (in header) -->
<span class="dot on" id="sdot" aria-label="Connected"></span>

<!-- fleet host dot -->
<span class="fdot idle" aria-hidden="true"></span><b>host-01</b>
```

**States:** `.on` (green/ok), default (red/err) for global; `.busy` (amber), `.idle` (green), `.unknown` (red) for fleet.

**Do:** Always pair with an `aria-label` on the dot itself or a visible text sibling. The color alone is not accessible.
**Don't:** Don't make dots larger than 8px — they're indicators, not targets. If you need a clickable status element, use a full badge instead.

---

## Token Quick-Reference (used by all components)

| Token | Value | Used by |
|-------|-------|---------|
| `--sp-4` / `--sp-8` / `--sp-12` / `--sp-16` | 4/8/12/16px | All padding/gaps |
| `--fs-11` / `--fs-13` / `--fs-14` | 11/13/14px | Text sizes (smallest→body) |
| `--panel` / `--panel2` | Surface colors | Backgrounds |
| `--line` | Border color | All borders |
| `--acc` | Accent (blue) | Focus, primary btn, active states |
| `--ok` / `--err` / `--warn` | Status colors | Dots, badges |
| `--text` / `--dim` / `--faint` | Text hierarchy | Body / secondary / muted |

---

## Onboarding Checklist (for new agents doing UI work)

1. Read this file top-to-bottom.
2. Open `ui/app.css` — the `:root` block at top has all tokens.
3. For any new element, find the closest existing component and clone its pattern.
4. Use ONLY `var(--*)` tokens for colors, spacing, font-sizes. No raw hex/px outside `:root`.
5. Run `python memory/designer/design_check.py` after edits — it catches token violations + motion budget overruns.
6. If you add a new component class, append a section here before committing.