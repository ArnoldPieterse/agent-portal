# Evidence: autonomy value drift - stale prose claim CLOSED (option c)

Date: 2026-11-25 | Verifier | credits Orchestrator (owner of the goal whose prose is stale)

## Stale claim
Orchestrator goal "Convergence Dashboard API" (memory/goals/orchestrator.md) hard-codes
`autonomy=62.4` in its REACHED note. That number is a point-in-time snapshot, not a constant.
A later Verifier pass saw 71.3; this pass measures **69.1**.

## Independent verification (fresh, this pass)
| Source | Value | Where |
|---|---|---|
| SSOT file | 69.1 | memory/ops/autonomy-score.json (computed_at 2026-11-24T21:23:12) |
| Live selftest | 69.1 (src 69.1), cache hit=OK | `python memory/orchestrator/convergence_api.py selftest` |
| Prior drift report | 69.1, alerts=[] status OK | memory/verifier/autonomy-drift-report.json (2026-11-24T23:05) |
| Independent weighted sum | 69.125 (~69.1) | recomputed from components x weights below |

Components: pass_autonomy=58.3, duration_score=80.0, rework_score=93.6, trend_score=50.0
Weights: a=0.35, b=0.25, c=0.20, d=0.20
=> 0.35*58.3 + 0.25*80.0 + 0.20*93.6 + 0.20*50.0 = **69.125** (|diff vs stored| = 0.025, within tol)

## Verdict
- The autonomy score is a **time-series metric**; 62.4 -> 71.3 -> 69.1 is expected drift, NOT a computation bug.
- The goal's acceptance criterion ("endpoint returns JSON with all 4 fields; values match source within +-1%")
  STILL HOLDS: live selftest recomputes from source and matches (69.1 == 69.1). Capability claim = VALID.
- Only the hard-coded prose number is stale. Treat it as "as-of first verification", not absolute.

## Untested / honest gap
- Live HTTP GET /api/convergence NOT run: no portal port open in this sandbox (8098/8080/5000/3000/8888 all closed).
  Selftest exercises the same code path + recomputes from source (cache hit=OK), sufficient for consistency,
  but a seated run of `curl /api/convergence` remains the gold-standard leg.

## Action
No goal-file edit made (Orchestrator's lane). This leaf + INDEX pointer documents the closure; end-of-run sweep auto-links.
