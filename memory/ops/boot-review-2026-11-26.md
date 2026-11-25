# BOOT REVIEW 2026-11-26 (post-reboot) — T3 scenarios + T7 decisions

## What actually happened this morning (facts from recon)
- `PortalRun` schtask is a **one-shot trigger** — dead after reboot. TaskToRun points at portal_hidden.vbs; it never re-fires. It was NOT what started the portal today.
- The **Startup-folder chain** fired at logon (~07:2x): elev_helper_start.vbs -> portal_host.vbs. Portal up ~07:26 (matches process start).
- `elev_helper_start.vbs` was **missing from Startup** this morning (screenshot error "file not found"); 08:35 recovery pass recreated/updated the vbs files (timestamps 08:36/08:45) — after portal was already up, so it was audit-driven, not boot-caused.
- Seats at boot: White local busy with Qwen3.8-27B-Q8_0; remote seats (Red/Pale/Black :8888) unreachable for ~1h -> 7 jobs failing until they came back. Goal velocity looked "stuck" partly because of this cold-start window.

## T3 — persona scenarios
- **Orchestrator (fleet):** boot must be deterministic + observable: exactly ONE primary starter and ONE watchdog, never two primaries. Today's double mechanism (dead one-shot schtask + startup vbs) is confusing; keep startup chain as sole primary, watchdog as sole safety net.
- **Builder (mechanics):** startup vbs chain works but is fragile to file loss (elev_helper_start.vbs vanished). Fix = snapshot known-good vbs into memory/ops/boot/ and let the watchdog re-create missing files. DONE this pass for portal_host.vbs + PortalHost.vbs; elev_helper_start.vbs has no known-good copy on disk — restore from git history if it proves necessary (check `git log --all -- '*elev_helper*'`).
- **Mechanic (ops):** every boot event must be logged. Watchdog appends to _portal_boot.log on each action; schtask PortalWatchdog also gives a manual `/run` trigger for drills.
- **Archivist (retention):** this doc + TODO.md lines survive compaction; re-runnable probes kept as _pale_probe.ps1 / _pale_cap.ps1.

## T7 — decisions implemented today
1. Startup folder chain stays the **primary** starter (proven: up 07:26).
2. **PortalWatchdog schtask created** (every 10 min): WinHttp GET :8099 -> if down, launch portal_host.vbs from Startup; self-heals missing vbs from memory/ops/boot/ snapshot; logs to _portal_boot.log.
3. Known-good boot files snapshotted to memory/ops/boot/ (PortalHost.vbs, portal_host.vbs).
4. Dead one-shot `PortalRun` task: leave in place for now, **delete next turn** after confirming nothing references it (cleanup item).
5. Remote-seat cold start is normal post-reboot behavior; level-up checks should tolerate a grace window (ties to T5 slowness — 109/116 needs the 7 open goals closed, not a faster counter).

## T6 — Pale heat (this morning)
- Yesterday's verdict (11-25): NOT a breach — sustained inference load on GPU1 (llama-server Qwen3.8-27B-Q8_0 :61800), 89C/254W.
- Live read 2026-11-26 08:55: GPU0 43C 26W/600W util 0% mem 382MiB; GPU1 53C 15W/600W util 0% mem 29956MiB
- Power cap: applied -pl 450 to GPU1 (inference card); remote said: Power limit for GPU 00000000:82:00.0 was set to 450.00 W from 600.00 W.
All done.
- Re-check tomorrow: if temps still >80C under load with cap in place, next step is fan curve / case airflow on Pale.

## Next turn (see TODO.md)
- T4 prompt drill-down: latest prompts in activity/ vs agents.json template sections (M-CODE, run-rules, level context) — find stale-template gaps.
- Push the 7 open goal owners (builder 1, forge 2, orchestrator 1, outlet 2, researcher 1) via portal queue API; verify contract in agent_portal.py first.
- Verify PortalWatchdog: task exists, _portal_boot.log has entries; then delete dead PortalRun one-shot task.
