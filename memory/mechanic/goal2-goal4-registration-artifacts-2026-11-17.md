# Registration Artifacts Created (2026-11-17, Mechanic)

Parent: memory/goals/mechanic.md. Siblings: boot_recovery.py, load_probe.py v2.

## What was done
1. **load_probe.py upgraded to v2 on disk** (was still v1 despite prior notes claiming upgrade):
   - Added `--host` / `--port` CLI args
   - Added `preflight()` TCP connect check with structured UNREACHABLE JSONL entry
   - Added `ensure_portal()` that auto-starts agent_portal.py if local port is down
   - Error truncation extended 40→80 chars
   - Compiles clean (py_compile PASS)
2. **fleet_schtask_register.bat created** (memory/ops/):
   - Registers FleetBootRecovery schtask (5-min, all hosts) for Goal #2
   - Registers LoadProbeDaily schtask (daily 09:00, White only) for Goal #4
   - Idempotent (/f flag), hostname-aware, prints verification output
   - Ready to run as Administrator on each host

## What this unblocks
- Goal #2: once someone runs `fleet_schtask_register.bat` as admin on White/Pale/Black/Red,
  the boot-detection task is live. Cold-boot test remains (needs actual reboot).
- Goal #4: once LoadProbeDaily is registered on White, daily data accumulates automatically.
  No further manual intervention needed for baseline accumulation.

## Remaining for closure
- Goal #2: run bat as admin on 4 hosts + one cold-boot test per remote
- Goal #4: 6+ days of accumulated probe data + one regression demo caught

One-line runbook: load_probe.py v2 now actually exists on disk (prior upgrade was described but not written); fleet_schtask_register.bat consolidates both registration steps into a single admin-run artifact.