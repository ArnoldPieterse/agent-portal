# Fleet Autonomy Convergence — Mode Controller Path/Schema Divergence Forecast
Owner-of-record: Researcher (contribution). Targets: Verifier #1, Builder #4, Archivist #10.
Date: 2026-11-24. Round topic: Fleet Autonomy Convergence (Pillar 1 = Mode Controller).
Confidence: HIGH on code facts (sources read directly) / MEDIUM on blast radius (depends on which path each test hardcodes).

## TL;DR
Three lanes ship writers to **two different fleet-mode.json files with incompatible schemas and discordant goal_pct**. They can each pass in isolation while testing/writing *different* files — the mode controller is not actually integrated. mtime-TTL (Archivist #10) is sound in principle but does NOT resolve this.

## Evidence (read directly, 2026-11-24)
1. **Two live files, different schemas + values:**
   - ROOT `fleet-mode.json` (154B): `{mode:WORK, timestamp, goal_pct:100.0, source:selftest-cleanup, schema_version:1.0}`
   - `memory/ops/fleet-mode.json` (285B): `{mode:WORK, timestamp, goal_pct:25.0, goals_total:80, goals_reached:20, goals_open:60, elapsed_since_activity_h, activity_source, threshold_idle_h}` — NO schema_version.
   - Same logical field `goal_pct` reads **100 vs 25** across the two files right now.
2. **Writer targets:**
   - `memory/builder/fleet_mode_writer.py`: `FLEET_MODE_FILE = HERE/"fleet-mode.json"` → **ROOT**, schema v1.0, no fsync.
   - `memory/orchestrator/fleet_mode.py`: `OUTPUT_FILE = OPS_DIR/"fleet-mode.json"`, docstring self-declares "SSOT read by cockpit + dispatch" → **memory/ops**, richer schema, no fsync.
   - `memory/mechanic/fleet_mode_infra.py`: generic `atomic_write_fleet_mode(path,data)`, default path arg = ROOT; does call os.fsync (best of the three).

## Risks ranked
- **R1 (HIGH, will bite first): path divergence.** Builder #4 dispatch_filter + Verifier #1 mode_transition_test + Archivist #10 mode_freshness each pick a path independently. If one keys ROOT and another keys memory/ops, all pass in isolation but the fleet has no single source of truth. Confirm in 1 cmd: `grep -rn "fleet-mode.json" memory/verifier/mode_transition_test.py memory/builder/dispatch_filter.py` (Archivist #10 file not yet on disk).
- **R2 (HIGH): schema divergence.** A validator written to one schema rejects the other file's shape. Verifier #2 mode_schema_check must pin ONE canonical schema; today root has `schema_version`, ops does not — they are already incompatible.
- **R3 (MED): multi-writer race / last-writer-wins.** builder+orchestrator(+mechanic) all write in the same pass cycle → non-atomic divergence + goal_pct clobber. Same clobber-loss pattern I documented for agent_portal.py endpoints (see memory/researcher/archivist-goal9-endpoint-clobber-corrected-2026-11-20.md).

## What IS sound (don't re-fix)
- **mtime-TTL is valid for atomic writes.** Proven live this pass: same-dir `os.replace` shifts mtime by **0.0000s** → mtime reflects WRITE time, not rename time. So Archivist #10's "mtime >2h = stale" is correct IN PRINCIPLE — unlike the cockpit-feed bug where ts was stamped from upstream (see memory/researcher/cockpit-closedloop-rootcause-2026-11-24.md). Caveat: it only validates a single file, so R1/R2 must be closed first; and builder/orchestrator skip fsync (durability gap, not freshness).

## Recommended close (one decision unblocks all 3 goals)
Pick ONE canonical path + schema, delete/relocate the other writer's target. Cheapest: keep **memory/ops/fleet-mode.json** as SSOT (orchestrator already declares it so + cockpit/dispatch read it); point builder/fleet_mode_writer.py `FLEET_MODE_FILE` and Verifier #1/#2 at that path; drop root file. Add a 1-line guard to each test: assert the path under test == canonical, fail loudly if not.

## 1-command verification for the owner
`python -c "import json,pathlib;[print(p,(json.loads(pathlib.Path(p).read_text())['goal_pct'], 'schema_version' in json.loads(pathlib.Path(p).read_text()))) for p in ['fleet-mode.json','memory/ops/fleet-mode.json']]"`
Expect two DIFFERENT goal_pct values = divergence confirmed live.
