# Evidence: convergence_watch.py (Fleet Autonomy Convergence)
Date: 2026-11-25T18:53Z

## What it does
State-transition watcher for the fleet convergence gate. Runs convergence_gate.py --json,
compares verdict to persisted last-state (.last_verdict), alerts ONLY on transitions.
Steady-state re-runs are silent (no alert fatigue). Alerts -> convergence-alerts.jsonl.

## Verification
- `python memory/forge/convergence_watch.py --selftest` -> ALL PASS (10/10)
- Live run 1 (after --reset): [watch:INFO] NONE -> CONVERGED, exit 0, alert written
- Live run 2: "[watch] CONVERGED (no change, steady)" — silent, no new alert line
- convergence-alerts.jsonl contains exactly 1 entry (the initial record)

## Transition matrix (severity / exit code)
| prev \ new | CONVERGED | DEGRADED | DIVERGED | ERROR |
|---|---|---|---|---|
| NONE | 0 (record) | 2 | 1 | 1 |
| CONVERGED | -1 (silent) | 2 | 1 | 1 |
| DEGRADED | 0 (recovery) | -1 (silent) | 1 | 1 |
| DIVERGED | 0 (recovery) | 0 (improved) | -1 (silent) | 1 |
| ERROR | 0 (recovery) | 0 (partial) | 1 | -1 (silent) |

## Integration
- Pairs with convergence_gate.py (runs it as subprocess)
- State file: memory/forge/.last_verdict (single-line verdict string)
- Alerts log: memory/forge/convergence-alerts.jsonl (append-only JSONL)
- Can be scheduled via schtasks for periodic monitoring without flooding logs

Artifact: memory/forge/convergence_watch.py
