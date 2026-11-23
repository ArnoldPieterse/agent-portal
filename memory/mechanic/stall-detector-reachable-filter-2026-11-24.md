# Stall Detector: Reachable-But-Idle Filter (2026-11-24)

## Problem
Hot-note: "Stall detector must target only reachable-but-idle; down_streak already
covers unreachable — avoid duplicate alerts/feedback loop."

The original `stall_detector.py` flagged ANY agent with no lane file changes across
N passes. If an agent's seat is unreachable (e.g., Designer=unreachable, Researcher=not_loaded),
its lane won't advance -> false-positive stall alert that duplicates down_streak.

## Fix
Patched `memory/verifier/stall_detector.py`:
1. New `load_unreachable()` reads `memory/ops/unreachable_agents.json` (auto-loop populates per pass)
2. `detect_stalls()` accepts `exclude=set()` param; excluded agents get `{"excluded": true, "reason": "unreachable (down_streak covers)"}` instead of a stall flag
3. CLI: `--unreachable designer,researcher` for manual override; auto-reads JSON file if omitted
4. `--check` output now includes `excluded_unreachable` map

## Verification
`python memory/verifier/stall_detector.py --selftest` -> **7/7 PASS** (was 5, added 2):
- "unreachable agent excluded from stall flags" — stalled lane + exclude set -> excluded=True, stalled=False
- "active agents still detected with exclusion active" — other lanes unaffected

## Runbook one-liner
Stall detector now skips unreachable seats (reads `ops/unreachable_agents.json` or `--unreachable` flag); only reachable-but-idle agents trigger alerts. Prevents duplicate down_streak + stall feedback loop.
