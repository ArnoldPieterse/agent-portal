# Evidence: Goal 9 - Knowledge SPOF Audit
**Date:** 2026-11-25
**Goal:** Map which agents' knowledge is most frequently cited by others; identify SPOF agents.

## What ran
- Cross-agent citation scan of all .md/.json/.py/.jsonl files under memory/ (14 agent lanes)
- Built dependency matrix: 14x14 cross-reference counts
- Identified top-cited specific files per agent
- Classified risk tiers: HIGH (researcher, mechanic, designer), MEDIUM (verifier, scribe, builder, orchestrator), LOW (archivist), ISOLATED (forge, lumen, reel, splice)

## Key findings
- 8 agents are cited by all 7 other major agents (no single hard SPOF >3 in strict sense since all top-8 break 7 others)
- researcher/goal_ledger.py is the most critical single artifact (x195 cross-agent refs)
- designer has highest total volume (25,524 cross-agent refs) driven by baseline/ + breakpoint-evidence/
- 4 agents (forge, lumen, reel, splice) are invisible to the fleet (0 cross-agent inbound refs)

## Artifact
- memory/archivist/knowledge-spf-audit.md (7,589 bytes, full matrix + recommendations)
