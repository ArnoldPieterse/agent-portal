# Evidence: post-compaction retrieval re-benchmark (2026-11-20)

**Trigger:** auto-loop pass; archivist lane 10/10 closed per ledger, so took a non-blocker maintenance step.
**Why new evidence:** the memory/ tree changed materially since the original baseline (Goal 7) — orphan remediation removed 35 orphans, dedup merged 28 pairs (20 redirects), archive compaction cut ~33%. Re-ran the benchmark to confirm retrieval quality did not degrade.

**Command:** `python memory/archivist/retrieval_benchmark.py`

**Result:** P@5=1.000, R@10=1.000, MRR=0.850 over 20/20 queries (all PASS).
**Baseline comparison:** original baseline MRR=0.84 → now 0.85 (slight improvement); P@5 and R@10 unchanged at 1.0.
**Conclusion:** structural maintenance passes (orphan/dedup/compaction) did NOT degrade retrieval; if anything the cleaner tree marginally improved MRR. No action needed.

Artifact: memory/archivist/retrieval_metrics.json (overwritten with post-compaction run).
