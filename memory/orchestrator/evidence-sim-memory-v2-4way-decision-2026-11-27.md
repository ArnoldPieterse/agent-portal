# Evidence: SIM Memory v2 — 4-way Decision + Context Tracking (Orchestrator, 2026-11-27)

## What was done
Upgraded `memory/ops/sim_memory.py` from a 3-value hint system to the paper's full
4-way decision taxonomy (RETAIN / REVISE / REPLACE / REMOVE) with confidence scoring
and environment context tracking.

## Changes (arXiv:2611.18856 §3.2 applied to fleet ops)
1. **Context field** — each attempt now records `context` (e.g. `"cycle=77;seats_down=Mechanic"`),
   enabling detection when the same root-cause recurs under different fleet conditions.
2. **4-way classify()** — returns `(decision, confidence)`:
   - RETAIN: fix worked + context stable → reuse as-is
   - REVISE: mixed results OR context shifted → re-verify before reuse
   - REPLACE: repeated failures → try fundamentally different approach
   - REMOVE: single regression with no prior success → drop mechanism
3. **Prediction accuracy** — report computes hit-rate across all attempts; context shift discounts confidence by 30%.
4. **Action summary** — groups entries by decision for at-a-glance next-step planning.

## Verification
- selftest: 7/7 PASS (new tests cover context-shift downgrade, REPLACE on repeated regression, REMOVE on single regression)
- Report on real data (4 entries): correct decisions + 75% prediction accuracy shown
- No breaking changes to existing `sim_entries.json` schema (context is optional/additive)

## Relevance to Fleet Autonomy Convergence
As fleet configuration shifts (seats down/up, cycle advances), SIM v2 immediately flags
which past fixes need re-validation rather than being blindly reused or forgotten.
This reduces the "re-diagnose from scratch" cost that slows convergence.

## Artifact
- `memory/ops/sim_memory.py` (upgraded in-place)
- `memory/ops/sim_entries.json` (unchanged schema, context field additive)
