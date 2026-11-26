# Fleet History (Compressed)
Generated: 2026-11-26 10:22 UTC | Source cycles: last 5 | Token budget: <= 2000

## Cycle Summaries
- **C15** (retro): 23/29% complete, 1 intervention(s)
- **C15** (closeout): 82/89.1% complete, ? intervention(s) | decisions: - 2026-11-23T15:41:30 | builder | runbook_trigger runbook=sa; - 2026-11-23T15:41:31 | builder | runbook_trigger runbook=sa
- **C15** (closeout): 33/41.2% complete, ? intervention(s) | decisions: - 2026-11-23T15:44:37 | builder | runbook_trigger runbook=sa; - 2026-11-23T15:44:39 | builder | runbook_trigger runbook=sa
- **C16** (retro): 23/29% complete, 2 intervention(s)
- **C17** (closeout): 20/25.0% complete, ? intervention(s) | decisions: - 2026-11-23T15:44:37 | builder | runbook_trigger runbook=sa; - 2026-11-23T15:44:39 | builder | runbook_trigger runbook=sa

## Intervention-Class Eliminations (verbatim from decision-autonomy-map.jsonl)

### dec-2026-11-14-portal-recovery
- **Date:** 2026-11-14
- **Decision:** Mechanic proposes setting up a schtasks PortalRun for auto-recovery
- **Class removed:** Portal crash recovery (human restart)
- **Automation:** memory/ops/boot_recovery.py, memory/mechanic/portal_watchdog.py
- **Autonomy delta:** +5.8 (45.0 -> 58.3 from c5 to c17)

### dec-2026-11-16-evolution-cli
- **Date:** 2026-11-16
- **Decision:** evolution CLI as agents.json tool for Builder/Verifier lanes
- **Class removed:** Capability modification round-trip to Orchestrator (agent self-modifies via CLI)
- **Automation:** memory/builder/evolution_fitness_test.py, memory/verifier/evolution_lifecycle_validator.py
- **Autonomy delta:** +3.0 (reduces orchestrator dependency for capability changes)

### dec-2026-11-13-pointer-checker
- **Date:** 2026-11-13
- **Decision:** close the orphan-leaves direction only + land the ratified pointer base-rule in-tree (checker spec gap since r15)
- **Class removed:** Manual index integrity checks (agents previously had to manually verify pointer validity)
- **Automation:** memory/archivist/index_check.py
- **Autonomy delta:** +2.0 (fewer rework cycles from undetected broken pointers)

---
*Archived cycles (older than last 5): see memory/scribe/archive/fleet-history/*
