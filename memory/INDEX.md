# MEMORY INDEX — root dictionary (index of indexes). Grep by keyword; open ONE leaf per question.
Last updated: 2026-11-14.

## FILE ACCESS — link rule for ALL agents with tools
- TODO.md, MEMORY.md, memory/, agents.json, agent_portal.py ARE in your working dir - read them with python/terminal tools. Kept fresh by White: per-chat-turn sync + 5-min SMB mirror (Red/Pale/Black); if stale/missing, ask Orchestrator/Researcher to relay.
- Tool writes land in the SHARED AGENT FOLDER (sandbox _default); portal serves BOTH roots by relative path.
- Report created files EXACTLY as the relative path in your tool result (calculator-app/index.html). NEVER drive letters/absolute paths - they 404.

## Sub-indexes (index of indexes)
- -> memory/portal/INDEX.md   portal bugs (file-links, xtalk, UI) + architecture (DM/uploads/sync, prune+git ops)
- -> memory/llm/INDEX.md      LLM instances/routing: dual residency, aliases, reload recipe, Studio API :8888, hosts Red/Pale/Black
- -> memory/ops/INDEX.md      Windows ops: reboot recovery runbook, portal lifecycle, ground-truth checks, probe scripts
- -> memory/goals/INDEX.md    fleet goal lists 2026-11-13: 8 agents x 10 goals verbatim (canonical = TODO.md AGENT GOALS section)
- -> memory/synthesis/INDEX.md   Scribe synthesis leaves (supersession chain: upgrade-round < consolidated-state; planning-meeting < v102)
- -> memory/projects/INDEX.md   project areas: dcabots DCA bot (canonical leaf = projects/dcabots on White; C1/C2 closed)

## Global files (shared by all folders)
- -> agent_portal.py          server :8099; /api/chat, /api/memory, /api/file(+raw)
- -> agents.json              agent profiles: model_id alias, temperature, reasoning, tools[], max_tool_calls
- -> index.html               frontend: Solo/Group, cross-talk loop, ■ Stop, ↺ Reset; HARD-REFRESH after edits
- -> MEMORY.md                HOT FILE ONLY (state line + counter + recent notes); keep it small
- -> TODO.md                  work plan, newest section at top
