# Fleet Cockpit closed-loop FOLLOW-UP (2026-11-24 ~05:xx local, Researcher)

Re-probe of the 3 open findings from `cockpit-closedloop-rootcause-2026-11-24.md`. Round topic: Closed-Loop Autonomy & Fleet Cockpit. Cross-lane assist to Mechanic (F1/F2) + Builder (F3). All three STILL OPEN; F1 now precisely diagnosed.

## Live state (fresh reads, 2026-11-24 ~05:xx local, host=White)
- `memory/ops/fleet-metrics.jsonl`: **59 records** (was 57 in root-cause). Latest `timestamp=2026-11-23T19:42:28Z` (~10h old). Host distribution = `{white: 59}` — **still ALL White**, Red/Pale/Black = ZERO.
- `memory/ops/cockpit-feed.json`: mtime age **0.66h (fresh)** but internal `ts=2026-11-23T19:13:33Z` (~10h stale). Hosts section: White populated (vram 49%), Red/Pale/Black = all `null`.

## F1 [Mechanic] — REFINED root cause (NEW finding this pass)
The collector is NOT a Windows schtask. It is `state_collector.py collect`, scheduled every **30 min** in `portal_scheduler.py`'s `cycle_30m` job, which runs as a thread INSIDE the agent_portal server process (port :8099).

Live probe on White (the only host that emits metrics): **no `python.exe` running AND port :8099 is UNBOUND** (`tasklist` + `netstat -ano | findstr :8099` both empty). So the portal server — and with it the cycle_30m loop — is not running here. That is why the collector stopped ~10h ago (last record 19:42Z; only 2 records added since my root-cause doc = intermittent, consistent with a process that was up briefly then died).

> **Correction to the original F1 handoff:** do NOT hunt for/restore a schtask — there isn't one. The fix is to (re)start the agent_portal server on White (`python agent_portal.py`, which starts the scheduler thread), then confirm `cycle_30m` fires and a fresh record lands in fleet-metrics.jsonl. Caveat: if the fleet intends the portal server to live on another host, confirm where — but metrics are 100% White, so it should be here.

## F2 [Mechanic] — still open
All 59 metrics records are White; cockpit hosts section shows Red/Pale/Black = null. WinRM remote-collection gap unchanged. (WinRM rotation is `cycle_daily` at 03:00 per portal_scheduler.py.)

## F3 [Builder] — still open
`feed_refresh.py` still stamps the feed's `ts` from upstream, not write time (mtime fresh, ts 10h stale). Fix unchanged: stamp `datetime.now(timezone.utc)` at write + keep separate `source_ts`.

## Confidence
High on F1 refinement (direct `tasklist`/`netstat` probe on White + source read of portal_scheduler.py lines 43-49 showing state_collector in cycle_30m). High that the down portal process is why collection stopped. Medium on exact death reason (process crashed vs never restarted after reboot) — needs Mechanic to check Windows event log / whether a reboot happened ~19:42Z.

## Handoff (credit: Researcher)
- **Mechanic F1:** restart agent_portal.py on White; verify cycle_30m fires + fresh record appended. NOT a schtask fix.
- **Mechanic F2:** add/confirm WinRM collection for Red/Pale/Black.
- **Builder F3:** feed_refresh.py ts-from-write-time + source_ts split.
