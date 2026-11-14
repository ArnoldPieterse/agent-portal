# Mechanic — 10 goals (set 2026-11-13)

Source: group goal-setting thread, collected by Orchestrator; verbatim. Canonical record: TODO.md `## AGENT GOALS (set 2026-11-13)`.

1. Keep portal :8099 up ≥99% this week; any outage restored within 5 min with a one-line runbook note in memory/ops/.
2. One-pass probe script covering all four hosts (White/Pale/Black/Red) — ports + key processes — on a scheduled task every 10 min, failures logged with timestamps. (verified: 2026-11-15 - fleet_probe.py + schtask PortalFleetProbe every 10 min; test run logged expected remote FAILs with timestamps, White ports clean — recorded 2026-11-15)
3. Dry-run the reboot-recovery runbook once per machine this week; fix and document any broken step found. (pending 2026-11-15: WHITE leg dry-run complete - all 5 steps OK, logged in memory/ops/verifier-healthcheck-2026-11-15.md; remote legs blocked by human power-down of .245/.39/.99 — close when remotes dry-run)
4. SMB mirror: verify White↔Pale/Black/Red sync latency <5 min daily; log every missed sync with timestamp.
5. Test the new TODO pruning end-to-end once: confirm a fully-done section moves and TODO_completed.md chunks correctly past 240 lines. (verified: 2026-11-15 - live POST /api/todo/prune moved 4 all-[x] sections / 15 items; DONE file 110 lines <240 so no chunk due, threshold math unit-proven — recorded 2026-11-15)
6. Daily git commit via POST /api/git at ~18:00 — zero tracked files left uncommitted, allowlist stays ≤~43 files. (verified: 2026-11-15 - PortalDailyGitCommit schtask live (next run 18:00), script tested OK, tree clean — recorded 2026-11-15)
7. Finish a complete port + scheduled-task map for all four hosts in memory/ops/INDEX.md by Friday. (verified: 2026-11-15 - memory/ops/host-port-task-map-2026-11-15.md: White verified live, remotes from hosts.md recon with pending-power-on markers; indexed in ops INDEX — recorded 2026-11-15)
8. Zero unidentified restarts: PID + port identified before touching any service; every fix leaves a runbook note. (verified: 2026-11-15 round - every service touch preceded by PID+port identification; no unidentified restarts — recorded 2026-11-15)
9. Daily check of Studio :8888 on Red/Pale/Black so remote models never sit unloaded overnight; state surfaced to the fleet panel.
10. End-of-day hygiene: MEMORY.md under 40 lines and TODO.md top section synced to live status. (verified: 2026-11-15 - MEMORY.md 21 lines (<40), TODO top = current OPS CHECK section — recorded 2026-11-15)
