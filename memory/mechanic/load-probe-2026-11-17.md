# Load Probe - 2026-11-17 (Day 2)

**Result:** CRIT - Portal DOWN at probe time (01:41 UTC).

## What broke
Portal process not running on White. `start /b python agent_portal.py` issued but sandbox does not support background process spawning (no log produced, port still closed after 5s wait).

## What fixed it
Nothing yet - portal needs to be started from a context that supports backgrounding (the PortalWatchdog schtask on the real White host would handle this; in the sandbox we rely on the orchestrator/agent loop keeping it alive).

## Runbook note
- If load_probe.py returns CRIT: first check `netstat -ano | findstr :8099` on the host. If no listener, portal is down. On real White, PortalWatchdog (5-min schtask) auto-recovers. In sandbox, restart via agent loop.
- A CRIT day IS a valid baseline data point (it tells us the SLO was violated).

## Baseline status
- Day 1 (2026-11-16): OK - p95 at 50c = 751ms
- Day 2 (2026-11-17): CRIT - portal down, no latency data
- Need: 5 more healthy days for the 7-day regression window to activate.
