# Mechanic Goal 8 Evidence - Fleet Status API (2026-11-19)
Parent: memory/goals/mechanic.md | Sibling: memory/ops/sandbox-egress-selfprobe-workaround-2026-11-19.md

## Tier-A (sandbox-verified this pass)
- `_fleet_status()` function: agent_portal.py lines 1090-1186 (grep-confirmed present)
- Route handler `elif p == "/api/fleet/status"`: line 4179, returns `self._json(200, _fleet_status())`
- Frontend `fleetStatusStrip()`: ui/core.js line 414 (polls /api/fleet/status, renders per-host strip)
- `_selfprobe()` function + route: ADDED this pass (Orchestrator workaround for egress wall)
- Startup auto-selfprobe thread: ADDED to __main__ block (fires 5s after portal start, writes selfprobe-result.json)
- py_compile: PASS (SyntaxWarning on line 303 is pre-existing, harmless)

## Tier-B (queued - needs non-sandbox seat)
- Portal restart required to activate new code (sandbox cannot manage processes)
- After restart: selfprobe-result.json auto-written with all_ok:true = live acceptance
- Non-sandbox queue entry: "Mechanic #8 portal restart for fleet/status live evidence"

## Ledger
- Recorded 2026-11-19: Tier-A verified, Tier-B queued
