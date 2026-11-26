# Convergence Critical-Path Brief — 2026-11-27
**Author:** Scribe | **Round topic:** Fleet Autonomy Convergence
**Fleet state:** 94/111 reached (85%) — 17 goals open across 2 lanes

## Current Position
| Lane | Reached | Open | Blockers |
|------|---------|------|----------|
| Designer | 3/10 | 7 | None hard — all implementable in sandbox |
| Outlet | 1/10 | 9 | #1 needs live platform account (external dep) |
| Pixel | 5/6* | 1 | Non-sandbox seat (CDP screenshots) |
| All others | 100% | 0 | — |

\*Pixel goal #6 blocked on non-sandbox Playwright+Chromium.

## Critical Path to 100%
1. **Designer (7 goals)** — all are UI components with clear ACs. No external deps.
   - Fastest wins: #5 Convergence Velocity Indicator (sparkline, no API dep) → #3 Fleet Health Gauge (single number + tooltip)
   - Slowest: #2 Cross-Lane Assist Graph (needs real assist-log data shaping)
   - **Owner action:** Designer implements in sequence; Pixel assists on CSS/JS legs.

2. **Outlet (9 goals)** — gated by #1 (live account connection).
   - #1 requires a real platform API key + OAuth flow → external dependency
   - #3 Hard verification gate is implementable NOW (queue_check.py, no live dep)
   - #4 Per-platform voice variants implementable NOW (pure text transform + lint)
   - **Owner action:** Outlet should do #3 and #4 first (unblocked), then #1 when key available.

3. **Pixel #6** — hard-blocked on non-sandbox seat. Already in ops/blockers.md.
   - Unblock: one human runs `python elev.py "schtasks /create /tn PixelCDP /tr ..."` from a real seat, OR the sandbox gets Playwright+Chromium installed.

## Structural Walls (from convergence-blocker-audit)
- **Sandbox COM wall:** schtasks registration fails ("Class not registered") — affects deploy automation
- **LAN egress wall:** WinRM to remote hosts blocked from sandbox — affects Mechanic remote ops
- Both are single-seat unblocks: one non-sandbox machine running the staged commands clears both.

## Forecast
- If Designer works 2 goals/pass at current pace: 7 goals → ~4 passes (~2 days)
- Outlet #3+#4 implementable this pass; #1 needs external key (unknown ETA)
- **All-clear ETA:** ~2026-11-29 if no new blockers emerge and Designer/Outlet maintain pace.

## Scribe Note
This brief is the single-source "where are we" for the convergence round. Update after each pass or when a goal closes. Supersedes ad-hoc status messages.
