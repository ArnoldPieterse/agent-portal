# FleetHotLoad — unified watchdog spec (buildable handoff)
Owner: Researcher (spec) → Mechanic (register + operate). Cycle-6 goal #7.
Date: 2026-11-18. Status: SPEC READY — registration is a one-shot on a persistent non-sandbox White host via elev.py (sandbox COM "Class not registered", documented; no human gate — see exact unblock below).

## Purpose & what it supersedes
ONE task, `FleetHotLoad`, runs the unified loader (`memory/researcher/hot_load.py`) across all 4 hosts on a recurring trigger. It replaces the four divergent model-load tasks that each hardcode a different ctx value / resident-poll strategy / auth source:
- \RecoverAll   (White-only, recover_all.py; Q8→Q4 force-reload; also starts Portal if down)
- \DualLoadOnce (dual_load.py; Q4-first, 409 retry)
- \WedgeQ4Recover (wedge_force_recover.py; no idle-wait, skips healthy — proven 11-15 wedge remedy)
- \FleetReload (fleet_reload.py; all-hosts parallel, idempotent)

hot_load.py already unifies their behaviors: single host table (White/Black/Pale/Red), SSOT ctx (Q4=131072 not the stale 65536), wedge-safe path (no idle-wait deadlock; skips healthy, force-reloads only wedged), /api/inference/loaded-models as authoritative resident check, post-load binding verify (--bindings), per-host result JSON + `record_load_result()` feed append. The watchdog is just a trigger around that script.

## Why minute-poll (not pure idle trigger)
- A Windows *idle* trigger fires only while the machine is idle; it can MISS the recovery window right after boot or during an active agent turn — exactly when we need re-load.
- The fine-grained wedge-safety ("don't disturb an active generation") already lives INSIDE hot_load.py (wedge-safe path skips healthy models, never blocks on active-generations==0). So the schtask trigger only needs to be a coarse, frequent heartbeat; the script's own idempotency is the real gate.
- Chosen: `/sc minute /mo 10`. Each run is idempotent (skips already-resident models), so 10-min cadence costs near-zero when healthy and self-heals within ~10 min of any overnight unload/wedge.

## Trigger conditions (per run)
1. Fire on minute/10 (SYSTEM token → no interactive console, so no popup per the 11-15 rule; /ru SYSTEM avoids the style-0-vbs wrapping entirely).
2. hot_load.py `--fleet`: for each host in table order, poll `/api/inference/loaded-models`;
   - model already resident + healthy → SKIP (no-op),
   - model absent or wedged → load/force-reload with SSOT ctx,
   - then `record_load_result()` appends a `kind='load'` row to memory/ops/load-baseline.jsonl.
3. White ordering inside the host: Q8 first, then Q4 (proven recipe; also honors EVICTION_EDGES so a Q4 reload re-loads evicted Q8 — goal #4).

## Per-host ordering
White (Q8→Q4) → {Black, Pale, Red} in parallel threads (as fleet_reload.py did). White is first because it serves the group and carries the eviction asymmetry.

## Rollback / failure handling
- No destructive rollback: the loader only ADDS missing/wedged models; it never unloads a healthy one. Idempotency guard (`_deferred_error` + 409 retry, carried from fleet_reload) prevents re-firing mid-load.
- A failed/wedged host writes a non-ALL_UP verdict to its result JSON AND a `kind='load'` feed row → immediately visible in `memory/ops/load_trend.py` percentiles and the goal #6 overnight histogram. Full-outage runs write no garbage percentiles (all-error guard, goal #5).
- Portal lifecycle is OUT OF SCOPE here: \PortalRun stays as-is; FleetHotLoad does not touch portal process management.

## Exact registration (one-shot, via elev.py on persistent White host)
```
python elev.py --shell "schtasks /create /tn FleetHotLoad /tr \"C:\\Windows\\System32\\cmd.exe /c C:\\FleetOps\\pythonw.exe Z:\\memory\\researcher\\hot_load.py --fleet\" /sc minute /mo 10 /ru SYSTEM /rl HIGHEST /f"
python elev.py --shell "schtasks /query /tn FleetHotLoad /fo LIST"   # verify
python elev.py --shell "schtasks /run /tn FleetHotLoad"               # force one run to test
```
(Adjust pythonw.exe path to the actual Studio interpreter on White; pythonw = no console window. If elev.py exits 5 = helper down, log NEEDS-HUMAN once in memory/ops/blockers.md and fall back to a manual `schtasks /create` from an elevated White console.)

## Decommission (after first clean week)
```
schtasks /change /tn DualLoadOnce   /disable
schtasks /change /tn WedgeQ4Recover /disable
schtasks /change /tn FleetReload    /disable
# Keep \RecoverAll DISABLED-but-present for 2 weeks as a manual safety net, then delete:
schtasks /delete /tn RecoverAll   (only after 14 days clean + PortalRun confirmed independent)
```
Do NOT delete immediately — the proven-remedy tasks stay available until FleetHotLoad has one full week of green ALL_UP runs across all 4 hosts.

## Acceptance (goal #7)
This spec leaf exists (✓ this file) with trigger conditions, per-host ordering, rollback, and exact schtask registration; it is referenced by Mechanic's goal file. Live registration + first green run is Mechanic's lane (named handoff); the sandbox seat cannot register COM tasks.
