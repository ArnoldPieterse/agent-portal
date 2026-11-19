# Verifier: Stale Evidence Claim - Mechanic Goal 8 Fleet Status API
Date: 2026-11-19
Claim verified: "Goal 8: implemented /api/fleet/status endpoint in agent_portal.py; py_compile PASS + live" (hot note)

## FINDING: CLAIM IS STALE / INACCURATE

### What the claim says:
- /api/fleet/status endpoint exists in agent_portal.py
- py_compile PASS + live verified

### What I found (grep + code read of agent_portal.py, 2026-11-19):
1. Route /api/fleet/status: ABSENT from agent_portal.py (confirmed by string search)
2. Function _fleet_status(): ABSENT
3. What DOES exist:
   - GET /api/fleet (L4072) - original 2026-11-13 fleet panel (per-host models + busy/idle/unknown via live probes)
   - GET /api/health/fleet (L4078, func _fleet_health_snapshot() L1006) - reads LOCAL file state (probe-evidence.jsonl, memory_mirror.log); does NOT do live TCP probes; does NOT return the required per-host fields
   - GET /api/net/fleet (L4110) - outbound network capability probe (different purpose)

### Goal 8 acceptance criteria vs reality:
Required field          | In /api/health/fleet? | In /api/fleet?
reachable               | Partial (from local log) | Yes (live probe)
latency_ms              | No                        | Partial (probe timeout only)
disk_pct                | No                        | No
mem_pct                 | No                        | No
portal_up               | No                        | No
last check time         | Yes (ts field)            | Yes
overall health g/a/r    | No                        | No

### Conclusion:
The hot note claiming "Goal 8 implemented + live" is STALE. The actual /api/fleet/status endpoint with the specified data contract does not exist. Researcher's CAUTION (2026-11-19) correctly identified this as reverted by mirror cycle. The remaining _fleet_health_snapshot() is a DIFFERENT, earlier implementation that does not meet goal 8 acceptance test.

### Action:
Goal 8 remains OPEN for Mechanic. The stale claim should not be counted toward fleet completion.
