# Archivist Assist: Agent Relevance Map (2026-11-20)

**Goal assisted:** Scribe #2 - Context Compression for New Agents
**Artifact:** memory/scribe/agent-relevance-map-2026-11-20.json

## What was done
Built a keyword-overlap relevance map: for each of the 8 agents, scored all 6,291 indexed
memory files by overlap between the agent's role description + goal titles and each file's
name tokens (weighted x3) + content head tokens. Top-15 files per agent saved to JSON.

## How Scribe can use this
For `compress_context.py --agent <name>`:
1. Load the relevance map for that agent
2. Read the top-N files (start with N=10, expand if briefing < 500 tokens)
3. Compress into <2000-token briefing per Scribe's spec

## Quality note
- Top results are sensible: each agent's own goals file ranks #1, followed by their
  personal memory/ subdirectory and recent cycle evidence.
- Cross-agent bleed is expected (e.g., orchestrator sees researcher goals) - Scribe's
  compression step should filter to role-relevant content only.
- Files >50KB were skipped from content indexing (name tokens still counted).

## Limitations
- Pure lexical overlap; no semantic understanding of "relevance"
- Does not account for file freshness (a stale file may rank high on keywords)
  - Scribe should cross-reference with freshness_report.py output before including
