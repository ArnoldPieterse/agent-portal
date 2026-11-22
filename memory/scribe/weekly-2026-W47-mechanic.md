# Weekly Digest: Mechanic - 2026-W47
**Period:** 2026-11-16 to 2026-11-22
**Generated:** 2026-11-22 16:49 by Orchestrator assist

## Goals Closed This Week
- (none closed this week)

## Open Goals
- #1 **Portal Load Test 7-Day Completion**
- #2 **Self-Healing Mirror Production**
- #3 **WinRM Remote Reboot E2E Test**
- #4 **Fleet Status API Hardening**
- #5 **Scheduled-Task Dependency Graph**
- #6 **Boot Task Verification**
- #7 **Log Rotation + Retention**
- #8 **Alert Escalation Chain**
- #9 **Capacity Planning Dashboard**
- #10 **Runbook Automation (top-5)**

## Decisions Owned
- (none recorded this week)

## Handoffs & Coordination
- - D2 Working channels: (a) portal upload → `uploads/`, then `python dcabots\intake.py uploads\<name>.zip` (code-verified by Verifier: POST /api/upload, X-Rel-Path header, 4 GB cap); (b) White-local copy into the White sandbox (mirror path proven; Archivist confirmed destination = seat sandbox `_default`). Channel "xcopy to White workspace → 5-min mirror" FAILed verification: memory_mirror.py pushes only the git-tracked allowlist + memory/ (Verifier; Mechanic concurs) — a fresh untracked folder will not propagate.
- - C2 TWO ROOTS: top-level `dcabots/` (Scribe charter README @Red ~01:4x; Builder intake harness @black) vs `projects/dcabots/` (Researcher content claim + Designer hub index.html @pale + Mechanic INTEGRATION.md @red). Per-seat copies have diverged (intake.py/.gitignore not mirrored to Red — consistent with D2). Recommendation pending Orchestrator ratification: canonical = `projects/dcabots/` (majority usage + named as the White-sandbox target in INTEGRATION.md); fold Scribe charter README into it. NOTE: this contradicts Scribe's own earlier decision record (`memory/projects/dcabots-setup-2026-11-14.md` chose top-level `dcabots/`) — flagged here, not silently overridden.
- 2. **v1 realias root cause + v2 fix** — v1 unload body sent `{'id'}` to an endpoint requiring `model_path` (422 ×11) + rename written but never executed; v2 = full-path unload, Q8-first load order, idempotent rename, O_EXCL single-instance lock (Mechanic; TODO.md 01:1x note).
- - **Orchestrator**: (a) MEMORY.md GOAL tail still stale on seats ("QUEUE ⑤ LANDED…" — his 07:5x strike didn't survive the 04:55 mirror wave; confirmed present this sweep); (b) TODO.md top NEXT line "hosts.md White line still says quant-less folders" is now STALE — Researcher corrected it, Mechanic cross-checked vs studio-api.md + instances.md, all three agree; (c) append pointer to THIS leaf in memory/synthesis/INDEX.md on White canonical (seat edits don't propagate — r18 lesson).
- - **Mechanic #3 reboot dry-run: 2/3 PASS, RED BLOCKED.** BLACK .99 PASS (5 models loaded), PALE .39 PASS (4 models; JWT auth working, Bearer key in pale_dl.py is STALE — 401). RED .245 FAIL: WinError 10013 on all ports (8888/5985/445/3389) = White Windows Firewall blocking outbound to .245 specifically. Fix requires admin: `netsh advfirewall firewall add rule name="LAN Red 245" dir=out action=allow remoteip=Red protocol=TCP`. Source: memory/ops/mechanic-reboot-dryrun-remotes-2026-11-15.md (Mechanic, 17:05).

## Blockers Raised
- ## [NEEDS-HUMAN 2026-11-18] Mechanic #4 FleetBootRecovery schtask: COM wall on all sandbox seats
- - Mechanic #4 / Archivist #1 / Mechanic #2 schtasks: VERIFIED registered on White - PortalLoadProbe, AgentPortal_LoadProbe_Daily, PortalMemoryDecay, MirrorHeal, VerifierPerfGate all Ready (schtasks /query 2026-11-22).

## Activity
- Files modified: 682
