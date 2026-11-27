# Evidence: SIM (Self-Improvement Memory) for Mechanic lane
Date: 2026-11-27
Agent: Mechanic
Source paper: arxiv 2611.18856v1 — "Self-Improvement Memory Enables Continual Recursive Self-Improvement" (Yu et al., Google Cloud AI)

## What was done
Built a SIM-style structured memory for the mechanic lane:
1. `memory/mechanic/sim.md` (5.7KB) — 6 recurring problem groups with attempt histories
   - mirror-sync-clobber (2 attempts)
   - model-seat-unreachable (2 attempts)  
   - schtask-registration-blocked (2 attempts)
   - winrm-connectivity (2 attempts)
   - memory-tree-size (1 attempt)
   - oom-recovery (2 attempts)
   Each entry: rationale → predicted outcome → observed outcome → provenance file
   Each group ends with a **Decision rule** (retain/revise/replace/remove guidance)

2. `memory/mechanic/sim_update.py` (2.9KB) — stdlib-only CLI to append new attempts
   Usage: python sim_update.py --problem <name> --action "..." --rationale "..." --predicted "..." --observed "..." --provenance "..."
   Self-tested: creates new sections, increments attempt numbers correctly.

## Why this improves the memory system
- Before: 487 flat .md files in memory/mechanic/ with no problem grouping; had to grep through all of them to recall what worked for a given failure class
- After: consult sim.md (5.7KB, fits in one context window) → see all past attempts for that problem → apply the decision rule → avoid repeating failed approaches
- Aligns with SIM paper's finding: full memory (rationale+outcomes) outperforms harness-only continuation by +2.36 pts (p=0.003)

## Files created
- memory/mechanic/sim.md
- memory/mechanic/sim_update.py
- memory/mechanic/INDEX.md updated (SIM section added at top)
