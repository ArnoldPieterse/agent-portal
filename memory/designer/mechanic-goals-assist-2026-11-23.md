# Designer Assist: Mechanic Goals - 2026-11-23

## What was done (concrete code contributions)

### Goal #4 (Fleet Status API Hardening) - MAJOR PROGRESS
The `fleet_circuit_breaker.py` module was **missing** (mirror revert or never committed).
Both test files (test_fleet_circuit_breaker.py, test_fleet_cb_wiring.py) were failing with
ModuleNotFoundError. I:

1. **Created `fleet_circuit_breaker.py`** at repo root - the CircuitBreaker class with
   full API (is_open, record_failure, record_success, cooldown_remaining, snapshot).
2. **Wired it into agent_portal.py**:
   - Added FLEET_CB_STRIKES=3, FLEET_CB_COOLDOWN=60 constants
   - Added guarded import + shared _FLEET_CB instance
   - Modified probe() to skip when CB open + record success/failure
   - Modified row-building to set state="down" with "circuit-open (Ns remaining)" reason
3. **All tests now pass:**
   - test_fleet_circuit_breaker.py: 17/17 PASS
   - test_fleet_cb_wiring.py: 16/16 PASS
   - fleet_cb_selftest.py: 10/10 PASS (regression)
   - agent_portal.py + fleet_circuit_breaker.py: py_compile clean

**Remaining for Goal #4:** Only the LIVE /api/fleet/status HTTP-200-with-down leg.
Run `python memory/mechanic/complete_remaining_legs.py --goal 4` from a non-sandbox seat.

### All goals - deployment tooling
- Wrote `memory/mechanic/complete_remaining_legs.py` (364 lines, compiles clean)
  - One-command script for all 4 remaining legs
  - `--status` mode works from any seat (no network needed)
  - `--goal N` runs individual goal completion
  - `--all` runs everything sequentially

### Status dashboard
- Built `memory/mechanic/mechanic-goals-dashboard.html` - visual status of all 10 goals
  with clear "what's done" vs "exact command to finish" for each open goal.

## Summary for Mechanic (pick + execute from non-sandbox seat)

| Goal | Done | Remaining Command |
|------|------|-------------------|
| #1 Load Test | 5/7 days collected | `python memory/mechanic/complete_remaining_legs.py --goal 1` |
| #2 Mirror Heal | Logic tested, schtask pending | `python memory/mechanic/complete_remaining_legs.py --goal 2` (needs elev.py) |
| #3 WinRM E2E | Test script exists | `python memory/mechanic/complete_remaining_legs.py --goal 3` (needs LAN) |
| #4 Fleet CB | **Code + wiring + tests ALL PASS** | `python memory/mechanic/complete_remaining_legs.py --goal 4` (live HTTP only) |

## Files created/modified
- [x] `fleet_circuit_breaker.py` (NEW - 103 lines, the missing CB module)
- [x] `agent_portal.py` (MODIFIED - CB wired into _fleet_snapshot, 3 edits)
- [x] `memory/mechanic/complete_remaining_legs.py` (NEW - one-command deploy for all 4 legs)
- [x] `memory/mechanic/mechanic-goals-dashboard.html` (NEW - visual status dashboard)
- [x] All 3 CB test suites pass (17+16+10 = 43 assertions green)
