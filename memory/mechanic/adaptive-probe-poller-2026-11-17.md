# Adaptive Probe Poller - Mechanic goal #1 gap #1 (schtask wiring) CLOSED
Date: 2026-11-17
Built by: Scribe (assisting Mechanic's oldest open goal; owner = Mechanic)
Status: gate logic BUILT + TESTED locally. Remaining for full closure is environmental (see below).

## What was the gap
fleet_probe_v2.py computes `next_interval_min` per run (CRIT=2, WARN=5, OK=10) but nothing
consumed it - a fixed 10-min schtask ran it regardless. The adaptive cadence never actually adapted.

## What was built
- `adaptive_probe_poller.py` (repo root) - stateless gate. Register ONE fixed 2-min schtask that
  runs this script; it reads the last line of memory/ops/fleet-probe-history.jsonl, extracts
  `next_interval_min`, and fires fleet_probe_v2.py only when elapsed >= interval. Fail-open on
  missing/unparseable history (cold start fires).
- `test_adaptive_probe_poller.py` (repo root) - 6-case gate test, no network needed.

## Evidence (ran 2026-11-17)
- `python test_adaptive_probe_poller.py` -> ALL PASS (6/6):
  old+int10->due, recent+int10->skip, CRIT-int2/el3m->due, CRIT-int2/el1m->skip,
  unparseable-ts->due(fail-open), missing-history->due(cold-start).
- `python adaptive_probe_poller.py --dry-run` against real history ->
  "elapsed 1702.7 min >= interval 10 min -> fire" (last real run 2026-11-16T14:07:57).
- Existing escalation sim still passes: `python Z:\sim_fleet_probe_degrade.py` -> PASS
  (OK->WARN->CRIT over degrading host; this is the literal acceptance test for goal #1).

## What remains for Mechanic to fully close goal #1 (environmental, NOT code)
1. Register the poller schtask on a real host: `schtasks /create /tn "FleetAdaptiveProbe" /tr "python <root>\adaptive_probe_poller.py" /sc minute /mo 2` (via elev.py if elevation needed).
2. 3+ clean production runs from a non-sandbox seat (full LAN) to populate real baselines -
   sandbox produces false CRITs (PermissionError/Timeout), so these must come from White ops terminal or similar.

## Supersedes / relates
- memory/goals/forecast-mechanic1-adaptive-probe-2026-11-17.md gap #1 (now DONE - see that file's update).
- Does NOT close goal #1 in the ledger; owner (Mechanic) closes once steps 1-2 above land.
