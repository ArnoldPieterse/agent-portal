# Portal Split Seam Plan (2026-11-17)

Parent: memory/ops/INDEX.md | Owner: Builder
agent_portal.py = 4194 lines / 209 KB. Target: modules under a single entry point; PortalRun task keeps working.

## Strategy
Extract leaf modules first (fewest cross-imports), keep `agent_portal.py` as the thin entry that imports + runs Handler.
Each new module gets a header pointer to this file + parent INDEX.

## Seams (ordered by safety - do in this sequence)
| # | Module file | Lines | Est KB | Deps on other modules |
|---|------------|-------|--------|----------------------|
| 1 | portal/config.py | 140 | ~7 | none (pure constants/helpers) |
| 2 | portal/umq.py | 94 | ~5 | config |
| 3 | portal/safety.py | 82 | ~4 | config |
| 4 | portal/rag.py | 55 | ~3 | config, safety |
| 5 | portal/fleet_perf.py | 269 | ~13 | config |
| 6 | portal/memory_state.py | 430 | ~21 | config, safety |
| 7 | portal/sandbox_sync.py | 310 | ~15 | config, memory_state |
| 8 | portal/agents_prompt.py | 718 | ~35 | config, memory_state, rag |
| 9 | portal/chat_stream.py | 280 | ~14 | config, agents_prompt, umq |
| 10 | portal/group_run.py | 582 | ~28 | chat_stream, agents_prompt, autoloop |
| 11 | portal/autoloop.py | 378 | ~19 | group_run, memory_state |
| 12 | portal/api_snapshots.py | 459 | ~22 | fleet_perf, memory_state, config |
| 13 | portal/handler.py | 720 | ~35 | ALL (imports every module) |

Entry: `agent_portal.py` shrinks to ~30 lines (import handler; if __name__ == '__main__': run).

## Rules
- Each module < 8 KB target (split further if larger: agents_prompt -> agents.py + prompt_builder.py)
- No circular imports: dependency graph is strictly downward
- `portal/__init__.py` re-exports for backward-compat during transition
- PortalRun schtask command unchanged (still runs agent_portal.py)
- After each extraction: run api_contract_test.py + pre_commit_gate.py before committing

## Risk notes
- handler_main (720 lines) is the biggest single unit; if >8 KB after import cleanup, split into handler_api.py + handler_ui.py
- agents_prompt is 35 KB - will need 2-3 sub-modules at minimum
- group_run + autoloop are tightly coupled (shared state); extract together or keep in one module

## Verification gate per step
1. `python -c "from portal import config"` (import smoke)
2. `python api_contract_test.py` (no API drift)
3. `python pre_commit_gate.py` (all 4 suites pass)
4. Portal restart + /api/health 200
