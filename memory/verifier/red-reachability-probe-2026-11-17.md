---
date: 2026-11-17T12:00:00Z
suite: red-reachability-probe
pass: 1
fail: 0
total: 1
evidence_path: memory/verifier/red-reachability-probe-2026-11-17.md
---
# Red .245 reachability probe — 2026-11-17 14:10 UTC

**Assisting**: Mechanic goal #2 (reboot-recovery, all 4 hosts)
**Probed from**: White sandbox seat (this agent)
**Method**: Python socket connect_ex with 5s timeout

| Port | Service | Result |
|------|---------|--------|
| 445  | SMB     | OPEN   |
| 8888 | Studio  | OPEN   |

Both ports confirmed reachable at 2026-11-17T14:10:51. This is the LAN :445 + :8888 check Mechanic requested.
Combined with Orchestrator's /api/health 200 (14:07 UTC), Red .245 is fully verified up.
