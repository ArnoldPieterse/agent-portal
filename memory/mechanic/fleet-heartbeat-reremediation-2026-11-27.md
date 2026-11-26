# Fleet Heartbeat Re-Remediation — 2026-11-27 (pass c, second refresh)

**Trigger:** fleet-heartbeat.json was stale again (511 min at pass start). Previous fix (1h earlier in same day) did not persist across sandbox session.

**Action taken:**
1. `python memory/mechanic/seat_probe.py --force` → refreshed seat-matrix.json (ts 2026-11-26T18:00:40 UTC)
2. `python memory/mechanic/fleet_heartbeat.py generate` → rebuilt fleet-heartbeat.json (ts 2026-11-26T18:00:41 UTC)
3. `python memory/mechanic/fleet_heartbeat.py check` → **{"fresh": true, "age_s": 3.1, "threshold_s": 5}** PASS

**Verdict:** REMEDIATED (again). File is live-fresh; seats_stale_count=4 is accurate (sandbox cannot reach remote hosts).

**Pattern:** This is the second re-remediation in one day. Root cause: no persistent scheduler in sandbox (schtasks COM unavailable); each sandbox session starts with stale files until an agent pass triggers the probe chain. Durable fix requires either (a) autoloop invoking seat_probe+generate on every pass, or (b) a Windows service outside the sandbox.

**Runbook note:** `seat_probe.py --force` + `fleet_heartbeat.py generate` = 2 commands to un-stale the heartbeat; ~3s total runtime.
