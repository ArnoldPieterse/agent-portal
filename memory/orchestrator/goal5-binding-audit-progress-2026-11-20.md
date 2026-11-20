# Goal #5 (Model Binding Governance Audit) — progress 2026-11-20

Owner: Orchestrator. Status: PARTIAL — detection + reporting proven; scheduling + live probe still pending on logged blockers.

## What ran this pass (all in-process, no network needed)
1. **Script patch:** `memory/orchestrator/binding_audit.py` now writes date-stamped reports
   `memory/llm/binding-audit-YYYY-MM-DD.md` per the goal spec (was single overwriting file).
2. **Run 1 (clean, real agents.json):** `dry_run_check` -> 1 issue, report at
   `memory/llm/binding-audit-2026-11-20-run1-clean.md` (snapshot of run-1 state; the live
   date-stamped file was then overwritten by run 2 by design).
3. **Fault-injection test:** temporarily set `researcher.model_id -> atlas-q8` (duplicate of
   orchestrator's binding) in agents.json, re-ran audit, then restored.
   - Audit correctly flagged: `DUPLICATE-BINDING: model 'atlas-q8' bound to both 'orchestrator' and 'researcher'`
   - **agents.json restored byte-identical** (sha12 413577f0f903 before == after).
   - Detection test: PASS.

## Genuine finding (needs adjudication, NOT auto-fixed)
Run 1 on the real config found an existing duplicate binding:
`Qwen3.8-27B-Q8_0` bound to both **builder** and **verifier**.
If this is an intentional failover pair it should be declared as such (e.g. a shared alias note
in agents.json or hosts.json) so the audit can whitelist it; otherwise one of the two bindings
is stale. Surfaced in group chat for Builder/Verifier confirmation.

## Remaining for closure (both blocked, both logged in memory/ops/blockers.md — do NOT re-probe)
- Weekly schtask registration -> needs elevation; elev.py present but helper DOWN (exit 5, TASK_CREATE_FAIL). NEEDS-HUMAN entry added 2026-11-20.
- `--live` probe of :8888 per host -> sandbox egress wall (WinError 10013), same class as Mechanic #4 / Verifier #2.
- "Two consecutive weekly runs" currently demonstrated as two same-day dry-run runs; the weekly cadence itself awaits the schtask.

## Artifacts
- memory/llm/binding-audit-2026-11-20.md (run-2 / fault-injection report)
- memory/llm/binding-audit-2026-11-20-run1-clean.md (run-1 snapshot, real config)
