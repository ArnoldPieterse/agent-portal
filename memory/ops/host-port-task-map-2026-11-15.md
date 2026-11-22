Last updated: 2026-11-18 (added Access section: RDP + SMB passwords empty on all hosts)

# Host port + scheduled-task map
White rows VERIFIED live 2026-11-15 (probe + schtasks query). Remote rows from memory/llm/hosts.md recon (11-11..11-14) - re-verify at power-on (fleet_probe.py will flag reachability every 10 min meanwhile).

## Access (RDP + SMB) - all hosts
- **All passwords are EMPTY.** RDP on every host: empty password (Arnold, 2026-11-18). SMB admin shares (C$) likewise - `net use \\ip\C$ /user:<acct> ""` works; see memory_mirror_hosts.json (note field).
- Accounts: Red = `Red`, Pale = `pale`, Black = `black` (per memory_mirror_hosts.json); White is the local machine.

## White ([LAN-IP] / local)
| port | service | state |
|---|---|---|
| 8099 | portal (agent_portal.py, PID in _portal_pid.txt) | UP (verified 11-15) |
| 8888 | Unsloth Studio | UP (Q8_0 resident) |
| 445 | SMB (mirror push target) | open (empty-pw hosts, memory_mirror_hosts.json) |
| 5985 | WinRM (fallback exec) | TrustedHosts = .245/.99/.39 |

| task | schedule | purpose |
|---|---|---|
| PortalRun | at logon | start portal (TRAP: no-ops while Running - kill PID first, windows-runbook.md) |
| MemoryMirrorRun | every 5 min | memory_mirror.py push/pull allowlist |
| PortalDailyGitCommit | every 15 min (was daily 18:00, 2026-11-16) | POST /api/git safety-net commit (drift <=15 min idle) |
| PortalFleetProbe | every 10 min | fleet_probe.py 4-host port probe, failures -> ⚠missing:fleet_probe.log |
| RecoverAll | on demand / boot | recover_all.py model reload per llm recipe |

## Red (Red) - seats: Scribe, Mechanic
Ports: 8888 Studio (Bearer auth ON), 3389 RDP, 445 SMB, 5985 WinRM. Tasks: PortalRun + RecoverAll (per hosts.md 11-12 recovery line). PENDING power-on re-verify.

## Pale (Pale) - seats: Designer, Archivist
Ports: 8888 Studio, 445 SMB, 5985 WinRM (cmdkey TERMSRV target per recon). Tasks: PortalRun + RecoverAll (same rollout). PENDING power-on re-verify.

## Black (Black) - seats: Builder, Verifier
Ports: 8888 Studio (was bound 127.0.0.1-only; LAN access via JWT lan-access route, auto_start), 445 SMB, 5985 WinRM. Tasks: PortalRun + RecoverAll (same rollout). PENDING power-on re-verify.
