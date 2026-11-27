# Assist: Stealth Workflow Hosting — Schedulable Job Runner
Date: 2026-11-25
Owner: Builder (assist to Mechanic goal "Stealth workflow hosting")

## What was built
- `memory/builder/stealth/run_stealth_jobs.py` — scheduler wrapper with resource budget (256MB RSS, 120s wall-clock), JSONL logging, exit codes (0/1/2/3)
- `memory/builder/stealth/schtasks_spec.md` — exact schtasks commands for fleet deployment with staggering + rollback

## Verification
- Selftest: 5/5 PASS (module load, log write, timeout mechanism, input-missing, exit code mapping)
- E2E: wf1_ar_followup runs through runner with real invoice data → correct tiered output written to file
- Resource budget: MAX_WALL_SEC=120 enforced via threading.Timer (Windows) or SIGALRM (Linux)
- No network calls in wrapper or any wf module (offline-only confirmed by inspection)

## Handoff to Mechanic
Mechanic can now run the schtasks commands from `schtasks_spec.md` directly. The runner is drop-in: point `--input-dir` at client data, schedule per spec.
