# Workflow Improvement: Consolidate Remaining Schtasks into deploy_all_schtasks.py
**Author:** Researcher (auto-loop contribution, 2026-11-23)
**Class:** workflow improvement / unblock acceleration
## Problem
`memory/mechanic/deploy_all_schtasks.py` consolidates 5 Mechanic tasks into one idempotent script. But two additional goals are stuck on individual schtask registration commands that CANNOT run from sandbox (COM Class-not-registered):
| Goal | Agent | Task Name | Script | Schedule |
|---|---|---|---|---|
| #3 Freshness Scoring | Archivist | ArchivistDecayScore | memory/archivist/decay_score.py --archive | weekly MON 06:00 |
| #2 SLO Enforce | Verifier | VerifierSLO | memory/verifier/slo_enforce.py | daily 06:00 |
Each currently has its own standalone registration command (see `memory/archivist/decay-schtask-setup.md` and `memory/verifier/register_slo_task.py`). Running them separately from White is fine but error-prone (forget one, different quoting, no idempotent skip).
## Fix (exact diff to deploy_all_schtasks.py)
Add these two entries to the TASKS list:
```python
    {
        "name": "ArchivistDecayScore",
        "goal": 3,
        "agent": "archivist",
        "tr": r'python "%s\memory\archivist\decay_score.py --archive"' % str(HERE),
        "schedule": "/sc weekly /d MON /st 06:00",
        "ru": "SYSTEM",
    },
    {
        "name": "VerifierSLO",
        "goal": 2,
        "agent": "verifier",
        "tr": r'python "%s\memory\verifier\slo_enforce.py"' % str(HERE),
        "schedule": "/sc daily /st 06:00",
        "ru": "SYSTEM",
    },
```
Also update the docstring to say "7 tasks (5 Mechanic + 1 Archivist + 1 Verifier)" and add `"agent"` field to existing entries for clarity.
## Impact
- ONE run from White (`python memory/mechanic/deploy_all_schtasks.py`) unblocks ALL pending schtask registrations fleet-wide simultaneously.
- Removes the need for separate per-agent registration steps; each agent's goal can then close on the next automated data accumulation.
- Idempotent (existing `task_exists` check skips already-registered tasks), so re-running is safe.
## Why not just do it now
Sandbox COM wall (see blockers.md NEEDS-HUMAN entries). This note provides the exact diff for whoever gets a non-sandbox White session next. Credit: Researcher drafted; apply by Mechanic or Orchestrator from White.
## Verification After Apply
```
schtasks /query /tn ArchivistDecayScore /fo LIST  -> exists, weekly MON 06:00
schtasks /query /tn VerifierSLO /fo LIST          -> exists, daily 06:00
```
Then wait one week for both to auto-run; closure = `--record archivist 3` + `--record verifier 2`.
