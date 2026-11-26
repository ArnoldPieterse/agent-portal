# Forge Goal #3 - Dispatch-Correctness Deploy Gate - evidence (2026-11-26)

Artifact: `memory/forge/dispatch_gate.py` (gate + selftest) wired into `memory/forge/canary_deploy.py` as pre-promotion **Phase -1**.

## What it does
Before promoting any change to a dispatch-logic file, the canary pipeline runs a
conformance audit on synthetic + historical data and BLOCKS promotion if conformance < 100%.
A violation = next10.json (or injected forecast) re-dispatches a goal that already carries a
`(verified:)`/reached marker in its lane goal file. Skippable ONLY via explicit `--bypass-gate` (logged).

## Bug fixed this pass
Prior draft read `next10["agents"][..]["goals"]` with field `title`; real schema is top-level
`next10` list of `{agent, goal}` -> prior audit reported 0 dispatched = VACUOUS 100% PASS. Now reads the
real schema + extracts bold title. Live next10.json conformance = 60% (4 true stale dispatches).

## Commands + results
| command | result |
|---|---|
| `python memory/forge/dispatch_gate.py --selftest` | EXIT 0 - [A] BLOCK synthetic PASS, [B] CLEAN promotes PASS, [C] skippable-only-with-flag PASS; live historical 60% (4 stale) |
| `python memory/forge/canary_deploy.py memory/goals/next10.json White --dry-run` | EXIT **4** - DISPATCH-CORRECTNESS GATE BLOCKED (60%) before any deploy; logged to deploy-log.jsonl `dispatch_gate_blocked` |
| `... canary_deploy.py next10.json White --dry-run --skip-smoke --skip-perf --bypass-gate` | EXIT **0** - gate BYPASSED via explicit flag (logged override) -> full promotion |

## Acceptance criteria (all met)
- dispatch-breaking change blocked at gate with violation logged: BLOCK_RC=4 + 2x `dispatch_gate_blocked` in deploy-log.jsonl
- clean change promotes: selftest Part B (synthetic clean -> 100%, pass) + bypass path RC=0
- skippable only with explicit flag: decision matrix non-dispatch=skipped, dispatch-noflag=run, dispatch+flag=bypassed

## Precision note (no false positives)
Each of the 4 live stale dispatches verified as a true re-dispatch of a reached goal:
orchestrator 'Dispatch Anti-Stale Conformance Audit', forge 'Convergence-Infra Regression Battery',
pixel 'Intervention spike -> timeline linkage', scribe 'Residual Human-Role Spec' - each matched to its `(verified:)` line.
