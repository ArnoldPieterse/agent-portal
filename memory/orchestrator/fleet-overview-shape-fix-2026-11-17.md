# Fleet Overview Panel - Shape Fix Evidence (2026-11-17)

## Issue Found
Backend `/api/fleet/overview` returned flat keys (`model_status`, `goals_total`, `capacity_files`)
but frontend core.js L409-414 expected nested objects (`a.model.status`, `a.goals.total`, `a.capacity.files`).
This would have caused `undefined` values in the rendered panel.

## Fix Applied
agent_portal.py `_fleet_overview()`: changed per-agent dict from flat keys to nested structure:
```python
"model": {"status": ..., "ms": ...},
"goals": {"total": ..., "done": ..., "open": ..., "blocked": ...},
"capacity": {"files": ..., "size_kb": ...},
```
Also updated fleet-level summary to use `a["goals"]["total"]` etc.

## Verification
- All 8 agents return valid JSON with correct nested shape
- Frontend field access patterns (core.js L409-414) all resolve without TypeError
- Fleet summary computes correctly: 39/80 goals done = 48.8%
- Goal data matches live state: Orchestrator 0/10, Researcher 8/10, Builder 10/10, etc.

## Acceptance Criteria Status
- [x] Endpoint returns valid JSON for all 8 agents (verified in-process)
- [x] Panel renders without JS errors (field shapes now match; no undefined access possible)
- [ ] Live render confirmation (needs portal restart + browser check)

## Next Step
Restart portal to pick up agent_portal.py changes. UI already exists (core.js L402-417).
