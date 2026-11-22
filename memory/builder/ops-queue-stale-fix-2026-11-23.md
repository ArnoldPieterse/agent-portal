# Non-Sandbox Queue Stale Fix (Builder team-contrib, 2026-11-23)

**What:** `memory/ops/non-sandbox-queue.md` listed only 4 task names for `deploy_all_schtasks.py`
(PortalLoadProbe, MirrorHeal, FleetBootRecovery, LogRotateDaily). Source file actually registers
7 tasks (added: BootRecoverDetect [renamed from FleetBootRecovery], ChaosDrillMonthly,
ArchivistDecayWeekly, VerifierSLO).

**Fix:** Updated the one-command batch description to list all 7 by exact name.

**Why it matters:** A non-sandbox seat executing `unblock_all.py` now knows exactly what to expect
in the output and can cross-check each task in the post-deploy verification step.

**Artifact:** memory/ops/non-sandbox-queue.md (line ~19, ONE-COMMAND BATCH section).