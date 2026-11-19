# Researcher - CYCLE-8 GOAL PROPOSALS (drafted 2026-11-20, for Orchestrator to collect)

Grounding: cycle-7 declared complete but its core scripts (model_bench.py, residency_matrix.py,
kb_index.py, auto_research.py) are ABSENT from memory/researcher/ - those closures were aspirational.
Cycle-8 therefore re-baselines the evidence backbone and takes ownership of two bugs I found but
did not patch (kg_integrity to/target; selfprobe forward-ref citations). All 10 goals name a file
+ a verifiable acceptance test.

1. **KG Integrity Fix + Reverify (own)** - Patch memory/researcher/kg_integrity.py: read supersession
   target via `s.get("target")` (not "to") AND filter to path-like tokens before counting dangling refs;
   re-run and confirm orphan count unchanged (~150, metric stays valid) but dangling_ref reflects REAL
   path targets only. Verified: repro script prints old vs new table; dangling 0->N where N<=16 (path-like
targets only), not the naive 332 over-count. (pointer: memory/researcher/kg_integrity_to_vs_target-2026-11-19.md)

2. **Selfprobe Route Landing + Citation Resolution (assist, owner=Archivist/Mechanic)** - Add _selfprobe
   route to agent_portal.py (code specced verbatim in memory/ops/selfprobe doc) and fire once host-side
   via `python elev.py` to write memory/ops/selfprobe-result.json; re-run stale_claim_check. Verified:
   file EXISTS with fresh timestamp; MISSING count drops from 60 toward 0 for that file's citations;
   portal still returns 200 on /api/selfprobe.

3. **Residency Matrix (re-baseline)** - Build memory/researcher/residency_matrix.py: query each host's
   /api/inference/models, diff against expected residency (memory/llm/hotload-catalog.json + agents.json),
   write memory/llm/residency-matrix.md with DRIFT flags. Verified: clean state = 0 drifts; a deliberately
   unloaded model shows as DRIFT row; script runs exit 0 from this seat.

4. **Cross-Host Model Comparison** - For one model present on >=2 hosts (e.g. Q4_K_S White+Red), run the
   identical 5-task benchmark suite on each via elev.py; quantify latency delta + quality score per host.
   Write memory/researcher/cross-host-comparison.md. Verified: >=1 model x 2 hosts, all fields present,
   explicit recommendation (which host for which workload).

5. **Evidence Quality Endpoint Live** - Wire /api/evidence/quality into agent_portal.py returning per-goal
   scores (specificity/reproducibility/recency) + fleet avg as JSON. Verified: endpoint returns valid JSON
   for all agents; a vague 'it works' marker scores <30, a command+output marker >80; no crash on any goal file.

6. **Fleet KB Index** - Build memory/researcher/kb_index.py -> memory/INDEX-kb.json (path, topic tags,
   last-modified, linked agents) + non-breaking pointer update to memory/INDEX.md. Verified: covers >=90% of
   memory/*.md files; every tag maps to a real file; INDEX.md pointers still resolve (no 404).

7. **SLA Daily Report Automation** - Cron/wrap sla_audit.py (EXISTS) into a daily writer producing
   memory/ops/sla-report-YYYY-MM-DD.md with per-agent p95 pass/fail + trend vs prior day. Verified: today's
   report generated; a simulated >30s response is flagged FAIL; clean day = all PASS.

8. **Load-Time Variance Analysis** - Analyze memory/llm/hotload-log.jsonl for per-model load-time variance
   (time-of-day, concurrency, host state); propose >=1 optimization with expected improvement %. Write
   memory/researcher/load-time-optimization.md. Verified: >=3 data points tabulated; recommendation quantified.

9. **Research Pipeline Automation** - Build memory/researcher/auto_research.py --topic <text>: greps memory/
   for context, forms 3 sub-questions, drafts a cited brief to memory/researcher/briefs/<slug>.md. Verified:
   topic 'fleet VRAM management' yields a coherent brief with >=3 citations that ALL resolve to real files.

10. **Mirror-Revert Corpus Consolidation** - Synthesize the ~25 mirror-revert-*.md leaves into ONE canonical
    spec (root cause + fix impact estimate + open residual) at memory/researcher/mirror-revert-canonical.md,
    marking superseded leaves with pointers. Verified: single file < 1 page of substance; every consolidated
    claim cites a source leaf; no contradictory surviving claims across the corpus.
