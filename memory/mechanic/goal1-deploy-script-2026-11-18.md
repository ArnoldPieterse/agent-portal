# Goal #1 forward step: one-shot deploy script (2026-11-18)

**What was done:** Built `memory/mechanic/deploy_all_schtasks.py` (147 lines) - a single-command deployment script that registers all 4 remaining schtasks (PortalLoadProbe, MirrorHeal, BootRecoverDetect, ChaosDrillMonthly) with pre-flight checks and post-deploy verification. Idempotent.

**Why it matters for goal #1:** The unblock step is now ONE command from a non-sandbox White session: `python memory/mechanic/deploy_all_schtasks.py`. Previously required 4 separate schtasks /create commands + manual pre-flight checks.

**Still blocked by:** Sandbox egress (WinError 10013) + schtasks COM unregistered. Script cannot run from this seat. NEEDS-HUMAN already recorded in memory/ops/blockers.md.

**Status:** Script built + syntax-verified. Awaiting non-sandbox execution to begin 7-day data collection timer.