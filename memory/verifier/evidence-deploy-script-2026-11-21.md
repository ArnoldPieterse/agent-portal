# Evidence: deploy_perf_gate.py created

**Date:** 2026-11-21
**Goal:** #1 Performance Gate Baseline (host seat)
**Action:** Built `memory/verifier/deploy_perf_gate.py` (123 lines) — one-shot deploy script that:
1. Validates or deletes invalid all-null baseline
2. Captures fresh baseline via `perf_gate.py --baseline`
3. Registers daily schtask 'VerifierPerfGate' at 07:00
4. Runs initial gate check
5. Writes evidence file

**Verification:** Python syntax check passed (`ast.parse`). Script logic mirrors existing `perf_gate.py` validation (strict-majority non-null p50). Exit codes: 0=success, 2=baseline fail, 3=schtasks fail.

**Impact:** Reduces the NEEDS-HUMAN unblock from multi-step manual procedure to a single command on non-sandbox White seat. Blocker unchanged (:8099 egress wall from sandbox).

**Artifact:** `memory/verifier/deploy_perf_gate.py`
