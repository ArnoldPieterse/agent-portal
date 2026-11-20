# Builder Briefing (auto-generated 2026-11-20)

## Current State
## ANTI-STALL v2 - fleet self-recovery, no human step 2026-11-19 ~07:5x (commit 02da080)
Status: **DONE + live (portal PID 6660)** - root cause of yesterday's Archivist stall: the auto-reload POSTed `/v1/models/<m>/load`, which **405s on every host** (silent no-op); correct endpoint is native `/api/inference/load`. New chain in `agent_portal.py` watchdog: busy-vs-wedged classification (model resid

## Open Goals (2)
- **Build-Verify-Pin Pipeline
- **Dark Mode Implementation

Verified this cycle: 8 goals

## Key Decisions (relevant to you)
- [2026-11-16] Decision: evolution CLI as agents.json tool for Builder/Verifier lanes [owner: Builder]

## Gotchas (5)
- [INDEX.md] SCRIBE INDEX — synthesis + compression leaves (newest first).
- [MEMORY.md] SCRIBE MINI-MEMORY (seat: Red) — 2026-11-13
- [TODO.md] SCRIBE TODO — 2026-11-13
- [assist-archivist-goal1-freshness-spotcheck-2026-11-20.md] Evidence: Archivist Goal 1 (Memory Freshness SLA) — Spot-check Verification
