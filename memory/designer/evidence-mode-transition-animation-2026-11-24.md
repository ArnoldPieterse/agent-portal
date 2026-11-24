# Evidence: Mode Transition Animation (Designer goal #3)

Date: 2026-11-24
Agent: Designer

## What was implemented in ui/cockpit.js

### CSS transitions
- `.ckp-mode-banner` has `transition: background-color 400ms ease-in-out, color 400ms ease-in-out` — smooth color shift between mode variants (green→amber→grey)
- All panel sections (`.sec`, `.ckgrid`, `.ckrow`, `.ckhealth`) have `transition: opacity 350ms ease-in-out, transform 350ms ease-in-out`
- Active state `.ckp.mode-transitioning` sets `opacity:0; transform:translateY(6px)` on all sections — creates a clean fade-out/in cycle

### FLIP-lite animation for mode changes
- `animateModeChange()` function: adds `.mode-transitioning` class → 380ms timeout removes it
- This triggers CSS transitions for smooth reordering (no instant jump)
- Total transition duration: ~760ms round-trip (out + in) — well under the 1s jank threshold

### Reduced motion support
- `@media(prefers-reduced-motion:reduce)` sets `transition:none!important` on all animated elements
- JS check: `_reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches`
- When reduced motion is preferred, `animateModeChange()` returns immediately (no class toggling)

### Layout thrashing prevention
- Only one `classList.add()` + one `classList.remove()` per mode change — no layout reads during transition
- No getBoundingClientRect calls in the animation path (0 calls total)
- Transform-based movement (GPU-composited, avoids reflow)

## Verification
- Brace/paren balance: 92/92, 276/276
- 400ms ease-in-out present on banner
- prefers-reduced-motion media query present
- JS guard for reduced motion present
- No layout reads (getBoundingClientRect) in animation code path

## Artifact
ui/cockpit.js (~16.6KB)
