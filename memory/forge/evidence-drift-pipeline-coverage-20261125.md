# Evidence - drift_detect.py extended to fleet pipeline coverage (2026-11-25 11:31 UTC)

## Context (Fleet Autonomy Convergence)
Builder landed a schedulable wrapper pipeline for the 3 stealth workflows
(memory/builder/stealth/run_stealth_jobs.py + wf1/wf2/wf3). The gate previously
scanned ONLY memory/forge/*.py, so fleet-wide additions were invisible to drift
detection - exactly the silent-degradation class this gate exists to catch.

## Change (memory/forge/drift_detect.py)
1. STDLIB now derived from `sys.stdlib_module_names` (authoritative) with a
   curated fallback. Root cause of prior false-positive risk: the hardcoded set
   missed legitimate stdlib modules `resource` (run_stealth_jobs.py) and
   `statistics` (wf2_weekly_report.py), which would have reported phantom DRIFT.
2. scan_gate_scripts() now walks PIPELINE_DIRS = [memory/forge, memory/builder/stealth],
   keyed by repo-relative path.

## Verification (real commands, exit codes)
- `python memory/forge/drift_detect.py --simulate` -> RESULT ALL PASS (6/6), exit 0
- `python memory/forge/drift_detect.py` -> VERDICT CLEAN, exit 0
  Scripts scanned (9): consistency_check.py, convergence_gate.py, drift_detect.py,
  runbook_audit.py, stealth_smoke_gate.py, run_stealth_jobs.py, wf1_ar_followup.py,
  wf2_weekly_report.py, wf3_reminder_pipeline.py
- AST import audit of the 4 stealth scripts: all imports resolve to stdlib after
  fix (resource/statistics correctly classified); zero real third-party deps.

## Result
Gate now covers the whole fleet pipeline; no new unlisted deps and no orphaned
tests introduced by Builder's wrapper addition. Drift report appended to
memory/forge/drift-report.jsonl.
