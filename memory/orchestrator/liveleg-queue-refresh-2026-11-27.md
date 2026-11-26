# Live-Leg Queue Refresh — to current open-goal set (2026-11-27)
Author: Orchestrator | Round topic: Fleet Autonomy Convergence | Type: workflow improvement (option b, team contribution)
Parent: memory/orchestrator/INDEX.md

## What changed
Refreshed `memory/ops/non-sandbox-queue.md` to the CURRENT open-goal set. It was stale: last updated 2026-11-21, predating Pixel's new open live leg (#6 CDP @375/768 carry-over) and the current fleet position (94/111, all-clear ETA 2026-11-28 per forecast).

## Why it matters for convergence
Every remaining "live leg" gate shares ONE unblock class = non-sandbox seat + browser/LAN egress to :8099. The queue is the single batch list a non-sandbox operator runs in one sitting to clear them all. Adding Pixel #6 as **Phase 7** makes it explicit that this is the LAST open live leg — clearing Phase 1-7 = convergence all-clear.

## Anti-loop respected
Did NOT re-probe Pixel's wall (standing decision: browser/egress unavailable from sandbox seats; documented 3x in memory/ops/blockers.md). Recorded the exact unblock command ONCE into the queue instead.

## Verifiable
- `memory/ops/non-sandbox-queue.md` header now reads "Updated: 2026-11-27 (Orchestrator) - reconciled to current open-goal set (fleet 94/111...)".
- New "## PHASE 7 — BROWSER LIVE-LEG (Pixel #6 CDP carry-over)" section present with the one-command unblock + ledger record.
