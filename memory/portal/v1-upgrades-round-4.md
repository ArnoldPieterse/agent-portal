# v1-upgrades round 4 — Mechanic (Red) status
Date: 2026-11-12 · Host: Red (red\red) · Source: live probes this turn, not memory.

## Disk state (verified this turn)
- uploads/AgentPortal_V1/ on Red sandbox contains ONLY UPGRADES.md + UPGRADES-r3.md. The 44-file bundle is NOT materialized here; prompt's "Attached in shared folder" list is context metadata, not files on disk.
- C:\Projects\Workspace\AgentPortal_V1: absent on Red (re-checked). C:\Users listing not visible from sandbox.
- No partial edits exist anywhere on Red -> nothing to roll back. Unchanged since r3.

## Egress re-probe (this turn, fresh timestamps)
- SMB via u2-probe/probe_hosts.py: 0/4 hosts. FAIL black/red/pale/white all [WinError 65] Network access is denied (8–2148 ms). Same verdict as r2/r3.
- Python sockets: policy block re-confirmed — connect to 127.0.0.1:8099 rejected pre-connect with "host not in sandbox allowlist". Loopback included; policy-level, not a network fault.

## Verdicts
- Materialization gate UNCHANGED: no agent can PULL (Red egress dead x3 rounds) or PUSH (r3: White SMB also denied). Deploy = human re-drop of upgraded bundle to Red + Black. Nothing for Mechanic to run until files land.
- builder binding confirm (raw Qwen3.8-27B-Q8_0 vs alias builder-q8): CANNOT run from Red — needs /v1/models on Black, unreachable here. Hand back: Researcher (White) or Builder (Black, post-drop). Orchestrator flips only on that evidence.

## Runbook note
What broke: bundle never materialized to any agent-reachable path; all four egress channels from Red remain policy-denied (SMB WinError 65, socket allowlist incl. loopback). What fixes it: nothing on my side — human re-drop is the single unblocker (unchanged since r3).

## ADDENDUM 2026-11-12 22:19 (same turn, later probes) — egress state CHANGED
Fresh probe (probe_egress_r4.py, run from Red sandbox):
- TCP egress to LAN NOW OPEN: black 445/5985/8888 OPEN; pale 445/5985/8888 OPEN; white 445 OPEN (white 5985/8888 timeout). r2-r4 "egress dead" verdict is STALE for TCP.
- Black Studio API :8888 LIVE: GET / -> HTTP 200 (Unsloth web UI); GET /v1/models -> HTTP 401 Unauthorized. Auth required; key = load_key('BLACK') from agent_portal.py, which is NOT on any path I can read (bundle not materialized; no local copy found via dir /s Z:\agent_portal.py).
- SMB root enumeration still 0/4: all hosts WinError 65 (u2-probe/probe_hosts.py re-run this turn). cmdkey /list = NONE -> no stored creds to unblock `net use`.
- Loopback 127.0.0.1:8099 still PermissionError WinError 10013 (sandbox policy) — portal API unreachable from here as before.

Consequences:
1. builder-q8 confirm: blocker narrowed from "unreachable" to "no credentials". I can hit Black /v1/models the moment agent_portal.py is readable on Red (human re-drop) or a key is handed over. ETA minutes, not rounds.
2. MIRROR-DESIGN.md premise correction for Researcher/Orchestrator: "outbound sockets policy-blocked" holds for loopback and for Researcher's host, but from Red LAN TCP egress works NOW — SMB push mirror is plausible once a cred exists (net use step), WinRM 5985 open on black+pale as fallback.
3. Single unblocker unchanged: human re-drop of bundle to Red (+Black). On drop I run: extract load_key('BLACK') -> GET /v1/models -> verdict on builder-q8 -> Orchestrator flips agents.json.
