# Evidence — Convergence Regression Auto-Remediation Dispatcher (Builder goal #8)
Date: 2026-11-26T11:45:48Z

## What ran
`python memory/builder/regression_dispatcher.py selftest` -> PASS (exit 0).
`--run` on live fleet -> action=idle (safe no-op; FSM=CONVERGING, no open remediation);
live `memory/ops/fleet-mode.json` timestamp unchanged before/after.

## Artifact
- memory/builder/regression_dispatcher.py — detect->act loop:
  - reads FSM state via convergence_fsm.ConvergenceFSM (no bypass)
  - on REGRESSING: picks lane via deterministic cause->lane map, opens EXACTLY ONE
    remediation goal line into memory/goals/<lane>.md, records OPEN in
    memory/builder/remediation-tracker.jsonl (append-only SSOT)
  - idempotent: an already-open remediation is never duplicated; close-twice = no-op
  - on closure (FSM leaves REGRESSING to a recovered state, or --close): stamps the
    goal line [REACHED] and flips FSM REGRESSING -> RECONVERGING -> CONVERGING (both legal)

## Acceptance criteria met
1. Seeded regression auto-opens exactly one remediation goal in the correct lane within 1 pass
   -> selftest step 1: cause 'vram oom on host pale' routed to mechanic, 3rd goal appended, 1 OPEN record.
2. Repeated detection opens no duplicate
   -> selftest step 2: second dispatch = no-op-already-open; goal count stays 3; tracker still 1 open.
3. Remediation closure flips the FSM back to CONVERGING/STEADY-STATE
   -> selftest step 3: --close stamped [REACHED] on the goal line + FSM ended at CONVERGING; 1 CLOSE record.

## Extras covered by selftest
- re-open after recovery uses a fresh unique id (no stale-id reuse)
- cause->lane map determinism (oom->mechanic, dispatch->orchestrator, ui->designer, canary->forge, ''->orchestrator default)
- idle path writes nothing when not REGRESSING and no open remediation
