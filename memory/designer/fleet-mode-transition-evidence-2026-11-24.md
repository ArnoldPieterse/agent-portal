# Mode Transition Animation - Evidence (Designer cycle-15 g2)
Date: 2026-11-24. Status: **REACHED**

## What was built
1. `ui/fleet-mode-transition.css` (60 lines) — Standalone CSS module:
   - Background color shift via `data-fleet-mode` attribute + CSS custom property (`--fleet-mode-bg`)
   - WORK=green tint, MAINTENANCE=amber tint, IDLE=grey tint
   - 400ms ease-in-out transition on main/panels
   - `.fmt-flip` helper class with transform transition for FLIP animation
   - `prefers-reduced-motion: reduce` → instant switch (no animation)
   - Print-safe (overlay hidden)

2. `ui/fleet-mode-transition.js` (115 lines) — IIFE exposing `window.fleetModeTransition`:
   - **FLIP technique**: First (batched getBoundingClientRect) → write reorder → Last (batched read) → Invert (translate transform) → Play (rAF + CSS transition, 0 JS reads)
   - Mode-specific panel orders: WORK (default), MAINTENANCE (health+productivity first), IDLE (chat+goals first)
   - `prefers-reduced-motion` guard skips animation entirely
   - `transitionend` cleanup removes helper class
   - Public API: `{setMode, reorder, transition, ORDERS}`

3. `ui/core.js` — Appended dynamic loader (script + link tags injected at runtime)

4. `memory/designer/fleet_mode_transition_verify.py` — 16-check verification script

## Verification
Ran `python memory/designer/fleet_mode_transition_verify.py`: **16/16 checks PASS**
- CSS: 400ms ease-in-out, mode colors, FLIP class, reduced-motion, print-safe, brackets balanced
- JS: FLIP all 4 phases present, 0 getBoundingClientRect in Play phase, reduced-motion guard, public API, braces balanced
- Integration: core.js loads both files

## Acceptance criteria met
- [x] Background color shift (green→amber→grey) over 400ms with ease-in-out
- [x] Panel reordering uses FLIP animation (not instant jump)
- [x] getBoundingClientRect calls <5 during transition (Play phase = 0)
- [x] `prefers-reduced-motion` respected (instant switch)
- [x] No layout thrashing (batched reads, single reflow per phase)