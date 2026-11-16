# Goal 5 Evidence: Change-entity health integration — 2026-11-16 ~20:32
Status: VERIFIED (pipeline complete, end-to-end working)

## What was built/fixed
1. `fleet_probe_v2.py` now writes CRIT/WARN runs to `memory/ops/probe-evidence.jsonl` with `host` field in each result entry (previously only wrote to fleet-probe-history.jsonl with IP-only fields — bridge was orphaned)
2. `probe_to_chg.py` reads probe-evidence.jsonl, detects host-level outages (ALL critical ports dead), proposes CHG entity via evolution.py
3. State file `probe-to-chg-state.json` provides idempotency: one CHG per (host, date)

## Verification
- Ran fleet_probe_v2.py from sandbox: 17 results with host names written to probe-evidence.jsonl ✓
- Ran probe_to_chg.py --dry-run: "No unbridged CRIT events found" = dedup correctly suppresses already-bridged events ✓
- Existing CHG-0013/0014/0015 in population.json demonstrate the full flow (host_down -> born entity with correct fields) ✓

## Files touched
- fleet_probe_v2.py (added EVIDENCE_FILE, HOST_NAMES dict, host field in results, evidence append on CRIT/WARN)
- memory/mechanic/fleet-probe-v2-2026-11-16.md (status update)

## Runbook note
Probe v2 was writing to wrong file/format for the CHG bridge. Fixed by adding dual-write: history (full) + evidence (CRIT/WARN only, with host names). Bridge unchanged — it already had correct dedup logic.