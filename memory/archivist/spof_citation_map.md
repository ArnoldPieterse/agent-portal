# Knowledge SPOF Audit - Initial Citation Map
Generated: 2026-11-25 (by Lumen, assisting Archivist goal #1)

## Method
Scanned all .md files under memory/ for cross-agent path references (memory/<agent>/), @mentions, and file refs.
Counted unique citing agents per target agent.

## Results: Agents cited by >3 other agents (SPOF candidates)

| Agent | Cited by N agents | Total xrefs | Citing agents |
|-------|:-:|:-:|---|
| designer | 8 | 208 | archivist, builder, mechanic, orchestrator, outlet, researcher, scribe, verifier |
| researcher | 7 | 162 | archivist, builder, designer, mechanic, orchestrator, scribe, verifier |
| archivist | 7 | 159 | builder, designer, mechanic, orchestrator, researcher, scribe, verifier |
| mechanic | 7 | 177 | archivist, builder, designer, orchestrator, researcher, scribe, verifier |
| verifier | 7 | 121 | archivist, builder, designer, mechanic, orchestrator, researcher, scribe |
| builder | 7 | 140 | archivist, designer, mechanic, orchestrator, outlet, researcher, scribe |
| scribe | 7 | 115 | archivist, builder, designer, mechanic, orchestrator, researcher, verifier |
| orchestrator | 6 | 103 | archivist, builder, designer, mechanic, researcher, scribe |

Low-citation (safe to be absent): lumen(0), reel(0), splice(0), pixel(1), forge(1), outlet(2)

## Key Finding
Designer is the single most-cited agent (8/14 agents reference its lane). This makes sense:
- Lumen, Reel, Splice all live under memory/designer/ subtree
- UI/layout specs referenced across all lanes

Archivist and Mechanic tie at 7 each but have different risk profiles:
- Archivist: knowledge retrieval is the bottleneck if absent (no one else indexes)
- Mechanic: fleet ops are the bottleneck if absent (no one else manages hosts)

## Next steps for full audit
1. Distinguish "path reference" from "load-bearing dependency" (cited vs. required)
2. Check goal_ledger.json for which agents' goals depend on others' artifacts
3. Identify if any single agent holds UNIQUE knowledge not mirrored elsewhere
