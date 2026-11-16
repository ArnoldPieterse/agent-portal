# MEMORY INDEX — root dictionary. Grep by keyword; open ONE leaf.
Updated: 2026-11-16.

## FILE ACCESS
- TODO.md, MEMORY.md, memory/, agents.json, agent_portal.py ARE in your working dir - read via python/terminal tools; White keeps fresh. Stale -> ask Orchestrator/Researcher to relay. Tool writes land in the SHARED AGENT FOLDER (sandbox); portal serves BOTH roots by relative path. Report created files EXACTLY as that relative path - never drive letters (404).

## Sub-indexes
- -> memory/portal/INDEX.md   portal bugs + architecture (DM/uploads/sync, prune+git)
- -> memory/llm/INDEX.md      LLM instances: dual residency, aliases, reload recipe, hosts
- -> memory/ops/INDEX.md      Windows ops: reboot recovery, portal lifecycle, probes
- -> memory/goals/INDEX.md    fleet goal lists (canonical = TODO.md AGENT GOALS)
- -> memory/synthesis/INDEX.md   Scribe synthesis leaves (supersession chain)
- -> memory/projects/INDEX.md   dcabots DCA bot + evolution layer

## Global files
- -> agent_portal.py          server :8099; /api/* endpoints; GET /ui/* UI modules
- -> agents.json              profiles (model_id alias, tools[], max_tool_calls)
- -> index.html               frontend shell (markup only); UI in ui/; HARD-REFRESH after edits
- -> MEMORY.md                HOT FILE ONLY (state line + counter + notes); keep small
- -> TODO.md                  work plan, newest section at top
