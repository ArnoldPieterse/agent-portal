# Goal 10 - model_reload.py Bug Fix (2026-11-22)

**Bug:** `model_reload.py` used `agents.get(agent_name)` to look up an agent, but agents.json has structure `{"agents": [{"id":..., "model_id":...}]}` (a dict wrapping a list). The script would always return None for any valid agent name.

**Fix:** Changed lookup to iterate the `agents` array and match on `a["id"].lower() == agent_name`. Handles both dict-wrapped and bare-list formats.

**Verification:**
- `python memory/mechanic/model_reload.py researcher` -> correctly finds agent, gets model_id=quinn-q4, then fails at Studio :8888 (WinError 10013 - expected sandbox egress block)
- `python memory/mechanic/model_reload.py nonexistent_agent` -> correctly reports "not found in agents.json"
- `py_compile` clean

**Status of all 5 Runbook Automation scripts:**
| # | Script | Exists | Tested in-sandbox | Notes |
|---|--------|--------|-------------------|-------|
| a | fleet_status_check.py | Y | Y (DEGRADED - expected) | Works; reports per-host status |
| b | model_reload.py | Y | Y (egress block at API step) | Bug fixed this pass |
| c | restart_portal.py | Y | Y (COM wall - expected) | Needs non-sandbox for schtasks |
| d | mirror_force_sync.py | Y | Y (PASS x2, 47s) | Fully working in-sandbox |
| e | host_reboot_verify.py | Y | not yet run this pass | No agents.json dependency |

**Remaining for full closure:** Run all 5 from a non-sandbox White seat to get clean PASS on each; verify idempotency (run twice = same result).