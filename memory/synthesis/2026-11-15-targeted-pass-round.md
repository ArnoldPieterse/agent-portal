# Synthesis — Targeted Pass Round 2026-11-15 ~18:xx

Fleet state at round start: 52/80 (65%). Open lanes: Builder 4/10, Verifier 3/10, Designer 1/10, Mechanic 8/10, Orchestrator+Researcher 8/10. Assist pool: Archivist + Scribe at 100%.

## Decisions & outcomes (verbatim, source-cited)

- **Mechanic #3 reboot dry-run: 2/3 PASS, RED BLOCKED.** BLACK .99 PASS (5 models loaded), PALE .39 PASS (4 models; JWT auth working, Bearer key in pale_dl.py is STALE — 401). RED .245 FAIL: WinError 10013 on all ports (8888/5985/445/3389) = White Windows Firewall blocking outbound to .245 specifically. Fix requires admin: `netsh advfirewall firewall add rule name="LAN Red 245" dir=out action=allow remoteip=Red protocol=TCP`. Source: memory/ops/mechanic-reboot-dryrun-remotes-2026-11-15.md (Mechanic, 17:05).

- **PALE auth fix documented.** Bearer key `sk-lm-2052...` stale; JWT login (`POST /api/auth/login`) is the working path. fleet_reload.py already uses JWT for Pale. Action: note in pale_dl.py that Bearer is deprecated. Source: memory/ops/mechanic-reboot-dryrun-remotes-2026-11-15.md (Mechanic).

- **Designer index.html pin synced.** Local was stale at b59e528fe540 (L827 dup-catch bug); Orchestrator applied fix; confirmed byte-exact at canonical 37549a041412 on shared root. Source: MEMORY.md hot notes + TODO.md DONE section 17:xx (Orchestrator).

- **Goal-cycle upgrade live in agent_portal.py.** Goal-reset flag arms GOAL_RESET_PENDING.json at 100% fleet; cross-assist + anti-loop rules injected every turn. Portal restart per RESTART TRAP pending to load upgrades. Source: TODO.md top section (Orchestrator, 18:xx).

- **Human gates ALL cleared by Arnold 17:xx.** ① Mechanic #3 remote legs OK'd; ② CHG-0002 ACCEPTED; ③ White Q8_0 = KEEP. Source: TODO.md DONE section 17:xx (Orchestrator recording Arnold directive).

## Still open after this round
- RED firewall fix (HUMAN GATE — requires admin on White)
- Portal restart to load goal-cycle upgrade
- Builder/Designer/Verifier open lanes continue in next pass

---
Scribe, 2026-11-15 ~18:xx. All claims trace to named source files above.