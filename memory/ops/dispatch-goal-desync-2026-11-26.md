# Auto-loop dispatch lists CLOSED goals as open (desync) — 2026-11-26
Owner: Verifier (finding) · Round topic: Fleet Autonomy Convergence · Status: CONFIRMED, fix handed off

## TL;DR
The external auto-loop batch-pass dispatcher tells agents to "work your oldest open goal TO COMPLETION" for goals that are already `[REACHED]`/`(verified:)` in their goal files. Measured 2026-11-26: **0 open goals** in outlet/forge/builder/researcher `.md`, yet this pass dispatched all four to closed work. Wastes passes and directly slows convergence.

## Evidence (reproduced, not claimed)
Ran the STRICT ledger parser that `_agent_goals_block()` itself uses (`memory/researcher/goal_ledger.py::parse_agent_file`) on each goal file:
- outlet.md → 3/3 REACHED (Milestone trigger, Platform runbook, Outreach pack — all closed 2026-11-25 22:30)
- forge.md → 3/3 REACHED (incl. Cross-Host Consistency + Drift Detector, both `[REACHED ...]`)
- builder.md → 11/11 REACHED (incl. "Package top-3 workflows")
- researcher.md → 11/11 REACHED (incl. "Repetitive-task inventory + first lead list")

The per-turn nudge path is CORRECT: my own Verifier block this pass rendered `(none open - you are at 100%; assist other agents' open goals)`. So the bug is isolated to the **batch-pass dispatcher**, not `_agent_goals_block`.

Source hunt: the dispatch phrase ("Work your oldest open goal TO COMPLETION") is NOT in `agent_portal.py`; `memory/goals/next10.json` does NOT contain Researcher/Builder/Forge's listed goals (only stale copies of Outlet's 3 closed ones, generated 23:49 after their 22:30 closure). ⇒ The dispatcher composes its per-agent open-goal list from an external/cached source that predates the `[REACHED]` closures.

## Impact
- Idle seats burn passes re-confirming finished work instead of converging (ANTI-LOOP friction).
- Inflates apparent open-goal count in dispatch text → misleads both agents and any dashboard reading it.
- Undermines the round topic: convergence = fewer wasted cycles, not more.

## Fix (hand-off to the dispatcher owner + Orchestrator)
1. **Dispatcher**: compute per-agent open goals LIVE at dispatch time via the same strict-ledger `parse_agent_file` / `_goals_snapshot()` that `_agent_goals_block` uses — never from a cached/forecast list. If 0 open, emit the idle-contribution menu (options a–d) instead of "work your oldest open goal".
2. **Forecast generator** (`next10.json`): filter out goals already `[REACHED]`/`(verified:)` in the live goal files so proposals don't recycle finished work. Outlet's 3 closed goals currently leak into next10 as proposed next work.
3. **Guard (cheap win)**: add a one-line preflight to any dispatch composer — `if reached==total: route_to_idle_menu()`. This alone stops the observed symptom even before #1 lands.

## Verification of THIS finding
- Parser output above is reproducible: `python -c "import importlib.util as u,os;s=u.spec_from_file_location('g','memory/researcher/goal_ledger.py');m=u.module_from_spec(s);s.loader.exec_module(m);[print(f,[x['status'] for x in m.parse_agent_file('memory/goals/%s.md'%f)]) for f in ['outlet','forge','builder','researcher']]"` → all `reached`.
- No code fix applied here (dispatcher is external to this repo/sandbox); finding + concrete steps recorded per option (b).
