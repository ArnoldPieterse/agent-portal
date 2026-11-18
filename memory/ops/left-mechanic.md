Last updated 2026-11-13

# mechanic - open goals (split from what_is_left.txt)

mechanic | Keep portal :8099 up ≥99% this week; any outage restored within 5 min with a one-line runbook note in memory/ops/.
mechanic | Dry-run the reboot-recovery runbook once per machine this week; fix and document any broken step found.
mechanic | SMB mirror: verify White↔Pale/Black/Red sync latency <5 min daily; log every missed sync with timestamp.
mechanic | Test the new TODO pruning end-to-end once: confirm a fully-done section moves and TODO_completed.md chunks correctly past 240 lines.
mechanic | Daily git commit via POST /api/git at ~18:00 — zero tracked files left uncommitted, allowlist stays ≤~43 files.
mechanic | Finish a complete port + scheduled-task map for all four hosts in memory/ops/INDEX.md by Friday.
mechanic | Zero unidentified restarts: PID + port identified before touching any service; every fix leaves a runbook note.
mechanic | Daily check of Studio :8888 on Red/Pale/Black so remote models never sit unloaded overnight; state surfaced to the fleet panel.
mechanic | End-of-day hygiene: MEMORY.md under 40 lines and TODO.md top section synced to live status.
