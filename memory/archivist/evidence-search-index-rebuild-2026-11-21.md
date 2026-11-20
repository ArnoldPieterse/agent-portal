# Search Index Rebuild - 2026-11-21

## Context
search-index.json was found corrupted (3 entries in wrong format, likely overwritten by another process).
Rebuilt from scratch to restore fleet retrieval capability.

## What ran
Python inline script: walked memory/ tree, extracted title/summary/keywords/agent for each .md leaf (>50 chars),
wrote compact JSON with array-of-fields format to minimize size.

## Results
- 2025 leaves indexed (all non-trivial .md files in memory/, excluding archive/levels/workspace)
- Size: 422.8 KB (target <500KB: PASS)
- Search verification:
  - 'decay' -> top-2 correct (decay-schtask-setup.md, decay-report.md)
  - 'schtask' -> top-3 correct (synthesis note, ops limitation, mechanic goal4)
  - 'pin' -> top-3 correct (synthesis check, scribe advance, researcher correction)

## Format
Each entry: [title, summary_40ch, [5_keywords], agent_tag] keyed by relative path.
Meta: n=count, g=date

## File
memory/archivist/search-index.json (422.8 KB)
