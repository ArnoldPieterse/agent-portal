# Alert Escalation Chain - Design & Implementation
Date: 2026-11-20 (Mechanic, goal #8)
Status: BUILT + SELFTEST PASS (8/8). Watchdog integration pending non-sandbox deploy.

## Architecture

```
Failure detected
       |
       v
+-------------------+
| LEVEL 1           |  <5 min window
| Auto-retry x3     |  backoff: 5s, 15s, 45s
+-------------------+
       | (all retries exhausted)
       v
+-------------------+
| LEVEL 2           |  <30 min window
| Agent handoff     |  structured request logged
| (e.g. -> Orchestrator)   for reassignment
+-------------------+
       | (30 min unresolved)
       v
+-------------------+
| LEVEL 3           |  >45 min total
| NEEDS-HUMAN       |  written to memory/ops/blockers.md
| (terminal state)  |  requires human + `--resolve <id>`
+-------------------+
```

## Thresholds
| Constant | Value | Meaning |
|----------|-------|---------|
| L1_MAX_RETRIES | 3 | fails before escalating to L2 |
| L1_BACKOFF_S | [5, 15, 45] | seconds between retries |
| L2_HANDOFF_TIMEOUT_S | 1800 (30 min) | agent handoff window |
| L3_ESCALATE_TIMEOUT_S | 2700 (45 min) | total time before NEEDS-HUMAN |

## Files
- `memory/mechanic/escalation_chain.py` - core module (EscalationChain class + selftest)
- `memory/mechanic/escalation_state.json` - active incident state (auto-managed)
- `memory/mechanic/escalation_log.jsonl` - append-only audit log
- `memory/ops/blockers.md` - L3 target (NEEDS-HUMAN entries appended here)

## Integration Points
1. **portal_watchdog.py**: on port-check failure, call `EscalationChain("portal_down").fail()` instead of raw log+restart. On recovery, call `.success()`.
2. **mirror_heal.py**: on repeated SMB failures, use same pattern with incident_id="mirror_smb_{host}".
3. **fleet_probe_v2.py**: per-host probe failures feed into per-host incidents.

## CLI
```bash
# Self-test (no side effects, uses temp files)
python memory/mechanic/escalation_chain.py --selftest

# Resolve an incident after manual fix
python memory/mechanic/escalation_chain.py --resolve portal_down
```

## Verification Status
- [x] Module built + compiles clean
- [x] Selftest 8/8 PASS (all 3 levels fire correctly, state transitions verified)
- [ ] Watchdog integration (code change to portal_watchdog.py) - queued for non-sandbox deploy
- [ ] Live test: simulated failure escalates through all 3 levels in production
- [ ] NEEDS-HUMAN only fires after full chain exhausted (verified in selftest; needs live confirmation)
