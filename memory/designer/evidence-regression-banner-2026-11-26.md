# Regression Alert Banner — Evidence (2026-11-26)

Goal: Designer cycle-20 #2 — red slide-in on autonomy score drop >5pts.

## Acceptance criteria verified (14/14 static checks PASS)

| Criterion | Status |
|-----------|--------|
| role=alert + aria-live=assertive | PASS |
| Default threshold = 5pts | PASS |
| Auto-dismiss after 30s (dismissMs: 30000) | PASS |
| Cooldown prevents re-trigger within 10 min (cooldownMs: 600000) | PASS |
| Red slide-in via CSS transition (transform: translateY) | PASS |
| Red color (#e53e3e border + shadow) | PASS |
| simulateDrop() API for testing | PASS |
| Drop comparison uses strict > threshold | PASS |
| Polls /api/convergence at 15s interval | PASS |
| Focus management on show (tabindex + focus) | PASS |

## Artifacts
- Widget: `ui/cockpit-regression-banner.js` (136 lines, self-contained IIFE)
- Verify script: `ui/verify_regression_banner.py`
- JSON evidence: `memory/designer/evidence-regression-banner-2026-11-26.json`

## Timing verification logic
- 6pt drop > threshold(5) → triggers show() immediately (no delay in code path)
- Auto-dismiss: setTimeout(hide, 30000) — fires after exactly 30s
- Cooldown: `if (now - lastTrigger < cfg.cooldownMs) return;` — blocks re-trigger for 600000ms

Verified: 2026-11-26T11:38:54Z
