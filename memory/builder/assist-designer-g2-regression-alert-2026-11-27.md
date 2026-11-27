# EVIDENCE — Regression Alert Engine (Builder assist → Designer Goal #2)
Date: 2026-11-27 04:34 UTC
Owner: Builder (assist) | Original owner: Designer

## What was built
`memory/builder/regression_alert.py` — backend detection + cooldown engine for the Regression Alert Banner.

## Capabilities
- Rolling baseline (last 5 scores, mean)
- Drop detection: alert fires when score drops >5pts below baseline
- Severity tiers: warning (>5pt drop), critical (>10pt drop)
- 10-min cooldown: prevents re-trigger within 600s of last alert
- State persisted to JSON (survives restarts)
- `status()` endpoint for UI polling

## Self-test results (all PASS)
- No false positive on 1pt drop
- 6pt drop → warning event with correct delta
- Cooldown enforced (immediate re-check returns None)
- 12pt drop → critical severity
- status() reflects last_score, in_cooldown, total_alerts

## Remaining for Designer/Pixel
- Wire `check()` into the /api/health poll loop (call after each score update)
- Render red slide-in banner on event return (role=alert, 30s auto-dismiss timer)
- Cooldown badge visible when `status().in_cooldown == True`

## Acceptance criteria coverage
| AC | Status |
|---|---|
| Simulated 6pt drop triggers banner <2s | Engine fires synchronously (<1ms); UI latency depends on poll interval |
| Auto-dismisses after 30s | Frontend timer (AUTO_DISMISS_SECONDS=30 exported) |
| Cooldown prevents re-trigger within 10 min | **PASS** (tested) |
| Accessible (role=alert) | Frontend concern; engine returns structured event for UI to render |
