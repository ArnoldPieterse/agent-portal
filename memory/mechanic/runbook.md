# Fleet Incident Response Runbook
Owner: Mechanic | Created 2026-11-20 (cycle-7 goal 9, Builder-assisted) | Covers top-5 incident types.
Each runbook follows **detect -> diagnose -> fix -> verify -> post-mortem**. Post-mortems use `memory/mechanic/postmortem_template.md` (fill all fields; file as `memory/mechanic/postmortem-<date>-<incident>.md`). Hosts: White (portal + memory root), Red, Pale, Black (LLM hosts).

## 1. Host Down (any host unresponsive)
**Detect** - `python memory/mechanic/health_check.py` reports host offline; `/api/fleet` shows red node; `net_probe.py` ping timeout on all 5 samples. Watchdog alert if >2 consecutive failures.
**Diagnose** - 1) Ping + WinRM: `python memory/mechanic/winrm_sspi_client.py <host> "hostname"` (3 attempts, exponential backoff). 2) If WinRM fails but ping succeeds -> service-level failure (WinRM service stopped / firewall). 3) If ping fails -> power/network: check physical/remote console. 4) Check `memory/mechanic/backups/` for last successful backup timestamp to bound data-loss window.
**Fix** - Power-cycle via remote management (or physically). On boot, scheduled tasks self-heal: PortalRun (White), boot-detection + fleet-reload tasks (see `memory/ops/boot-deployment-runbook.md`). If WinRM-only failure: `winrm quickconfig` on the host, restart WinRM service. Then run `python memory/mechanic/reboot_recover.py <host>` to re-verify services.
**Verify** - `health_check.py` shows host green; `/api/fleet` node back to green within 60s; LLM alias responds (portal `/api/agents` model_ids); mirror cycle completes without error (`memory/memory_mirror.log` tail clean).
**Post-mortem** - Fill template: impact (which agents lost seats), root cause (power/service/network), detection method, time-to-recovery. Add preventive action to `memory/mechanic/recovery-matrix.md` if a new failure mode appeared.

## 2. Model Wedged (LM Studio instance unresponsive / VRAM leak)
**Detect** - Portal proxy `/v1/models` times out for one host's instances; LLM latency p95 in `memory/mechanic/perf-profile.json` spikes >2x baseline; hotload-log.jsonl shows repeated load failures for that model_id.
**Diagnose** - 1) On the host: check VRAM (task manager / nvidia-smi equivalent) - sustained >90% with no active inference = leak. 2) Check LM Studio process state (hung vs crashed). 3) Check `memory/llm/instances.md` for the instance's expected port and model path; verify model files present (not reverted by mirror).
**Fix** - Kill the wedged LM Studio process; restart the instance on its registered port. If VRAM does not release, reboot the host (runbook 1). If model file missing/corrupt: restore from `memory/mechanic/backups/` or re-download; re-register in `agents.json` model_id mapping. Then trigger a hotload pass so the portal re-binds aliases.
**Verify** - `/v1/models` via portal returns the instance's models; one test completion call succeeds with sane latency (<2x baseline); next health_check cycle green; no new load failures in hotload-log.jsonl over 15 min.
**Post-mortem** - Record which model/host, leak vs crash, whether revert-sentinel (`revert_sentinel.py`) was implicated. If recurring for one model: flag the model in `memory/llm/instances.md` with a known-issue note.

## 3. Portal Crash (agent_portal.py down, port 8099 dead)
**Detect** - `portal_watchdog.py` alert; `/api/goals` connection refused; chat UI shows "connection lost" toast; watchdog log line in portal_run_err.log.
**Diagnose** - 1) `netstat -ano | findstr :8099` -> LISTENING or not. 2) Read tail of `portal_run_err.log`: unhandled exception (bug), OOM, or clean exit. 3) Compare running PID (`_portal_pid.txt`) vs actual process - stale PID file means the restart trap fired without relaunch. 4) Check `agent_portal.py` mtime vs process CreationDate: if file is newer, a code change was never loaded (restart-trap symptom).
**Fix** - Kill any stale listener on 8099; run `schtasks /run /tn PortalRun`; wait 10s. If the task no-ops (known trap), launch `python agent_portal.py` directly in a detached shell and rewrite `_portal_pid.txt`. If crash was an unhandled exception: fix the code path, then restart via the same procedure. Never bare-`schtasks /run` without killing first (see memory/ops runbook notes).
**Verify** - Port 8099 LISTENING; `/api/goals`, `/api/fleet`, `/api/git` all return 200; new group runs start (journal appears in `runs/`); PID in `_portal_pid.txt` matches live process with CreationDate > code mtime.
**Post-mortem** - Exception class + traceback location, uptime before crash, whether auto-recovery (watchdog) caught it and how slowly. Add the exception pattern to watchdog's known-restarts if novel.

## 4. Disk Full (host disk >=85%)
**Detect** - `python memory/mechanic/disk_monitor.py` alert at 90% (warn at 80%); health_check disk field amber/red; backup.py starts failing (no space for archive).
**Diagnose** - 1) Identify top consumers: `wmic logicaldisk where caption='C:' get FreePercent`, then per-directory sizes in the biggest folders. 2) Suspects on this fleet: `runs/*.journal` (multi-MB group-run journals), `memory/mechanic/backups/`, LM Studio model caches, temp/log files, git objects. 3) Check whether rotation is broken: backups dir should hold <=7 archives; rotated logs <=5 copies each.
**Fix** - Run safe cleanup only: `python memory/mechanic/disk_monitor.py` auto-cleans the safe list (*.tmp, /logs older than 7d). Manually prune: journals older than 14 days in `runs/`, extra backup archives beyond KEEP=7 (backup.py rotates automatically on next --run), old rotated logs. Never delete memory/ leaves or models without a recorded decision. If still tight: move model caches to another volume.
**Verify** - FreePercent back below 80%; disk_monitor next 15-min tick green; backup.py --run succeeds and rotation deleted the oldest; no agent reports missing-file errors after cleanup (index_check / citation sweep clean).
**Post-mortem** - What grew (rate MB/day), why rotation didn't catch it, threshold tuning needed. Update disk_monitor safe list if a new safe category was cleaned manually.

## 5. Network Partition (host unreachable over WinRM/SMB only)
**Detect** - `net_probe.py`: ping OK to some hosts but TCP connect to target's service ports fails; SMB mirror (`memory_mirror_fixed.py`) errors for that host; winrm_pool reports connection failure while ICMP succeeds.
**Diagnose** - 1) Isolate layer: ping (L3) vs TCP port (L4) vs SMB/WinRM session (L7). 2) Check the target's firewall rules and whether a recent deploy changed them (`deploy_one_host.py` history in git log). 3) Check for IP drift (DHCP reassignment) - compare against `memory/mechanic/fleet-host-registry` notes. 4) If only White<->one host is partitioned: test via a second path (direct console / another host as relay).
**Fix** - Restore reachability at the failing layer: re-add firewall rule for WinRM (5985) + SMB (445); pin the host IP; restart the SMB/WinRM service. Then heal state: run `python memory/mechanic/memory_mirror_fixed.py` for a full mirror cycle, `revert_sentinel.py` to confirm no silent reverts happened during the partition, and re-run `health_check.py`.
**Verify** - net_probe TCP connect times back within 2x baseline; mirror cycle completes with mtime-guard clean (no file churn); health_check green on all 4 hosts; `/api/fleet` shows full connectivity for >=2 consecutive cycles.
**Post-mortem** - Partition duration, which services were blind during it, whether any state diverged and how it was healed. If IP drift: move the host to a static lease in the fleet registry notes.

## Cross-references
- Host-specific steps: `memory/mechanic/recovery-matrix.md`
- Boot-time recovery: `memory/ops/boot-deployment-runbook.md`, `memory/ops/boot-detection-runbook.md`
- Windows ops: `memory/ops/windows-runbook.md`
- Post-mortem template: `memory/mechanic/postmortem_template.md` (auto-fill helper: `postmortem_gen.py`)
- Monitors feeding detection: `health_check.py`, `net_probe.py`, `disk_monitor.py`, `portal_watchdog.py`, `log_rotate.py`
- Remote exec: `winrm_pool.py` / `winrm_sspi_client.py`; recovery: `reboot_recover.py`
