## 2026-11-19 fleet_status.js endpoint fix (Mechanic c5#8)
**Bug:** ui/fleet_status.js fetched `/api/fleet/status` (non-existent); actual backend is `/api/fleet`.
**Fix:** Rewrote fetch to call `/api/fleet`; adapted render() to use the real data shape:
- hosts: array of {host, state(busy/idle/unknown), generations, agents, reason}
- overall badge derived from host states (any unknown=red, any busy=amber, else green)
- per-host dot color: idle=green, busy=amber, unknown=red
- timestamp from data.ts
**Verification:** parens+braces balanced; correct endpoint present; old wrong endpoint removed. 2662 bytes, 63 lines.
**Remaining for full closure:** live browser render test (needs non-sandbox seat with Chrome/Edge + LAN to :8099).
**Runbook note:** fleet_status.js was fetching a phantom endpoint; fixed to use /api/fleet which already exists in agent_portal.py L4072.
