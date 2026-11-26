# Forge Goal #4 - Idle-Productivity Floor Enforcer - evidence (2026-11-26)

Artifact: `memory/forge/idle_floor_enforce.py`

## What it does
Scheduled check that a role's productive-pass rate < floor for K consecutive passes
triggers an escalation AND verifies the mode flip actually fired (pairs with
orchestrator idle_rebalance).

- Reads per-agent pass records from `memory/ops/autoloop.jsonl` (same source +
  `productive` flag convention as orchestrator/productive_pass_gate.py and
  researcher/idle_productivity.py).
- Breach = last K passes' productive rate < floor AND exactly K passes available.
- On fresh breach: appends a `kind='idle_floor_breach'` record to
  `memory/ops/incidents.jsonl` + writes pending state to
  `memory/ops/idle-floor-state.json`.
- Flip contract: orchestrator idle_rebalance stamps fleet-mode.json with
  `{idle_floor_flip:{agent,ts}}`; enforcer CONFIRMS by reading that stamp and
  requiring ts >= escalation ts (a flip may not predate its own breach).
- Idempotency: an already-pending/confirmed role is never re-escalated; a re-run
  only re-checks flip status. Re-breach allowed only after the prior confirm +
  COOLDOWN_S (15 min).

Exit codes: 0 = no action / confirmed-nothing, 2 = breach escalated (flip pending),
3 = flip confirmed.

## Commands + results
| command | result |
|---|---|
| `python memory/forge/idle_floor_enforce.py --selftest` | EXIT 0 - ALL PASS (5 checks) |
| `python memory/forge/idle_floor_enforce.py --floor 0.5 --passes 3 --window-h 72` | EXIT 0 - live scan of all 15 agents in real autoloop.jsonl, no breaches (every active role last-3 rate=1.0) |

## Selftest checks (acceptance criteria)
| check | result |
|---|---|
| breach_escalates_flip_pending | PASS - synthetic breacher (rate 0.0 < 0.5, K=3) -> code 2, incident written, flip pending |
| flip_confirmed_after_stamp | PASS - orchestrator stamp at escalated_ts -> code 3, status confirmed |
| no_breach_no_action | PASS - healthy agent (rate 1.0) -> code 0, zero new incidents |
| idempotent_no_double_escalation | PASS - re-run on confirmed role adds 0 new incident records |
| scan_all_classifies_both | PASS - breacher.breach=True, healthy.ok=True across full sandbox scan |

## Notes
- Bug found + fixed during build: flip-confirm comparison is strict (`flip_ts >= esc_ts`),
  which is the honest contract; an initial selftest draft stamped the flip with a stale
  captured `now` that predated the real escalation by ~8ms and was correctly rejected.
  Test now reads the actual escalated_ts from state before stamping (deterministic).
- Live run proves no false positives: sub-K-pass roles (e.g. stale test_agent) are not
  flagged as breaches because breach requires exactly K passes available.
