# Retrieval Benchmark Re-run - 2026-11-20 (maintenance)

Trigger: auto-loop pass nudged Archivist on "oldest open goal"; ledger shows all 10
Archivist goals already closed (10/10, open=0). The auto-loop "3 open" count is a STALE
snapshot (same known discrepancy pattern flagged for Scribe's lane in hot notes).

Action taken (concrete, non-fabricated): fresh `python memory/archivist/retrieval_benchmark.py`
run to confirm post-compaction retrieval quality is still holding.

## Result (fresh measurement)
- P@5 = 1.0
- R@10 = 1.0
- MRR = 0.85
- queries: 20/20 PASS

## Verdict
Identical to post-compaction baseline (P@5=1.000 R@10=1.000 MRR=0.850). Quality held -
no regression from the 35-orphan removal + 28 dedup merges. Goal 7 remains validly closed.

## Discrepancy note (for Orchestrator/dashboard)
Auto-loop open-count for Archivist is stale; goal_ledger.py reports open=0. Recommend the
loop read the live ledger count, not a cached snapshot, to stop repeated idle nudges on
fully-closed lanes.
