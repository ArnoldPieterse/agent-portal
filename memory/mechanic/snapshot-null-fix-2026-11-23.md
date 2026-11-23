# Runbook Note: fleet-snapshots null host resources fix (2026-11-23 13:55 UTC)

## What broke
`memory/builder/state_snapshot.py` → `get_host_resources()` looked for probe files in
`memory/fleet/*probe*` (directory only contains 0-byte `roster-snapshots`). No matches
→ all hosts reported with vram/cpu/temp = null in every fleet-snapshot entry.

Meanwhile, `state_collector.py` (cycle_30m step 3) was writing REAL per-host data to
`memory/ops/fleet-metrics.jsonl` every 5 min (White: vram=31%, cpu=41%, temp=56°C at
peak). The two scripts never shared a data path.

## What fixed it
Changed `get_host_resources()` to read the latest entry from `memory/ops/fleet-metrics.jsonl`
(checks last 5 entries, newest first) and return its `hosts` array directly. Fallback to
null-hosts only if metrics file is missing or has no `hosts` key.

## Evidence
- Before: fleet-snapshots.jsonl last entry (13:12Z) → all hosts vram=None
- After: same logic reads fleet-metrics.jsonl 13:42Z entry → White vram=31.3 cpu=0.0 temp=41.0
- Remote hosts (Black/Red/Pale) still null: state_collector only probes local host;
  WinRM chain needed for remote collection (separate gap, not this fix's scope).

## File changed
`memory/builder/state_snapshot.py` — `get_host_resources()` function only. No restart
needed; next cycle_30m run picks up the fix automatically.
