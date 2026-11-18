# Ops — probe & verification scripts inventory
Last updated: 2026-11-11 (split from memory/ops-windows.md; +host probes).
## Probe scripts (project root)
- smoke_e2e.py — full group flow incl. cross-talk + block test. silent_probe2.py — [SILENT] behavior.
- probe_quinn.py / test_group.py — per-agent reply + role-fix proof. qprobe.py, probe2..7 — API probes.
- e2e_test.py (task \PortalE2E) — 400-fix + tool-execution proof. e2e_parallel.py (task \PortalE2EPar)
  — concurrent group prompt: stream-overlap timing, atomic counter growth, memory-file readability.
  ALL e2e runners must be DETACHED (schtasks): an in-turn probe queues behind this chat's own Q4 slot.
## Host probes (multi-host expansion)
- red_probe.py / _red_recon*.py — Red :8888 over LAN (`set RED_KEY=...` first).
- probe_black.py — Black :8888 over LAN (`set BLACK_KEY=...` first); TCP pre-checks 8888/3389, then
  /api/health, /v1/models, /api/settings/lan-access. Key (refreshed ~14:00, verified) lives in host_api.py
  load_key('BLACK') - chat-only pattern; tunnel Bearer works today (tunnel_urls.json). scan_red.py — subnet sweep for other hosts.
- mstsc_shots.ps1 — PrintWindow (flag 2) capture of EVERY visible RDP window from White without stealing
  focus -> mstsc_<pid>.png; use to inspect Arnold's remote sessions (Red/Black).


## Fleet panel ground truth (2026-11-13)
- GET http://127.0.0.1:8099/api/fleet -> 200 + one entry per host {state busy|idle|unknown, models, last_seen}; a dead host must show unknown (never idle/green) and the response stays bounded (~3s timeout per dead host). Detail: memory/portal/fleet-status.md.

## Ground-truth rule: verify agent file writes on disk
- An agent's "I wrote X" reply is a CLAIM, not evidence. 2026-11-11: Archivist announced "Drafted and
  written: memory/portal/file-links.md" in group e2e round 2; the file existed nowhere (project root,
  sandbox, V1) and no tool trace in portal logs -> hallucinated write. Check the path on disk before
  recording a build claim as done (provenance note in memory/portal/file-links.md).

## Chained runners: verify summary sections against on-disk result files (2026-11-12)
red_chain.py first run: red_smoke.py crashed exit=1 (open() got an indent= kwarg) so the chain's
summary kept the PREVIOUS run's red_smoke_result.json section, and a P() signature bug killed the
chain after writing it. Rule: for any chained runner, check each summary section against the
on-disk *_result.json timestamp BEFORE acting; a crashed stage leaves a stale section behind.
