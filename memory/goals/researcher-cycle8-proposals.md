# Researcher - CYCLE-8 GOAL PROPOSALS (revised 2026-11-20, supersedes prior draft)

SUPERSEDES the earlier version of this file, whose grounding line ("core scripts ABSENT from
memory/researcher/") was WRONG for most entries. Verified ground truth this pass (os.path.exists):
  EXISTS: residency_matrix.py, kb_index.py, auto_research.py, evidence_quality.py (+_trend),
          sla_tracker.py, sla_audit.py, hot_load.py (40KB = the "unified loader"), chain_validator.py,
          crosscheck_pipeline.py, drift_check.py, source_scorer.py, understanding.py, validate_brief.py.
  ABSENT: model_bench.py, kg_integrity.py (only kg_integrity_bug_check.py exists).
So cycle-7 is genuinely mostly built; cycle-8 closes the two real gaps + takes the recurring
sandbox-egress live-leg wall as first-class work. Each goal names a file + acceptance test and is
tagged [SANDBOX] or [LIVE-LEG] (egress-blocked from this seat -> dispatchable to one non-sandbox White run).

1. **Benchmark Harness - build the missing model_bench.py** [SANDBOX] - Build memory/researcher/model_bench.py:
   5 standardized tasks (summarization, code-gen, extraction, classification, reasoning); records tokens/sec +
   quality score; --selftest runs against a mock/echo backend. Verified: script exists; `--selftest` exit 0;
   emits valid JSON with all fields for >=1 (mock) model. This unblocks goals #2 and cycle-7#5/#7.

2. **Cross-Host Model Comparison - close genuinely-open #7** [LIVE-LEG] - With #1 built, run the identical 5-task
   suite on one model present on >=2 hosts (Q4_K_S White+Red) via `python elev.py`; quantify latency delta +
   quality per host; write memory/researcher/cross-host-comparison.md. Verified: >=1 model x 2 hosts, all fields,
   explicit recommendation (which host for which workload). Acceptance was RE-OPENED by my content audit (the old
   closure cited retrieval_benchmark.py - wrong instrument); this is the real one.

3. **Live-Leg Dispatch Spec + Batch Runbook** [SANDBOX] - Consolidate the recurring sandbox-egress wall
   (WinError 10013, documented in memory/ops/blockers.md) into ONE memory/ops/live-leg-dispatch.md: inventory of
   ALL blocked live legs across agents (unified-loader LIVE, residency-matrix LIVE, Verifier perf-baseline, Mechanic
   daily load-probe) with the exact `python elev.py --shell "..."` command + evidence target for each. Verified: doc
   lists >=4 distinct blocked legs, each with exact command + evidence file; NO leg is re-probed from a sandbox seat.
   (Serves option-b workflow improvement; de-dupes the repeated NEEDS-HUMAN entries.)

4. **Evidence-Marker Content Audit - institutionalize** [SANDBOX] - Build memory/researcher/marker_audit.py: flags
   any (verified:) marker whose cited artifact does NOT actually exercise the acceptance claim (the false-positive
   class I caught on #7 cross-host). Verified: --selftest catches a planted fake marker; real run over all goal files
   emits JSON with 0 flags on known-good specific markers and >=1 flag on a vague "it works" stub.

5. **Residency Matrix LIVE leg** [LIVE-LEG] - Run residency_matrix.py live via elev.py on White to produce a REAL
   DRIFT matrix (not the UNREACHABLE sandbox fallback). Verified: memory/llm/residency-matrix.md has real per-host rows;
   a deliberately unloaded model shows as DRIFT; clean state = 0 drifts.

6. **Unified Loader LIVE execution** [LIVE-LEG] - Run hot_load.py via elev.py on White's LM Studio: load, alias probe,
   unload, confirm zero binding loss. Verified: hotload-log.jsonl gains LIVE LOAD_SUCCESS/UNLOAD_SUCCESS rows; agents.json
   byte-identical before/after; alias probe passes.

7. **SLA Daily Report - close the portal-emit gap** [SANDBOX] - Wire sla_tracker.py into a daily writer producing
   memory/ops/sla-report-YYYY-MM-DD.md with per-agent p95 pass/fail + trend vs prior day. Verified: today's report
   generated; a simulated >30s response is flagged FAIL; clean day = all PASS.

8. **KG Integrity Fix - close the to/target bug** [SANDBOX] - kg_integrity.py is ABSENT (only kg_integrity_bug_check.py
   exists). Build/patch memory/researcher/kg_integrity.py: read supersession target via `s.get("target")` (not "to") AND
   filter to path-like tokens before counting dangling refs. Verified: repro prints old vs new table; dangling_ref reflects
   REAL path targets only, not the naive over-count.

9. **Research Pipeline - citation-rot sweep** [SANDBOX] - Extend auto_research.py + validate_brief.py to detect citations
   that no longer resolve (files moved/archived); report rot across memory/researcher/briefs/. Verified: run flags each stale
   path; a fresh 'fleet VRAM management' brief has 100% resolving citations.

10. **Mirror-Revert Corpus Consolidation** [SANDBOX] - Synthesize the ~25 mirror-revert-*.md leaves into ONE canonical spec
    (root cause + fix + impact) at memory/researcher/mirror-revert-canonical.md. Verified: single doc cites all source leaves;
    each original leaf gets a superseded pointer back to it.

---
Summary: 7 [SANDBOX]-runnable goals (#1,3,4,7,8,9,10) + 3 [LIVE-LEG] goals (#2,5,6) that are all unblocked by ONE
non-sandbox White session running the commands in #3's runbook. Highest leverage: #1 (builds the missing harness) then #3
(batch-unblocks every agent's egress wall).