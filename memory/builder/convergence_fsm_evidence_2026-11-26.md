# Evidence — Builder Goal 1 (Cycle 20): Convergence State-Machine SSOT
Date: 2026-11-26T09:34Z · Status: **REACHED**

Artifact: `memory/builder/convergence_fsm.py` (new) — authoritative FSM for the convergence
lifecycle, distinct from fleet_mode_writer.py (which only writes WORK/MAINTENANCE/IDLE atomically).

## States + legal-transition table
DISCOVERING -> CONVERGING -> STEADY_STATE <-> REGRESSING -> RECONVERGING (self-loops legal).
`LEGAL` dict defines 15 edges; `is_legal(src,dst)` / `legal_targets(state)` are the single check.

## Integration (no bypass)
- `fleet_mode_writer.write_mode()` -> `_ensure_fsm_stamped()`: every atomic mode write now carries
  `fsm_state` + `fsm_validated:true`; respects an already-validated payload (no override/loop).
- `orchestrator/fleet_mode.py` main(): after the atomic write, derives lifecycle state from
  goal_pct/mode and emits through ConvergenceFSM (illegal moves auto-rejected+logged); prev fsm_state
  is preserved into result so it persists across runs.
- `autonomy_regression_gate.log_regression()`: a detected regression emits a REGRESSING transition.

## Verification (all 3 acceptance criteria met)
1. **Unit tests** — `python memory/builder/convergence_fsm.py selftest` =>
   `FSM SELFTEST PASS: 15 legal transitions accepted, illegal rejected+logged, fleet-mode.json stamped fsm_state+fsm_validated`
   (temp files; live state untouched by test).
2. **fleet-mode.json carries fsm_state + fsm_validated:true** — live `memory/ops/fleet-mode.json` now
   shows `fsm_state: CONVERGING`, `fsm_validated: true`; verified it persists across two consecutive
   controller runs (CONVERGING->CONVERGING legal self-loop, not reset).
3. **grep: every mode/sentinel writer imports the FSM** — builder atomic writer, orchestrator
   controller, regression sentinel all reference `convergence_fsm` / `ConvergenceFSM`. No bypass.

## Side findings (out of scope for this goal; noted, not chased)
- Pre-existing bug: `autonomy_regression_gate.py` module-level `FLEET_MODE = ROOT/"fleet-mode.json"`
  is off-by-one (points at <root>/fleet-mode.json, not memory/ops). My FSM emit uses the correct ops
  path. Gate selftests 1-5 PASS; test6 fails on a pre-existing missing reference in pre_commit_gate.py.

## fsm-events.jsonl log format
{ts, from, to, legal, reason, source} — append-only at memory/ops/fsm-events.jsonl.
