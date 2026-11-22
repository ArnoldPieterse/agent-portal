# Fleet Decision Digest - 2026-11-23

**Period:** all-time (first digest)  
**Total decisions:** 32  
**Rollbacks/corrections:** 3

## Thematic Summary

### General (10 decisions)

- [2026-11-14] Amended N≥1 bracket ratified; destructive-clean independently rejected (Verifier r28/r30, verified first-party on Orchestrator's seat)
- [2026-11-14] 7. r27 N-semantics adopted as option (a); amended bracket ratified; probe canon = r21 (Researcher lane closure)
- [2026-11-12] # Decision 1 — 2026-11-12
- [2026-11-12] # Decision 2 — 2026-11-12
- [2026-11-12] # Decision 3 — 2026-11-12
- ...and 5 more in this theme

### Memory Hygiene (7 decisions)

- [2026-11-13] 7. Per-agent module hygiene (O3-ratified pattern): keep memory/<id /MEMORY.md + TODO.md pairs current; flag drift in other agents' modules rather than
- [2026-11-13] 6. [Orchestrator or Researcher] O5: close the orphan-leaves direction only — broken-arrow side already PASS at efbf4af from two independent seats (Orc
- [2026-11-13] O5 [Orchestrator or Researcher] close the orphan-leaves direction only (broken-arrow side already PASS at efbf4af from two seats: 44/44 + 37/37) + lan
- [2026-11-14] 6. memory/agents/INDEX (.md) dangling-ref flag RESOLVED as historical-only — superseded proposal per workspace/INDEX.md L46; ratified registry = per-a
- [2026-11-16] Archivist: 249/324 orphan backlog — proposed batch-index by agent folder OR superseded/archive convention; offered to draft either (Archivist msg). Ow
- ...and 2 more in this theme

### Operational Resilience (6 decisions)

- [policy] [R001] model_oom: Unload the OOM'd model and load a lower-quantization or smaller model in its place
- [policy] [R004] vram_pressure_sustained: Migrate the lowest-priority agent's model to another host to relieve pressure
- [policy] [R002] host_unreachable: Reassign all agents bound to the down host to the next available host with sufficient capacity
- [policy] [R003] agent_unresponsive: Reassign the agent's pending tasks to the next available agent with matching capability; mark agent as degraded in cockpit
- [policy] [R005] disk_space_critical: Prune old log files, clear __pycache__, archive completed cycle artifacts to cold storage; if still below 5%, halt new mod
- ...and 1 more in this theme

### Portal Ui (3 decisions)

- [2026-11-14] Mechanic proposes setting up a schtasks PortalRun for auto-recovery . Owner not yet assigned; if adopted, Mechanic (ops) is natural owner, Arnold appr
- [2026-11-16] Decision: evolution CLI as agents.json tool for Builder/Verifier lanes [owner: Builder]
- [2026-11-14] # Decision 9 — 2026-11-14

### Projects (3 decisions)

- [2026-11-14] # Decision 10 — 2026-11-14
- [2026-11-14] # Decision 13 — 2026-11-14
- [2026-11-14] # Decision 14 — 2026-11-14

### Goal Management (2 decisions)

- [2026-11-18] | Orchestrator | 10/10 | 0 | All goals verified; seat-drafted set ratified by completion |
- [unknown] No slippage: all goals closed within the cycle window. Cycle 5 focus: new features per ratified goal-set

### Agent Ops (1 decisions)

- [2026-11-13] # Decision 8 — 2026-11-13

## Corrections & Rollbacks

- [2026-11-14] **ROLLED BACK:** Amended N≥1 bracket ratified; destructive-clean independently rejected (Verifier r28/r30, verified first-party on Orchestrator's seat)
- [2026-11-14] **ROLLED BACK:** 6. memory/agents/INDEX (.md) dangling-ref flag RESOLVED as historical-only — superseded proposal per workspace/INDEX.md L46; ratified registry = per-a
- [2026-11-16] **ROLLED BACK:** Archivist: 249/324 orphan backlog — proposed batch-index by agent folder OR superseded/archive convention; offered to draft either (Archivist msg). Ow

## Notable Patterns

- Memory hygiene dominated with 7 decisions - the fleet is stabilizing its knowledge architecture.
- 3 corrections detected, indicating active self-correction in the decision process.
- Portal/UI work accounts for 3 decisions - frontend is an active investment area.
