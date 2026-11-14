Last updated: 2026-11-15 ~01:4x (Mechanic goal 7 - port + scheduled-task map, all four hosts; due Friday)

# Host port + scheduled-task map
White rows VERIFIED live 2026-11-15 (probe + schtasks query). Remote rows from memory/llm/hosts.md recon (11-11..11-14) - re-verify at power-on (fleet_probe.py will flag reachability every 10 min meanwhile).

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
| PortalDailyGitCommit | daily 18:00 | POST /api/git safety-net commit (drift <=24h) |
| PortalFleetProbe | every 10 min | fleet_probe.py 4-host port probe, failures -> fleet_probe.log |
| RecoverAll | on demand / boot | recover_all.py model reload per llm recipe |

## Red (IP_RED) - seats: Scribe, Mechanic
Ports: 8888 Studio (Bearer auth ON), 3389 RDP, 445 SMB, 5985 WinRM. Tasks: PortalRun + RecoverAll (per hosts.md 11-12 recovery line). PENDING power-on re-verify.

## Pale (IP_PALE) - seats: Designer, Archivist
Ports: 8888 Studio, 445 SMB, 5985 WinRM (cmdkey TERMSRV target per recon). Tasks: PortalRun + RecoverAll (same rollout). PENDING power-on re-verify.

## Black (IP_BLACK) - seats: Builder, Verifier
Ports: 8888 Studio (was bound 127.0.0.1-only; LAN access via JWT lan-access route, auto_start), 445 SMB, 5985 WinRM. Tasks: PortalRun + RecoverAll (same rollout). PENDING power-on re-verify.
