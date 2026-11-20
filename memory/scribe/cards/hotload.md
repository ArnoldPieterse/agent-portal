# hotload - Reference Card

_Generated: 2026-11-20 | Sources: 20 files | Key facts: 145_

## Key Facts

1. `hotload_controller.py` (root) - ops automation for on-demand model load/unload across fleet hosts
   _Source: `memory\mechanic\hotload-controller-built-2026-11-17.md`_

2. `python hotload_controller.py status` -> reports all 4 hosts reachable/unreachable with error detail
   _Source: `memory\mechanic\hotload-controller-built-2026-11-17.md`_

3. `python hotload_controller.py select --agent researcher` -> correctly maps to qwen3-27b-q4 (score 8.8, ACTIVE)
   _Source: `memory\mechanic\hotload-controller-built-2026-11-17.md`_

4. memory/llm/hotload-plan.md      - architecture + phases (PLANNED, not built)
   _Source: `memory\goals\scheduler-cycle6.md`_

5. memory/llm/hotload-selector.md  - research + layer design (DRAFT)
   _Source: `memory\goals\scheduler-cycle6.md`_

6. memory/llm/hotload-catalog.json v1.0 - model registry: hosts / models / planned_models / agent_profile_templates
   _Source: `memory\goals\scheduler-cycle6.md`_

7. `hotload_controller.py` - added verify, swap, report subcommands + record_load_time
   _Source: `memory\mechanic\cycle6-hotload-progress-2026-11-18.md`_

8. python hotload_controller.py status          # model state all hosts
   _Source: `memory\mechanic\cycle6-hotload-progress-2026-11-18.md`_

9. python hotload_controller.py select --agent X  # best model for agent
   _Source: `memory\mechanic\cycle6-hotload-progress-2026-11-18.md`_

10. memory/archivist/hotload-research-evidence.md
   _Source: `memory\archivist\digest-47-2026.md`_

11. memory/mechanic/cycle6-hotload-pass-note.md
   _Source: `memory\archivist\digest-47-2026.md`_

12. memory/mechanic/cycle6-hotload-progress-2026-11-18.md
   _Source: `memory\archivist\digest-47-2026.md`_

13. Auto-select the right LLM model per task, hotload it at runtime without restart,
   _Source: `memory\designer\llm-router-architecture.md`_

14. Residency bonus: if the matched model is already loaded → score +0.2 (no hotload needed)
   _Source: `memory\designer\llm-router-architecture.md`_

15. If a remote has the capability → route request there (higher latency but no hotload)
   _Source: `memory\designer\llm-router-architecture.md`_

16. Focus: Hotload productionization + fleet capacity orchestration. Turn the PLANNED hot-LLM-loading design (memory/llm/hotload-plan.md, hotload-selector.md, hotload-catalog.json v1.0) into a FUNCTIONAL scheduler, grounded in the proven backend-swap pro
   _Source: `memory\goals\archive\orchestrator-2026-11-19.md`_

17. Hot LLM Loading Functions - Expansion + Functional - Take the prior hotload work (backend-swap-procedure.md, reload recipe in studio-api.md, hotload-catalog.json v1.0, model_load_params.json) and BUILD a functional `model_scheduler.py`: a `plan(targe
   _Source: `memory\goals\archive\orchestrator-2026-11-19.md`_

18. Hotload Execute Engine (live) - Extend model_scheduler.py with `execute(plan)` that drives the Studio API per host using the proven bodies from backend-swap-procedure.md: idle-gate (poll active-generations==0) -> load -> poll /models until resident (
   _Source: `memory\goals\archive\orchestrator-2026-11-19.md`_

19. Focus: Hotload productionization + fleet capacity orchestration. Turn the PLANNED hot-LLM-loading design (memory/llm/hotload-plan.md, hotload-selector.md, hotload-catalog.json v1.0) into a FUNCTIONAL scheduler, grounded in the proven backend-swap pro
   _Source: `memory\goals\archive\orchestrator-2026-11-20.md`_

20. Hot LLM Loading Functions - Expansion + Functional - Take the prior hotload work (backend-swap-procedure.md, reload recipe in studio-api.md, hotload-catalog.json v1.0, model_load_params.json) and BUILD a functional `model_scheduler.py`: a `plan(targe
   _Source: `memory\goals\archive\orchestrator-2026-11-20.md`_

21. Hotload Execute Engine (live) - Extend model_scheduler.py with `execute(plan)` that drives the Studio API per host using the proven bodies from backend-swap-procedure.md: idle-gate (poll active-generations==0) -> load -> poll /models until resident (
   _Source: `memory\goals\archive\orchestrator-2026-11-20.md`_

22. Wrote `hotload_exec.py` (root dir, 147 lines): full load→poll→probe→unload→verify cycle for quinn-q4 on White :8888.
   _Source: `memory\orchestrator\goal1-hotload-tier-a-2026-11-20.md`_

23. Ran `python hotload_exec.py --dry-run` → PASS (logic validated, no network side-effects).
   _Source: `memory\orchestrator\goal1-hotload-tier-a-2026-11-20.md`_

24. [x] Script exists at root: `hotload_exec.py`
   _Source: `memory\orchestrator\goal1-hotload-tier-a-2026-11-20.md`_

25. ONE task, `FleetHotLoad`, runs the unified loader (`memory/researcher/hot_load.py`) across all 4 hosts on a recurring trigger. It replaces the four divergent model-load tasks that each hardcode a different ctx value / resident-poll strategy / auth so
   _Source: `memory\researcher\fleet-hotload-watchdog-spec.md`_

## Sources (by relevance)

- `memory\scribe\memory-hygiene-report.json` (23 facts)
- `memory\mechanic\hotload-controller-built-2026-11-17.md` (16 facts)
- `memory\goals\scheduler-cycle6.md` (14 facts)
- `memory\mechanic\cycle6-hotload-progress-2026-11-18.md` (9 facts)
- `memory\archivist\digest-47-2026.md` (9 facts)
- `memory\designer\llm-router-architecture.md` (9 facts)
- `memory\goals\archive\orchestrator-2026-11-19.md` (8 facts)
- `memory\goals\archive\orchestrator-2026-11-20.md` (8 facts)
- `memory\orchestrator\goal1-hotload-tier-a-2026-11-20.md` (6 facts)
- `memory\researcher\fleet-hotload-watchdog-spec.md` (6 facts)
- `memory\llm\hotload-plan.md` (5 facts)
- `memory\ops\claim-phantom-report.md` (5 facts)
- `memory\researcher\INDEX.md` (5 facts)
- `memory\designer\llm-router-prototype-2026-11-17.md` (5 facts)
- `memory\llm\hotload-selector.md` (4 facts)
- `memory\archivist\hotload-research-evidence.md` (4 facts)
- `memory\goals\researcher.md` (4 facts)
- `memory\goals\orchestrator.md` (3 facts)
- `memory\goals\archive\verifier-2026-11-19.md` (1 facts)
- `memory\goals\archive\verifier-2026-11-20.md` (1 facts)