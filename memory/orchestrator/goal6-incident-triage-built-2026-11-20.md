# Goal #6 Fleet Incident Auto-Triage — BUILT + acceptance-verified 2026-11-20

**Artifact:** `memory/orchestrator/incident_triage.py` (scan + triage + resolve + simulate).
**Incident output dir:** `memory/ops/incidents/` (7 files this pass: 5 real watchdog-derived portal_down by date, 2 synthetic acceptance-test).

## What it does
- Scans `memory/ops/watchdog.log` for DOWN events and `agents.json` for missing model bindings.
- Writes structured incident records `memory/ops/incidents/YYYY-MM-DD-<agent>-<event>.md` with: ID, Detected (UTC ts), Source, Classification, Severity, Action Taken, Assigned To, Status, Detail, Resolution checklist.
- Dedupes by md5(line) in `.incident_triage_state.json`; re-detected signals append a "Re-detected" block instead of duplicating the file.
- `--resolve <stem>` flips Status OPEN->RESOLVED(ts) and checks all resolution boxes (recovery path).
- `--simulate <event_type> [agent]` injects a synthetic incident for acceptance testing (no network/elevation needed).

## Bug fixed this pass
`assign_recovery()` had a dead-code line `if "agent" in classify.__code__.co_varnames:` (always True) that made every non-WinRM case return "Orchestrator", shadowing the intended infrastructure->Mechanic default. Rewrote to take `category`: WinRM/reboot->Mechanic, agent-category->Orchestrator, infra/default->Mechanic.

## Acceptance test (all 3 criteria PASS, run this pass)
1. **Simulated wedge -> correct incident file:** `--simulate wedged researcher` -> `2026-11-20-researcher-wedged.md`, severity=medium, assignee=Orchestrator.
2. **Mechanic assignment line present (WinRM reboot):** `--simulate host_down black` -> action="WinRM reboot + verify services", `- **Assigned To:** Mechanic`.
3. **Resolution updates on recovery:** `--resolve researcher-wedged` -> `- **Status:** RESOLVED (2026-11-20T12:47:54Z)` + boxes checked.

## Real-scan run (no network)
`python memory/orchestrator/incident_triage.py` detected 12 new portal_down events across 2026-11-16..20 from the live watchdog.log and wrote them to incidents/ (idempotent on re-run via state dedupe).

**Residual (non-blocking, NOT a closure gate):** wiring this into a recurring schtask + auto-pickup by Mechanic is a host-seat leg; logic + acceptance are fully verified in-sandbox. Goal #6's stated acceptance test is met.
