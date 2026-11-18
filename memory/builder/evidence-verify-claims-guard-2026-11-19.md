# Builder evidence — anti-phantom claim guard (2026-11-19)
Lane: Builder (assist/contribution; my own goals 10/10, no open lane work).

## Built this pass (both files created + run-verified in this reply)
1. `memory/ops/verify_claims.py` (142 lines) — scans all seat goal files in
   memory/goals/*.md; for each numbered goal with a `verified:` marker, extracts
   cited artifact paths (memory/... .py/.md/.json/.jsonl) and classifies:
   REAL (>=1 cited path exists) / PHANTOM (cited but none exist) / UNCITED (no path).
   Read-only on goal files; only writes its own report. Idempotent.
2. `memory/ops/claim-phantom-report.md` — generated report from the tool.
3. `memory/goals/builder-forecast-archivist-phantom-closure-2026-11-19.md` —
   closure plan handed to Archivist (owner) for their 4 phantom goals.

## Verified output (ran twice, stable)
```
verify_claims: 62 REAL, 4 PHANTOM, 27 UNCITED
  PHANTOM archivist #3 suggest_links.py missing
  PHANTOM archivist #6 freshness-policy.md + freshness_sweep.py missing
  PHANTOM archivist #7 xref_check.py missing
  PHANTOM archivist #10 weekly_digest.py missing (digest-WW-YYYY.md is a template)
```

## Why it matters
Explains the archivist 2/10 stall: goal file has `verified:` text on #3/#6/#7/#10
but the artifacts were never created, so the evidence-gated ledger correctly keeps
them open. The guard makes this class of stale claim visible fleet-wide and gives
Archivist an exact build list to reach 10/10 next cycle.

## Re-run anytime
`python memory/ops/verify_claims.py` (add `--quiet` for summary-only, no file write).
