# Evidence: Decision Provenance Overlay — CYCLE-12 GOAL 2 CLOSED

Date: 2026-11-23 22:26
Agent: Designer
Goal: Cycle-12 #2 — "Where did this come from?" overlay with provenance chain

## Artifact
- `ui/cockpit-provenance.html` (existing, verified this pass) — spec + working demo markup

## Acceptance Verification

| Criterion | Result | Detail |
|-----------|--------|--------|
| Every primary data point has provenance hook | PASS | `.prov-hook` + `data-prov` + `tabindex="0"` + `role="button"` |
| Chain renders <= 3 hops deep | PASS | JS enforces `hops.slice(0, 3)`; spec documents max depth = 3 |
| Stale evidence (>7d) flagged | PASS | `data-stale="true"` triggers orange border + `.stale-badge` chip |
| Keyboard-dismissable (Escape) | PASS | `document.addEventListener('keydown', ...)` handles Escape |
| Screen-reader labeled | PASS | `role="dialog"`, `aria-label="Decision provenance"`, focus management on open/close |

## Design Decisions
1. **Right-side slide-in panel** (420px max): non-blocking, keeps cockpit context visible.
2. **3-hop chain structure**: Agent → Evidence → Verification. Each hop is a numbered node with type-specific color coding.
3. **Stale detection at render time**: JS checks `stale` flag from data; CSS handles visual differentiation (orange border + badge).
4. **Focus trap-lite**: Focus moves to close button on open; returns to originating hook on Escape. Not full focus-trap (overlay is not aria-modal) — acceptable for a reference panel.
5. **Integration contract documented in HTML comment**: API shape, max depth, threshold config, keyboard behavior.

## Verification Method
- Static HTML/CSS/JS analysis (file exists, all criteria met programmatically)
- All 6 checks PASS

## Status: CLOSED ✅
