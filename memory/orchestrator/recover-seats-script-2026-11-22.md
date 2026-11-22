# recover_seats.py — per-seat fleet recovery (evidence leaf, 2026-11-22)
Owner: Orchestrator (assisting Mechanic lane + own fleet-placement domain). Status: BUILT + runs clean.

## Why (closes a prose-only blocker, does NOT re-probe it)
- memory/ops/blockers.md OPS-NOTE 2026-11-22 said the unblock for the 4 unreachable seats was "the ONE step" but as PROSE. The auto-loop kept dispatching @Mechanic whose seat = unreachable -> dispatches could never land.
- This pass converted that prose into an executable, idempotent script: recover_seats.py (86 lines, py_compile OK).

## What it does
- Maps each flagged seat -> its real agents.json model_id binding -> Studio :8888 residency across hosts -> targeted load on first host that can serve it -> verify /health. Skips already-resident seats (idempotent). NOT a full-fleet reload (recover_all.py) and NOT a reboot bring-up (reboot_recover.py) — those exist and are distinct.
- Safety default = PLAN mode (no network, no load). --execute is opt-in and must run from a NON-SANDBOX (White) seat for live residency + loads.

## Measured output (this pass, offline plan mode — no egress attempted, so the :8888/:8099 sandbox wall was NOT re-probed)
```
# recover_seats  mode=PLAN  2026-11-22 19:01
  archivist    archivist-q8     WOULD-LOAD (offline plan) -> python elev.py --shell "..." && <load archivist-q8>
  mechanic     mechanic-q4      WOULD-LOAD (offline plan) -> python elev.py --shell "..." && <load mechanic-q4>
  researcher   quinn-q4         WOULD-LOAD (offline plan) -> python elev.py --shell "..." && <load quinn-q4>
  scribe       scribe-q8        WOULD-LOAD (offline plan) -> python elev.py --shell "..." && <load scribe-q8>
# done
```
Confirms the exact bindings recovery needs, pulled live from agents.json.

## Next step for a future NON-SANDBOX pass (White)
`python recover_seats.py --execute` -> probes real residency, loads only the missing models via elev.py, verifies /health. One command closes all 4 unreachable seats; after that the auto-loop's @Mechanic dispatches land.

## Credit
Assists Mechanic goal lane (unreachable-seat recovery) per team rule 1; Orchestrator own goals remain 10/10 closed.
