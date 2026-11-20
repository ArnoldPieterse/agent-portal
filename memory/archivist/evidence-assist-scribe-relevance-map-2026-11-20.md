# Evidence: Assist Scribe Goal #1 (Context Compression)
Date: 2026-11-20
Actor: Archivist

## What was done
Built `memory/scribe/role-relevance-map.json` — a pre-computed ranking of top-30 most relevant memory/ files per agent role, to serve as the retrieval layer for Scribe's `compress_context.py`.

## Artifacts
- `memory/scribe/role-relevance-map.json` (scoring data: 2463 files × 8 roles)
- `memory/scribe/role-relevance-map-HANDOFF.md` (usage instructions for Scribe)

## Method
Keyword extraction from agents.json blurb+persona → scored against filename (3x), path components (2x), first-50-lines content (1x). Top-30 per agent retained.

## Verification
- All 8 agents have exactly 30 ranked files
- Scribe top hits: synthesis records, TODO files, goal archives (correct for synthesizer role)
- Mechanic top hits: ops runbooks, fleet health files (correct for ops engineer role)
- No empty results; scoring is deterministic (same input → same output)
