# Human Operating Manual — Residual Human-Role Spec
*Cycle 26 · Scribe goal #4 · written 2026-11-26*

**Purpose.** The single page answering: at steady state, what MUST the human still do?
Minimal action set only. Every already-automated touchpoint is excluded (see §3) and
cross-checked against existing automation so no listed action is one an automation covers.

**Sources (traceable).**
- `memory/scribe/fleet-autonomy-playbook.md` — "Where human input is still needed" list (the intended roadmap source).
- `memory/ops/human-interventions.jsonl` — 10 real logged interventions (cycles 2–17).
- `memory/scribe/intervention-pattern-summary.json` — pattern split: new_requirement 5, edge_case 2, preference_override 2, tool_gap 1.
- `memory/goals/dependency-graph.json` + `memory/orchestrator/dependency-graph.json` — existing-automation cross-check.

> NOTE (provenance): the Cycle-25 deliverables named as sources —
> `memory/scribe/touchpoint-roadmap.md` and `memory/scribe/autonomy-dependency-graph.json`
> — were **never persisted to disk** (verified absent 2026-11-26; a stale claim in the
> Cycle-25 goal file). This manual reconstructs the inventory from the playbook's
> "human input needed" list + the intervention log, which is exactly what that roadmap
> was specified to draw from. No numbers invented.

## 1. Residual human actions (the minimal set)
**Total: 4 actions — within the <=5 cap.**

### A1 — Set / redirect strategic direction  *(class: redirect, by design irreducible)*
- **Trigger:** whenever a new objective or priority change is wanted (round topic / goal set). Logged 3× (c2, c12, c16).
- **SLA:** on-demand, no fixed cadence — the human sets goals; fleet optimizes within them.
- **Consequence if skipped:** fleet keeps optimizing inside the last-set direction; no new strategic course. Not a failure — just no new intent.
- **Why not automated:** strategic intent is the human's role by design (playbook: "human is the goal-setter"). No automation may self-authorize new goals (circular authority).

### A2 — Ratify the cycle goal set  *(class: approve)*
- **Trigger:** GOAL_RESET_PENDING — each cycle's goal set (now auto-drafted by `memory/scribe/goal_synth.py`) awaits sign-off before work starts. Logged 3× (c5, c14, c16).
- **SLA:** within the cycle-boundary window; if not ratified, fleet holds and continues maintenance on existing goals (no new work begins).
- **Consequence if skipped:** no forward progress on *new* objectives this cycle; existing goals keep running. No data loss.
- **Why not automated:** `goal_ledger.py` tracks lifecycle but cannot self-ratify (circular authority). Path to elimination: confidence threshold for auto-approve (e.g., all goals forecast P>0.8).

### A3 — Specify UI / visual acceptance criteria  *(class: preference_override)*
- **Trigger:** a visual element ships and "what looks right" is not machine-decidable (e.g., button sizing/placement, c15). Logged 2× as preference_override.
- **SLA:** within the verification window for that UI change; if skipped, the change passes Verifier's *functional* tests only — layout/visual is not gated.
- **Consequence if skipped:** a visually-wrong-but-functionally-passing release can slip through (pixel regression uncaught).
- **Why not automated:** Verifier runs Playwright functional checks; there is **no design-rubric auto-checker yet**. Path to elimination: build a design-rubric auto-checker (Designer/Verifier).

### A4 — Confirm relocated model seat as a normal seat  *(class: edge_case, partial)*
- **Trigger:** `memory/ops/fleet_probe_v2.py` detects a host down and auto-relocates a model; the final "treat as normal seat" confirmation still comes from human (c17). Logged 2× as edge_case.
- **SLA:** within the probe/relocation window; if skipped, the relocated seat is held in degraded/quarantine state (not counted as a full seat).
- **Consequence if skipped:** reduced effective fleet size → slower cycle throughput. No correctness loss.
- **Why not automated:** detection + relocation IS automated (`fleet_probe_v2.py`); only the final confirmation is residual. Path to elimination: codify auto-relocation policy in `fleet-mode.json`.

## 2. What this means at steady state
The human's irreducible role collapses to **two**: set direction (A1) and ratify goals (A2).
The other two (A3 visual spec, A4 seat confirmation) are *convergence targets* — each has a named
automation that will remove it (design-rubric checker; fleet-mode.json auto-relocation policy).
When both land, steady-state human load = 2 actions/cycle max.

## 3. Already automated — EXCLUDED from the manual (cross-check)
These were candidate touchpoints but are covered by live automation, so they are NOT listed above.
Every path verified to exist on disk 2026-11-26.

| Excluded touchpoint | Covering automation (exists) |
|---|---|
| Portal crash recovery | `memory/mechanic/portal_watchdog.py` + `memory/ops/boot_recovery.py` |
| Host-down detection + model relocation | `memory/ops/fleet_probe_v2.py` |
| Mirror / pin-file clobber healing | `memory/ops/mirror_heal.py` |
| Pointer/index integrity | `memory/archivist/index_check.py` |
| Goal lifecycle tracking | `memory/researcher/goal_ledger.py` |
| Autonomy score computation | `memory/orchestrator/autonomy_score.py` |

**Acceptance self-check:** 4 residual actions (<=5 cap) ✓ · every action has trigger+SLA+skip-consequence ✓
· all roadmap touchpoints covered (3 classes + 3 gaps → mapped to A1–A4) ✓ · no listed action is one an
existing automation covers (§3 cross-check, all paths exist) ✓.
