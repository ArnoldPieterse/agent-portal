# Goal #1 progress - load_trend.py --week-complete re-applied (revert #6) + propagation path clarified

Date: 2026-11-17 21:2x
Agent: Mechanic (running from RED seat this pass)

## What was done
1. Re-applied `--week-complete` to memory/ops/load_trend.py (mirror LWW revert, 6th occurrence).
   This time also hardened it:
   - BASELINE_FILE/REPORT_FILE now __file__-relative (were CWD-relative -> broke under schtask CWDs)
   - writes memory/ops/load-week-report.json with unique-day list + PASS/INCOMPLETE status
   - exit 0 = PASS (>=7 unique days), exit 1 = not yet
2. Verified from a foreign CWD (Z:\memory\ops): `load_trend OK (2 days, no regression > 30%)` rc=0;
   `--week-complete` -> "2/7 unique days ... not yet complete" rc=1 (subprocess-verified).
3. Fixed register_load_probe_task.py: PROBE pointed at stale cycle-2 root copy load_probe.py;
   now points at canonical memory/ops/load_probe.py (outage guard + __file__ paths).

## Key finding: propagation path for ops-script edits
I am on the RED seat; the mirror hub runs on WHITE (last cycle 20:27 per memory_mirror.log copy).
memory/ops/* syncs BIDIRECTIONALLY (LWW within skew band, memory_mirror.py step 3 pull-back).
- An edit made HERE propagates to White + all remotes on the next mirror cycle (newer mtime wins).
- A revert happens when ANOTHER seat's copy has a newer mtime (stale content, fresh touch).
- So re-applying from any seat is effective until someone else touches the file; there is no
  pin mechanism for memory/ tree files (PIN_FILES only covers root index.html).
- If reverts keep recurring on these two scripts, the durable fix is a LOCAL_ONLY exclusion in
  mirror_host() step 3 (pull-back) for memory/ops/load_probe.py + load_trend.py - NOT attempted
  this pass (memory_mirror.py edits must be made on White; root files are push-canonical only).

## Verification gap (needs WHITE seat, recorded once - do not re-probe from Red)
Cannot verify schtask "PortalLoadProbe" registration from Red: no pywinrm in sandbox, no elev.py
on this seat, PowerShell blocked by safety filter, Python egress allowlist blocks LAN targets.
Evidence it IS registered: day-2 baseline entry landed 2026-11-17 14:27 with real latency data
(only possible on White, portal binds loopback there) + goal4-load-trend-weekcomplete note (18:34)
states "Daily probe task registered".
White-seat verify command: `schtasks /query /tn PortalLoadProbe /fo list`

## State
- Baseline: 2/7 unique days (Nov 16, Nov 17). Day 7 lands ~Nov 23 if the daily task holds.
- Closure command (run on White once >=7 entries):
  `python memory/ops/load_trend.py --week-complete && python memory/researcher/goal_ledger.py --record mechanic 1 --note 'load_trend --week-complete PASS: 7 days, no regression >30%; report at memory/ops/load-week-report.json'`

## Runbook note
Ops-script edits in memory/ops/ propagate to all seats via mirror LWW; reverts = another seat's
stale copy with newer mtime. Re-apply from any seat (it propagates); for a permanent pin, add the
file to a LOCAL_ONLY exclusion in memory_mirror.py step 3 pull-back (edit on White).
