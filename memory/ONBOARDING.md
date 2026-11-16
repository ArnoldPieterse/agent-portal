# Agent Onboarding Knowledge Pack

> Auto-generated skeleton from memory/INDEX.md (2026-11-16). Regenerate on index change.
> Target read time: <15 min. Use this to orient, then grep for specifics.

## 1. What This Fleet Is

A multi-agent AI system (8 agents) running on a 4-host Windows fleet (White/Red/Pale/Black).
- **White** = primary host; runs agent_portal.py (:8099), all shared files live here.
- **Red/Pale/Black** = LLM inference hosts (LM Studio :8888 or filtered proxies); also SMB-mirrored for file access.
- The portal serves the group chat UI, API endpoints, and file links to the human via relative paths.

## 2. Directory Tree (what lives where)

```
<working-dir>/
├── agent_portal.py          # Portal server (:8099) - routes, handlers, state
├── agents.json              # Agent profiles: model_id, temperature, tools, max_tool_calls
├── index.html               # Frontend (Solo/Group modes, cross-talk loop)
├── user_messages.json       # Human message queue (auto-injected per agent)
├── MEMORY.md                # HOT FILE - state line + recent notes (keep small!)
├── TODO.md                  # Work plan - newest section at TOP
├── memory/                  # All persistent knowledge, modular by topic
│   ├── INDEX.md             # ROOT POINTER MAP - start here for any lookup
│   ├── portal/              # Portal bugs, architecture, API reference
│   │   └── INDEX.md
│   ├── llm/                 # LLM instances, routing, dual residency, reload recipe
│   │   └── INDEX.md
│   ├── ops/                 # Windows ops: reboot runbook, portal lifecycle, probes
│   │   └── INDEX.md
│   ├── goals/               # Fleet goal lists (canonical = TODO.md AGENT GOALS)
│   │   └── INDEX.md
│   ├── synthesis/           # Scribe synthesis leaves + supersession chain
│   │   └── INDEX.md
│   ├── projects/            # Project areas (dcabots, evolution layer)
│   │   └── INDEX.md
│   ├── handoffs/            # Cross-agent knowledge handoff protocol + log
│   ├── archivist/           # Archivist scripts: KG, decay, snapshots, gates
│   ├── builder/             # Builder work evidence
│   ├── designer/            # Designer critiques + design tokens
│   ├── mechanic/            # Mechanic fleet ops evidence
│   ├── orchestrator/        # Orchestrator decisions
│   ├── researcher/          # Researcher findings
│   ├── scribe/              # Scribe synthesis outputs
│   ├── verifier/            # Verifier test evidence
│   └── workspace/           # Scratch / in-progress work
├── reports/                 # Generated PDFs and reports
└── archivist/               # (same as memory/archivist - scripts live here too)
```

## 3. Core Conventions

### File Access Rules
- ALL shared files are in your working directory. Read/write with python/terminal tools.
- Files are kept fresh by White: per-chat-turn sync + 5-min SMB mirror to Red/Pale/Black.
- If a file is stale or missing, ask Orchestrator or Researcher to relay.
- **Report created files as RELATIVE paths only** (e.g. `memory/portal/api-reference.md`).
- NEVER use drive letters or absolute paths in chat - they 404 on the portal.

### Memory Discipline
- `MEMORY.md` is a HOT FILE: state line + counter + recent notes ONLY. Keep it small.
- `TODO.md`: newest section at TOP. The LIVE PLAN section is the current work plan.
- `memory/INDEX.md` is the pointer map. Grep by keyword; open ONE leaf per question.
- Never paste whole modules into chat. Reference by path.

### Supersession
- When a document replaces another, mark it: `supersedes <old-file>` or `replaced by <new-file>`.
- The supersession validator (`archivist/supersession_check.py`) checks chains are acyclic.
- Dead (superseded) leaves are flagged for archival but NOT auto-deleted.

### Agent Communication
- Group chat: all agents see all messages. Address by name to target.
- Private: `[DM @Name] ...` sends text only that agent can see.
- Cross-talk budget: unlimited this cycle (was 6 per prompt in earlier cycles).
- End discussions with `[CONCLUDED]` when settled; `[SILENT]` when nothing new.

### Goal System
- Each agent has 10 goals per cycle, stored in `memory/goals/<name>.md`.
- Canonical goal list = TODO.md `## AGENT GOALS` section.
- Mark progress with evidence: file paths, script outputs, verification results.
- Cycle 2 started 2026-11-16; cycle 1 archived to `memory/goals/archive/`.

## 4. Where to Find What (quick lookup)

| I need... | Go to... |
|-----------|----------|
| Current work plan | TODO.md (top section) |
| Fleet state / what's happening now | MEMORY.md (state line) |
| Portal API endpoints | memory/portal/api-reference.md (auto-generated) |
| How LLM routing works | memory/llm/INDEX.md |
| Reboot recovery steps | memory/ops/INDEX.md → reboot runbook |
| My goals + status | memory/goals/<my-name>.md |
| All agents' goals | TODO.md `## AGENT GOALS` section |
| Project context (dcabots etc) | memory/projects/INDEX.md |
| Latest synthesis / decisions | memory/synthesis/INDEX.md |
| Design tokens / UI state | memory/designer/INDEX.md |
| Fleet health / probe results | memory/mechanic/INDEX.md |
| Cross-agent handoff protocol | memory/handoffs/PROTOCOL.md |
| Knowledge freshness status | archivist/freshness-report.md |
| Supersession chain report | archivist/supersession-report.json |

## 5. Key Scripts (archivist/)

| Script | Purpose |
|--------|---------|
| `knowledge_graph.py` | Walks all leaves → JSON dependency graph + text view |
| `memory_health.py` | Per-leaf staleness vs TTLs; freshness-report.md |
| `gen_api_ref.py` | Parses agent_portal.py routes → api-reference.md; gate on drift |
| `supersession_check.py` | Validates supersession chains (acyclic, living terminus) |
| `decay_score.py` | Scores leaves on recency × reference density × linkage |
| `snapshot.py` | Hashes all leaves into manifests; --diff shows changes |
| `index_check.py` | Verifies INDEX.md pointers resolve to real files |

## 6. Portal Architecture (30-second summary)

- **Server**: agent_portal.py, port 8099, Python http.server based.
- **Key endpoints**: /api/chat (group messages), /api/memory (file read/write), /api/file (serve files), /api/goals (goal state), /api/health/fleet (fleet status).
- **Frontend**: index.html - Solo mode (1 agent) or Group mode (all 8 + cross-talk).
- **Message flow**: Human types → user_messages.json queue → portal injects into next agent prompt → agent responds → group chat.
- **File serving**: Portal serves both the shared agent folder and memory/ by relative path.

## 7. First Things to Do When You Join

1. Read this file (you're doing it now).
2. Open `memory/INDEX.md` - grep for your domain.
3. Check TODO.md top section for current work plan.
4. Check MEMORY.md state line for fleet status.
5. Read your goals in `memory/goals/<your-name>.md`.
6. If you have tools: run `python archivist/index_check.py` to verify index integrity.
7. Start working on your highest-priority open goal.

---
*Generated 2026-11-16 by Archivist (goal 8). Regenerate when memory/INDEX.md changes.*

<!-- auto-generated skeleton note 2026-11-16: tree + conventions sections regenerate from memory/INDEX.md and lane INDEX files on index change (archivist cycle-2 goal 8). Current length 1029 words ~= 5 min read (<15 min target met). -->
