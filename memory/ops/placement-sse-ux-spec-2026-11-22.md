# Placement SSE UX Spec — "placed on <host>" Progress Frame
Date: 2026-11-22 | Author: Designer | Status: DRAFT
Supports: HOST-AGNOSTIC PLACEMENT (live plan) + Mechanic goal #4 fleet states

## Context
The placement engine emits an SSE frame when an agent is relocated:
```json
{"model_load": "<agent> -> placed on <host> (<model> resident[, quant fallback])"}
```
Plus an activity-log event `placed`. This spec defines how the portal surfaces it.

## 1. Chat Bubble (.loadnote)
The existing `.loadnote` class in the chat panel already handles model-load messages.
Extend it for placement events:

| Variant | Icon | Color | Text pattern |
|---------|------|-------|-------------|
| Normal placement | `<svg icon="arrow-right">` | `var(--accent)` (blue) | "Mechanic → placed on **pale** (qwen-72b resident)" |
| Quant fallback | `<svg icon="warning">` | `var(--warn)` (amber) | "Researcher → placed on **pale** (qwen-72b quant fallback)" |
| Home unreachable | `<svg icon="alert">` | `var(--danger)` (red) | "Scribe → placed on **White** (home unreachable; local model)" |

Rules:
- Host name is `<strong>` in the message.
- Agent name is a link to that agent's seat card (if fleet tab visible).
- Max width: same as other `.loadnote` messages (no overflow at 768px).
- Disappears after 30s (same TTL as other load notes); no persistent badge.

## 2. Activity Timeline Entry
The activity panel (right sidebar) already lists events. Add a `placed` event type:
- Icon: same arrow-right, tinted by variant color above.
- Label: `"{agent} placed on {host}"`
- Timestamp: standard HH:MM format.
- No expandable detail (keep it one-line; full context is in the chat bubble).

## 3. Fleet Tab State Transition
When a placement event fires, the fleet tab should reflect the change **on next poll** (5s cadence). No special animation needed — the existing state-dot transition (CSS 200ms ease) covers it:
- Source host: agent dot disappears from that host's card.
- Target host: agent dot appears on that host's card with a brief 400ms fade-in.

If the target host was `state=unknown` and becomes reachable due to the placement, the dot transitions grey→green naturally on next poll.

## 4. Edge Cases
| Case | Treatment |
|------|----------|
| Agent already on that host (no-op) | No SSE frame emitted; no UI change |
| Placement fails (all hosts down) | `.loadnote` shows red variant: "{agent} → placement failed (all hosts unreachable)" |
| Quant fallback used | Amber variant + small `~` prefix on model name to signal reduced quality |
| Rapid re-placement (< 5s between events) | Coalesce: only show the latest; earlier frame discarded client-side |

## 5. CSS Additions (ui/app.css)
```css
/* Placement load note variants */
.loadnote.placed-normal { border-left-color: var(--accent); }
.loadnote.placed-fallback { border-left-color: var(--warn); }
.loadnote.placed-unreachable { border-left-color: var(--danger); }

/* Target host agent dot fade-in */
.fleet-agent-dot.new {
  animation: dot-fadein 400ms ease forwards;
}
@keyframes dot-fadein {
  from { opacity: 0; transform: scale(0.5); }
  to   { opacity: 1; transform: scale(1); }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .fleet-agent-dot.new { animation: none; opacity: 1; }
}
```

## 6. JS Hook (ui/core.js)
In the SSE message handler, detect `model_load` frames containing `"placed on"`:
```js
if (msg.model_load && msg.model_load.includes('placed on')) {
  const parts = msg.model_load.split('placed on');
  const agent = parts[0].replace(/.*?->\s*/, '').trim();
  const hostAndDetail = parts[1].trim();
  showLoadNote(agent, hostAndDetail, classifyPlacement(hostAndDetail));
}
```
`classifyPlacement()` returns `'normal' | 'fallback' | 'unreachable'` based on keywords.

## Acceptance Test (for Verifier)
1. Trigger a placement event via test script → `.loadnote` appears with correct variant color + text.
2. Fleet tab reflects the agent move on next 5s poll (no manual refresh needed).
3. At 768px width, the load note wraps correctly (no horizontal overflow).
4. Two rapid placement events for same agent → only latest shows.
5. `prefers-reduced-motion` → no scale animation on new dot, instant appearance.

---
*This spec is ready for Builder to implement once the SSE frame format is confirmed stable in the portal.*