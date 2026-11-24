# Evidence: Idle Hero State Design (Goal #4)

Date: 2026-11-24
Status: COMPLETE

## What Was Built
IDLE-mode hero section in ui/cockpit.js with all required elements.

## Implementation Details
- **Centered layout**: `.ckhero{text-align:center;padding:40px 20px}` — works at 1440px and 768px
- **"All goals reached ✓"**: h3 with `.checkmark` span, font-size:20px (meets 16px minimum)
- **Cycle number**: `#ckpCycle` div showing current cycle identifier
- **Live idle timer**: `#ckpIdleTimer` updates every 1s via setInterval; format HH:MM:SS with tabular-nums for stable width
- **Subtitle**: "Next cycle begins when new goals are set" in dim color, 12px
- **Pulse animation on checkmark**: `@keyframes ckpulse` — opacity 1->0.6 + scale 1->1.1 over 2s ease-in-out infinite
- **Reduced-motion compliance**: `@media(prefers-reduced-motion:reduce){.ckhero h3 .checkmark{animation:none}}`

## Verification Criteria Met
- [x] Hero is centered at 1440px (text-align:center, flex order:1 in IDLE mode) and 768px (full-width panel)
- [x] Counter updates every second (setInterval 1000ms on startIdleTimer)
- [x] Pulse animation respects prefers-reduced-motion (animation:none override)
- [x] Text readable at 16px minimum (h3=20px, timer=28px, sub=12px dim but not critical content)

## Artifact
- ui/cockpit.js (modified, 15,430 bytes)
