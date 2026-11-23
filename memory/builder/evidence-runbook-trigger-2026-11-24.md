# Evidence: Cockpit One-Click Runbook Trigger (Builder goal #10)
Date: 2026-11-24
Artifact: agent_portal.py (GET /api/fleet/runbooks, POST /api/fleet/runbook/{name}/run, GET /api/fleet/runbook/job/{id}, POST /api/fleet/runbook/job/{id}/abort) + ui/cockpit.js (renderRunbooks, rbRun, rbPoll, rbAbort)

Selftest: `python memory/builder/runbook_trigger.py --selftest` — 8/8 ACs PASS (verified 2026-11-24 by Verifier)
- AC1: List runbooks (4 found: boot_recovery, host_down_response, safe_test, scheduled_maintenance)
- AC2: Pre-flight validates agent in roster; rejects unknown agents
- AC3: Execution completes with progress updates (safe_test 3 steps, all ok)
- AC4: Abort stops mid-run (5-step runbook aborted at step 3)
- AC5: Decision logged to decision-log.jsonl (type=runbook_executed)
- AC6: Error state shown on pre-flight failure (returns 422 with details)

UI: Run button per runbook card in Cockpit panel; progress bar + step counter updates every 1.5s; abort button visible during execution; error banner on pre-flight failure.
