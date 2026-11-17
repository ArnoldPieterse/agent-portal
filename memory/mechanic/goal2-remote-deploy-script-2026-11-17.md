# Goal #2 Progress: one-shot remote deploy script ready
Date: 2026-11-17 (Mechanic, auto-loop pass)

## Step taken
Wrote `memory/ops/deploy_boot_task_remotes.py` (5.4 KB, compiles clean):
- Single command from White non-sandbox admin session
- WinRM to Pale (.39) + Black (.99): copy scripts -> register ONSTART task -> verify
- Red excluded (powered off); add one line when back
- Results appended to boot-deploy-verify.jsonl

Updated `memory/ops/boot-detection-runbook.md` with the new one-shot section.

## Remaining for closure (unchanged)
- [ ] Run `python memory/ops/deploy_boot_task_remotes.py` from White non-sandbox admin session
- [ ] One real cold-boot test per remote (Pale + Black; Red when powered on)
- [ ] <60s power-on-to-portal-serving verified end-to-end

## Blocker (unchanged, not re-probing)
Sandbox blocks outbound sockets (WinError 10013). The one-shot script IS the unblock:
run it from any non-sandbox admin session on White. No multi-step manual process needed.
