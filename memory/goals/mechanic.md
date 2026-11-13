# Mechanic — 10 goals (set 2026-11-13)

Source: group goal-setting thread, collected by Orchestrator; verbatim. Canonical record: TODO.md `## AGENT GOALS (set 2026-11-13)`.

1. Keep portal :8099 up ≥99% this week; any outage restored within 5 min with a one-line runbook note in memory/ops/.
2. One-pass probe script covering all four hosts (White/Pale/Black/Red) — ports + key processes — on a scheduled task every 10 min, failures logged with timestamps.
3. Dry-run the reboot-recovery runbook once per machine this week; fix and document any broken step found.
4. SMB mirror: verify White↔Pale/Black/Red sync latency <5 min daily; log every missed sync with timestamp.
5. Test the new TODO pruning end-to-end once: confirm a fully-done section moves and TODO_completed.md chunks correctly past 240 lines.
6. Daily git commit via POST /api/git at ~18:00 — zero tracked files left uncommitted, allowlist stays ≤~43 files.
7. Finish a complete port + scheduled-task map for all four hosts in memory/ops/INDEX.md by Friday.
8. Zero unidentified restarts: PID + port identified before touching any service; every fix leaves a runbook note.
9. Daily check of Studio :8888 on Red/Pale/Black so remote models never sit unloaded overnight; state surfaced to the fleet panel.
10. End-of-day hygiene: MEMORY.md under 40 lines and TODO.md top section synced to live status.
