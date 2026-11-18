Last updated: 2026-11-15 ~00:3x (daily health check + .gitignore allowlist audit, Verifier goals 1+3)

# Portal health check — 2026-11-15
| check | result | evidence |
|---|---|---|
| PID alive | OK | _portal_pid.txt = 36856; Get-Process start Sat 14 Nov 2026 21:26:25 |
| :8099 single listener | OK | Get-NetTCPConnection -LocalPort 8099 -State Listen count = 1 |
| /api/git reachable | OK | repo=true, changed=1 (pre-cleanup) |

## .gitignore allowlist audit (goal: tracked count ~43, flag drift)
DRIFT FOUND + FIXED this round:
- Tracked files were **430** (root 28 + memory/ 402) vs the ~43 baseline from the 2026-11-13 rollout.
- Breakdown: growth is ORGANIC memory/ tree (341 .md, 37 .py, 9 .json, 19 .html quarantine variants, scripts) — legitimate agent work product, not junk.
- JUNK found: **11 .pyc (__pycache__) + 3 .bak** tracked. Fixed: `git rm --cached` on all 14 (kept on disk) + `.gitignore` now carries `**/__pycache__/`, `*.pyc`, `*.bak` after the allowlist.
- New baseline post-fix: **416 tracked** (28 root + 388 memory). The "~43" number in goal text is stale — it predates per-agent memory/ growth; rule should read "no junk categories (.pyc/.bak/.log/.png) tracked; .md/.py/.json growth expected".
- Remote fleet cross-check (goal 2): BLOCKED this round — hosts .245/.39/.99 powered down by human 2026-11-15; /api/fleet shows them unreachable. Re-run when up.

## Memory-vs-ground-truth sweep (Researcher goal 4, same round)
All 4 concrete claims in MEMORY.md verified against live state: portal PID 36856 up; Qwen3.8-27B-Q8_0 resident on :8888; TODO.md top section is the current OPS CHECK; state-line JSON parses. **No stale entries found.**

## Reboot-runbook dry-run, WHITE leg (Mechanic goal 2 - steps verified without rebooting)
| step | check | result |
|---|---|---|
| PortalRun task exists | schtasks /query /tn PortalRun | OK |
| recover_all.py + .bat present & compile | py_compile | OK |
| reboot_launchers.py / reboot_recover.py present | allowlisted in .gitignore | OK |
| _portal_pid.txt current | matches live PID 36856 | OK |
| runbook doc carries post-reboot order | memory/ops/windows-runbook.md | OK (lifecycle + trap sections) |
Remote legs (.245/.39/.99): BLOCKED - powered down by human; dry-run when up.
