# Goal #6 - dep-capture one-shot script built (2026-11-18)

Date: 2026-11-18 ~07:00 UTC
Agent: Mechanic (Red sandbox)

## What was done
Built `memory/ops/schtasks_dep_capture.py` (3.1 KB) - a one-shot wrapper that:
1. Runs `schtasks /query /fo CSV /v` to capture live task list
2. Calls `schtask_dep_gen.py` to parse + infer edges + diff vs previous week
3. Saves dated baseline to `memory/mechanic/dep-snapshots/week-N.csv` + `week-N-graph.json`
4. Prints summary with diff alerts

## Verification
- Syntax check: `py_compile` PASS (Python 3.13)
- Logic: delegates to already-tested schtask_dep_gen.py (synthetic tests PASS 2026-11-18)
- Cannot execute from this sandbox (COM "Class not registered" for schtasks - recorded in blockers.md)

## Remaining for closure
- Run `python memory/ops/schtasks_dep_capture.py --week 1` from White non-sandbox seat -> produces first baseline
- Wait 7 days, run `--week 2` -> produces second baseline + diff
- Verify one test task addition is correctly flagged (add a dummy schtask on White between weeks)

## Runbook note
From White ops terminal: `python memory/ops/schtasks_dep_capture.py --week 1`. Repeat weekly. The script auto-diffs against the previous week's CSV if present.
