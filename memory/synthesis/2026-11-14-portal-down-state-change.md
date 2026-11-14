# 2026-11-14 — Portal DOWN state change (Mechanic health check ~11:40)

Round record, no supersession. Source: Mechanic chat message 11-14 ~11:40 (portal health check); cross-checked against TODO.md + MEMORY.md on this seat.

## What was decided / established
- **Portal is DOWN** — no python process, no :8099 listener. Root cause per Mechanic: `agent_portal.py` upgraded at 08:02 today (**a3bec6e6**, +223 lines adding per-message ReadMem/StoreMem cycle) but never started after landing; a machine reboot killed prior **PID 23704** and nothing auto-restarted it (**no schtasks entry exists**). Logs empty = clean death, not a crash.
- Mechanic cannot restart from his sandbox (`_find_sandbox_dir()` fallback → `PermissionError` on `C:\Users`). **Human action required: Arnold runs `python agent_portal.py` from the White console.**
- Everything else verified OK by Mechanic: `memory_mirror.py` at pin e5c4a229; hosts.md already has quant-named folder names; py_compile on new portal code passes. Mechanic updated TODO with findings (not yet visible in my seat's 01:46 snapshot — mirror lag, expected).

## Consequences for open gates (synthesis, all traceable)
1. **Human gate re-ordered.** Starting the portal is now a *prerequisite* for every live gate: smoke8, AC-A2 process leg, /api/fleet, served pages. "Arnold's White-console pass" cannot execute until the portal is up.
2. **PID 23704 is dead** (reboot-killed). The MEMORY.md goal line ("portal PID 23704") and Verifier r76 leaf's process-leg pin are now stale. Post-restart, a NEW PID must pass the trap check: CreationDate > `agent_portal.py` LastWriteTime (~08:02); Verifier re-pins AC-A2-1..4 to it.
3. **a3bec6e6 has never run live** — py_compile only. The first restart is its first production run; Builder goal #9 5-point regression (chat, file links, DM markers, prune, git) should follow the start.

## Contradiction flagged (not adjudicated)
- TODO.md line 86 records `arnold-restart-r8.ps1` using `schtasks /run PortalRun` (r8, 11-13 — implies a PortalRun task existed), but Mechanic reports **no schtasks entry exists** (11-14 ~11:40). Either the task was lost at reboot or never created on this machine. Needs Arnold/Mechanic confirmation before anyone reuses that script path.

## Open decision
- Mechanic proposes setting up a **schtasks PortalRun for auto-recovery**. Owner not yet assigned; if adopted, Mechanic (ops) is natural owner, Arnold approval needed (machine-level task).

## Repair text owed on White canonical (my seat's root docs are push-only snapshots — edits here do NOT propagate)
- MEMORY.md hot note line 43 truncated: "…Arnold's White-console pass (bundle v2 items 1–8 + firewall :8099/:888" → complete as ":8099/:8888 egress) — **now with prerequisite: portal start first** (see this leaf)."
- MEMORY.md hot note line 44 truncated: "Portal DOWN: agent_portal.py upgraded (a3bec6e6) but" → complete as "but never started after reboot; no schtasks entry; Arnold must run `python agent_portal.py` on White console; PID 23704 dead — re-pin trap check to new PID post-restart."
- Hand off: **Orchestrator** applies both repairs at canonical.
