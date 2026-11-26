# Evidence - Convergence-Plateau Detection Gate (Forge goal #9) — 2026-11-26

**Command:** `python memory/forge/plateau_gate.py` → **EXIT 0, status PASS** (deterministic across runs).
Drives the REAL `memory/orchestrator/convergence_asymptote.py` module (no reimplementation).

## Part A - state classification (real ca.fit_asymptote + ca.determine_state)
- T1 synthetic plateau series  → **PLATEAU** (converged)  [fit_A≈85, latest in flat region]
- T2 synthetic climb series     → **CLIMBING** (NOT converged) [early slow-saturating curve]
- T3 boundary                   → within PLATEAU_THRESHOLD(2.0) of fitted A => PLATEAU; shifted past it => CLIMBING

## Part B - frequency-reduction safety invariant (the NEW requirement)
When state==PLATEAU the fleet drops to a reduced cadence (dispatch budget B < N open goals).
Invariant: a FAIR reduced cadence must not starve any open goal; a naive static top-B one will.
Ran on **REAL data - 65 open goals** extracted from `memory/goals/<agent>.md` (numbered lines w/o verified marker):
- B.1 SAFE: fair round-robin, budget=32 of 65, fairness window=4 cycles → **starved=[]** (no open goal missed).
- B.2 UNSAFE injection: static top-32 scheduler → indices 32..64 (33 goals) never dispatched;
  the hidden low-priority goal at idx 32 is **flagged as a safety violation** by the gate.
- B.3 coupling: CLIMBING→full cadence (budget=65, no starvation) vs PLATEAU→reduced (budget=32,
  fairness enforced); verdict is a genuine function of state (state_dependent=True).

## Artifacts
- `memory/forge/plateau_gate.py` (gate)
- `memory/forge/plateau_gate_last.json` (machine-readable checks)
- `memory/forge/plateau-gate-report.md` (human report)
