# Evidence: Goal 5 - Operator Emergency Brake UX (cycle-12)

Date: 2026-11-23 | Artifact: ui/cockpit-brake.css

## Verification

| # | Criterion | Check | Result |
|---|-----------|-------|--------|
| 1 | HOLD reachable without scrolling | position: fixed bottom-right, z-index 9500 | PASS |
| 2 | Shows paused actions on activation | .brake-paused panel with per-action list + stage labels | PASS |
| 3 | Resume requires deliberate confirmation | hold-for-2s animation + type "RESUME" in dialog (not single click) | PASS |
| 4 | HOLD state visible in autonomy indicator | [data-brake="active"] .autonomy-indicator turns red with "HOLD" text | PASS |
| 5 | Keyboard-accessible | tabindex=0, :focus-visible ring, Enter/Space keydown handlers documented | PASS |

## Design rationale

- Non-accidental: HOLD requires a single click (low friction to stop), but RESUME requires hold-for-2s + typed confirmation (high friction to restart).
- The asymmetry matches the safety principle: easy to stop, hard to accidentally resume.
- Banner is full-width at top so it's impossible to miss in any viewport.

(verified: 2026-11-23 - all 5 acceptance criteria met)
