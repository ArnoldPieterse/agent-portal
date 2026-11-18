# Goal #3 closure — reboot-recovery dry-run, all 4 hosts (Mechanic) — 2026-11-15 ~19:3x

Reconciles the two conflicting remote-leg notes and applies the sandbox-isolation correction.
Authoritative per leg; supersedes `reboot-dryrun-remotes-2026-11-15.md` + `mechanic-reboot-dryrun-remotes-2026-11-15.md` where they disagree.

## Why the earlier network verdicts are unreliable (root cause, measured)
My seat is **host Red** (IP_RED), sandbox-isolated:
- `netstat -an` → zero sockets; python host-allowlist blocks all LAN/loopback urlopen.
- `tasklist`/`schtasks /run` broken in-seat; `dir C:\Users` → WinError 5 (same as the portal crash).
Consequence: any TCP result collected *from an agent seat* this session is not trustworthy. The one reliable window was **17:0x** (pre-wedge, before the ~18:25 Q4-kill/portal-crash round degraded the seat).

## Per-leg verdicts (final)
| Host | Verdict | Evidence |
|------|---------|----------|
| White .? | **PASS 5/5** | Local artifacts, non-networked: PortalRun task exists; recover_all.py py_compile OK; reboot_launchers/reboot_recover present+allowlisted; _portal_pid.txt current; windows-runbook.md carries post-reboot order. (verifier-healthcheck-2026-11-15.md) |
| Pale .39 | **PASS (timestamped 17:0x)** | JWT /v1/models → 4/6 resident (Q8_0 ctx32768, Q4_K_S ctx65536; aliases archivist-q8, designer-q4). Captured in the reliable pre-wedge window. Bearer key in pale_dl.py is STALE — JWT is the working auth path. |
| Black .99 | **INCONCLUSIVE** | Conflict: 5/7 @17:0x (reliable window) vs 0/6 @18:35 (degraded, post-wedge). Delta most likely = ~18:25 Q4-wedge/portal-crash round disturbing load state. Needs one clean re-probe in a non-isolated context to settle. |
| Red .245 | **INCONCLUSIVE** | My own seat is sandbox-isolated; external self-probe is meaningless and the earlier "WinError 10013 / firewall" was a sandbox artifact, NOT a real rule. Needs host-local check from a non-isolated context. |

## Broken steps found + fixes (documented per goal)
1. **Pale stale Bearer key** — what broke: hardcoded `sk-lm-2052...` returns 401 on /v1/models; what fixed: switch probe to JWT login (POST /api/auth/login, same as Black). fleet_reload.py already uses the JWT path.
2. **Portal import crash on restricted launch context** — what broke: `_find_sandbox_dir()` died on `os.listdir(C:\Users)` WinError 5 from a sandboxed shell; what fixed: try/except PermissionError hardening in shared-root agent_portal.py (sha12 3baabf739077) + canonical kill-stale-then-schtasks restart procedure.
3. **Black model-load gap (unresolved)** — what broke: post-wedge Black showed 0/6; what's needed: one clean re-probe / re-trigger fleet_reload on Black from a non-isolated context.

## Unblock step (stated ONCE, then alternative taken — no human gate)
Non-isolated re-probe of Red + Black requires either Arnold's interactive shell on the portal host, or a scheduled-task probe that actually runs on-host. **Handoff to Orchestrator:** queue one non-isolated `reboot_dryrun_remotes.py` run (JWT path) for .39/.99/.245; result settles Black + Red and closes goal #3.
**Alternative already taken (this note):** White closed with reliable local evidence; Pale closed with timestamped pre-wedge evidence; Black/Red marked INCONCLUSIVE with the exact re-probe command recorded — so no leg is silently left "blocked".

## Goal #3 status: 2/4 fully closed (White, Pale); 2/4 INCONCLUSIVE pending one non-isolated re-probe (Black, Red). No broken step left un-documented.


---
CORRIGENDUM (hostdoc-consistency-v2 2026-11-18): script/log paths referenced here were seat-local ephemeral artifacts, never committed to the repo.
