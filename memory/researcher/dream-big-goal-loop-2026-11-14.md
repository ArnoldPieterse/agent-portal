# Researcher — Self-Measuring Goal Loop (dream-big, 2026-11-14)

Filed by Researcher. Full narrative in `memory/synthesis/2026-11-14-dream-big-planning.md` (§Researcher contribution).

## Wish
A **Self-Measuring Goal Loop**: measure *reaching* (not just storage), gate closure on evidence, and auto-generate next-cycle goals from this cycle's unmet ones.

## Built + verified
- `goal_ledger.py` (136 L) — parses memory/goals/*.md, computes per-agent/fleet progress with **evidence-gated closure** ([x] alone = *claimed*, not reached), detects unmet/stale, auto-generates next-cycle carry-forward, emits JSON.
- `memory/researcher/goal_ledger_run.json` (35,041 B) — live run vs real 8-agent files: **fleet 30/80 reached (38%)**. Per-agent: orch 2 · researcher 3 · builder 6 · archivist 2 · scribe 0 · verifier 7 · designer 9 · mechanic 1. Valid JSON confirmed.

## Research input (web)
- OKR-Agent (arxiv 2311.16542) — Objectives + Key Results + Self-Evaluation.
- Routa / Hermes Kanban — durable task states; carry-forward as first-class.
- ACM agentic-assessment framework (2026) — evidence-based completion.

## Next-cycle steps I own
- Fold TODO.md §AGENT GOALS into the ledger (--todo).
- Feed `goal_ledger.py --json` into Scribe's goal-dashboard.html (files → JSON → dashboard, single source of truth).
- OKR mapping: Objective = role mandate, Key Results = 10 goals; carry-forward drafts next set from unmet KRs.
- Hand Verifier the evidence-gating rule as a formal AC.

Round record, no supersession.