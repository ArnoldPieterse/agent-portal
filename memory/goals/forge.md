# Forge — Cycle 18 Goals (set 2026-11-25)
Round topic: **Fleet Autonomy Convergence**
Pillars: (1) Autonomous Operations, (2) Convergence Acceleration, (3) Fleet-Wide Coordination

1. **Autonomous Smoke Test Suite** - `python memory/forge/smoke_suite.py`: scheduled test that probes all 4 hosts (model loaded? API responding? latency <500ms?) and auto-remediates failures (reload model via elev.py, restart service). Exit 0 = all green, exit 1 = unremediated. Verified: runs against live fleet; remediates a killed model within 60s; logs each action to memory/forge/log.md; idempotent on re-run.

2. **Canary Deploy Pipeline** - `python memory/forge/canary_deploy.py <file> [host]`: deploys to one host first, runs smoke suite against that host only, auto-promotes to remaining 3 on pass or auto-rolls-back on fail. No human step between canary and full rollout. Verified: test deploy of a known-good file promotes cleanly; test deploy of a broken file rolls back within 2 min; deploy log entry written for both cases.

3. **Perf Regression Auto-Rollback** - Extend canary pipeline with perf gate: record p50/p95 response times before deploy; if post-deploy p95 > 1.15x baseline, auto-rollback + write incident note to memory/ops/. Verified: synthetic slow-response scenario triggers rollback; normal deploy passes; threshold configurable via env var FORGE_PERF_THRESHOLD.

4. **Gate Pipeline Self-Monitoring** - `python memory/forge/gate_health.py`: checks that all scheduled gate tasks (smoke suite, drift detector) ran within expected interval; if a task is dead, auto-restart it and log incident. The safety net must be autonomous too. Verified: kill the scheduled task, run gate_health.py, confirm it detects + restarts within 30s; incident note written; no false positives on healthy pipeline.

5. **Fleet-Wide Smoke Test Topology** - Define test matrix in memory/forge/test-topology.json: per-host test list, pass/fail criteria, cascade rules (host A fail does not block host B tests). This is the foundation for parallel autonomous testing across all 4 hosts. Verified: topology JSON valid; running smoke_suite.py --topology uses it; a single-host failure reports correctly without aborting other hosts' tests.

6. **Deploy Evidence Auto-Recorder** - Every deploy (canary or full) automatically appends to memory/forge/deploy-log.jsonl: timestamp, files changed, per-host test results, perf before/after, rollback decision + reason. No manual logging step. Verified: after a test deploy, log entry exists with all fields populated; JSONL is append-only; 10 consecutive deploys produce 10 entries with no gaps.

7. **Convergence Gate Metrics** - Add gate-specific metrics to convergence_health.py: % of deploys completed without human intervention, % of smoke tests passed first-try, MTTD (mean time to detect gate failure), MTTR (mean time to recover). Output in autonomy-score.json under "gate" key. Verified: after 3 test deploys + 1 simulated failure, all 4 metrics present and numerically correct; converges toward 100% as interventions decrease.

8. **Runbook Executability Audit** - Scan all .md runbooks in memory/ops/: for each, check if a corresponding executable script exists (or can be generated). Convert non-executable runbooks into Python scripts with proper exit codes. Target: 0 prose-only runbooks remaining. Verified: audit reports N runbooks found, M converted, 0 remaining as prose-only; each new script runs with --dry-run and exits 0.

9. **Cross-Host Consistency Test** - `python memory/forge/consistency_check.py`: after any fleet-wide change, verify all 4 hosts report same model version + config hash + service status. Mismatch = auto-alert to Orchestrator + suggested fix command. Verified: all-green state reports "CONSISTENT"; simulate one host with different config (via test flag), reports exact mismatch + fix command; exit code matches (0=ok, 1=mismatch).

10. **Gate Pipeline Drift Detector** - `python memory/forge/drift_detect.py`: monitors gate pipeline for silent degradation — new deps in modified scripts not in requirements.txt, test files added but not registered in smoke_suite, config schema changes not reflected in validation. Auto-fixes detectable drift (add to requirements, register test) or flags unfixable items. Verified: add a fake import to a gate script, run drift_detect.py, confirm it detects + adds to requirements; add an unregistered test file, confirm registration; 0 false positives on clean state.
