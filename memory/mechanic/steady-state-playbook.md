# Steady-State Ops Playbook
**Lane:** Mechanic | **Cycle 17, Goal #2** | Created: 2026-11-24
**Trigger condition:** `fleet-mode.json` shows `"mode": "STEADY-STATE"`
**Probe frequency in steady-state:** 15min (reduced from 5min)
**Escalation policy:** escalate only on SLA breach (not on first anomaly)

---

## Procedure 1: REDUCED-CADENCE PROBE

**Trigger:** fleet-mode.json mode=STEADY-STATE detected at probe start.

**Steps:**
1. Read `memory/ops/fleet-mode.json`; confirm `mode == "STEADY-STATE"`
2. Set probe interval to 15min (write to seat-matrix.json `probe_interval_min: 15`)
3. Run standard seat_probe.py cycle (TCP + portal + autoloop check)
4. Log cadence change to `memory/ops/probe-cadence-log.jsonl`: `{ts, from_min, to_min, reason}`
5. On next probe: if mode reverts to WORK, restore 5min cadence and log

**Rollback:** If a seat goes unreachable during reduced cadence, immediately restore 5min probes for the affected seat only (per-seat override). Log: `{ts, seat, action: "restore_5min", reason: "unreachable"}`.

---

## Procedure 2: LIGHT-RECOVERY (single-step)

**Trigger:** Seat state = "degrading" (from predictive trend) OR first "stale" detection in steady-state.

**Steps:**
1. Confirm via single probe: `python memory/mechanic/seat_probe.py --force`
2. If degrading/stale persists after confirmation: attempt ONE recovery action only:
   - If model not loaded: `python memory/mechanic/model_orchestrator.py --seat <SEAT> --dry-run`
   - If dry-run passes: execute real load
3. Wait one probe cycle (15min) for state to clear
4. If still degrading/stale after 2 cycles total: escalate to Procedure 3

**Rollback:** If recovery action worsens state (new seat also affected), unload the model just loaded and restore previous seat-matrix.json snapshot. Log rollback to `memory/ops/auto-ops-decisions.jsonl`.

---

## Procedure 3: SLA-BREACH ESCALATION

**Trigger:** Any of:
- Seat unreachable >30min (SLA detection breach)
- Cascade triggered (multiple seats down simultaneously)
- Recovery failed after 2 light-recovery attempts
- Host TCP probe fails >2 consecutive cycles

**Steps:**
1. Write escalation entry to `memory/ops/auto-ops-decisions.jsonl`:
   ```json
   {"ts": "...", "action": "sla_breach_escalate", "seat": "<SEAT>", "breach_type": "<detection|recovery|cascade|host>", "elapsed_min": N, "steady_state": true}
   ```
2. Execute full recovery playbook (auto-recovery-playbook-v2.md) - all steps
3. If cascade: activate seat-routing-map.json fallbacks for affected seats
4. Notify via cockpit feed (write to memory/ops/cockpit-feed.json with severity=critical)
5. Record detection-to-recovery time in `memory/ops/recovery-times.jsonl`

**Rollback:** Full recovery playbook rollback applies (see auto-recovery-playbook-v2.md §Rollback). Additionally: if steady-state caused the SLA breach (reduced cadence missed a degradation), revert to WORK mode by writing `mode: "WORK"` to fleet-mode.json and restoring 5min probes.

---

## Procedure 4: STEADY-STATE EXIT

**Trigger:** Any of:
- Orchestrator writes `mode: "WORK"` to fleet-mode.json (new cycle starts)
- SLA breach occurred (Procedure 3 fired)
- 3+ consecutive probes show >2 seats in non-healthy state

**Steps:**
1. Restore probe cadence to 5min for all seats
2. Clear any per-seat cadence overrides
3. Log exit to `memory/ops/probe-cadence-log.jsonl`: `{ts, action: "exit_steady_state", reason: "<new_cycle|sla_breach|multi_unhealthy>"}`
4. Run one full probe cycle at 5min immediately (don't wait for next scheduled tick)
5. Verify all seats reach expected state within 1 probe cycle
6. If any seat still unhealthy post-exit: remain in WORK mode recovery until resolved

**Rollback:** Exit is irreversible by design (you can't re-enter steady-state mid-recovery). If exit was premature (false trigger), Orchestrator must re-declare STEADY-STATE after 3 clean cycles.

---

## SLA Targets (Steady-State)
| Metric | Target | Breach triggers |
|--------|--------|----------------|
| Detection latency | <15min (one probe cycle) | Procedure 3 |
| Single-seat recovery | <45min (3 probe cycles) | Procedure 3 |
| Cascade recovery | <2h | Procedure 3 + Orchestrator notify |
| False-positive rate | <1 per week | Log for tuning |

## References
- `memory/ops/fleet-mode.json` — mode SSOT
- `memory/mechanic/auto-recovery-playbook-v2.md` — full recovery (Procedure 3 delegates here)
- `memory/ops/seat-routing-map.json` — fallback routing on cascade
- `memory/ops/probe-cadence-log.jsonl` — cadence change audit trail
- `memory/mechanic/seat_probe.py --selftest` — verify trend detection before deploy