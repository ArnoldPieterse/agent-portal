# Mechanic Open Goals Status - 2026-11-18

Ledger: 8/10 reached (80%). Two goals remain open, both time-gated or requiring out-of-sandbox execution.

## Still Open

### Goal 1: Keep portal :8099 up >=99% this week
- Type: Ongoing monitoring metric
- Closes: Week end with uptime tally
- Current status: No unplanned outage; 5 planned restarts each restored in ~10s (logged)
- Action needed: None until week-end tally

### Goal 3: Dry-run the reboot-recovery runbook once per machine this week
- Type: Requires admin + WinRM on all 4 hosts
- Blocker: Sandbox firewall (WinError 10013) blocks outbound TCP; COM objects unavailable for schtasks
- deploy_reboot_recovery_all.py --verify-only ran: White FAIL (COM not registered in sandbox), remotes unreachable
- Action needed: Run from White shell with elev.py: `python elev.py python memory/mechanic/deploy_reboot_recovery_all.py`
- Script ready: memory/mechanic/deploy_reboot_recovery_all.py (289 lines, idempotent, --verify-only safe)

## Completed This Pass
- net_probe.py upgraded: real host IPs from memory_mirror_hosts.json + --local flag for sandbox
- Evidence: memory/mechanic/net_probe_real_hosts_20261118-213151.md
- Hygiene check: MEMORY.md 35 lines (PASS), TODO.md top clean (PASS)
- Evidence: memory/mechanic/hygiene_check_20261118-213151.md
