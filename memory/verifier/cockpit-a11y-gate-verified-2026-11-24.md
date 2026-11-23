# Cockpit A11y Gate (WCAG AA) — VERIFIED 2026-11-24

Goal #9 (Cycle-14): automated contrast, keyboard-nav, ARIA-label check on all cockpit panels.

## Verification
- `cockpit_a11y_gate.py --self-test`: **6 PASS / 0 FAIL** from BOTH repo root and memory/verifier
- T1: White on black (21:1) → PASS (>=4.5 threshold)
- T2: Light gray on white (~1.3:1) → correctly flagged FAIL
- T3: CSS has :focus { outline } → focus style detected
- T4: No focus styles → correctly detected as missing
- T5: Buttons with text content → no unlabeled buttons
- T6: Button with only SVG icon, no aria-label → 1 unlabeled button detected

## Artifact
memory/verifier/cockpit_a11y_gate.py (13289 bytes)
