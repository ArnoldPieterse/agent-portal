# Goal 3 - API Contract Test Suite - Evidence (2026-11-20)

**Runner:** `memory/verifier/api_contracts.py` (full CLI: `--static`, `--negative`, `--live`)
**Contracts:** `memory/verifier/api-contracts/*.json` — 31 per-endpoint schemas + manifest.

## This pass (concrete step: completed the missing CLI runner)
Prior pass left `api_contracts.py` with `load_contracts()` / `validate()` / `negative_tests()`
but NO entry point, so `--static`/`--negative` produced no output. Added `main()` wiring all
three modes + a report writer (`api-contract-report-YYYY-MM-DD.md`).

## Verified from this seat (real runs)
- **STATIC: PASS** — 31/31 contract files well-formed (each has `/...` endpoint + usable
  schema: plain `type` or `oneOf`). Acceptance needs >=15 endpoints; 31 defined.
- **NEGATIVE (validator correctness): 5/5 PASS** — proves a simulated schema change is caught:
  valid response -> 0 errors; missing required key; wrong type; const violation; nested item.
- Syntax check (`ast.parse`) clean.

## Live leg — GATED (logged NEEDS-HUMAN, not re-probed)
`--live` returns exit 2 from this sandbox seat: portal :8099 unreachable (WinError 10013
egress wall). SAME class as Verifier #1 perf-gate baseline + Mechanic/Orchestrator live legs —
already documented in `memory/ops/blockers.md`. Runner degrades gracefully: static+negative
still valid, exit code distinguishes unreachable (2) from real contract failure (1).

## Acceptance criteria status
- [x] 15+ endpoints have contract tests (31 defined, statically validated)
- [x] A simulated schema change is caught (5/5 negative tests)
- [ ] Clean state passes all LIVE + per-endpoint pass/fail report — needs non-sandbox seat
      with :8099 egress: run `python memory/verifier/api_contracts.py --live` once.
