# Competitive Feature Scan — Multi-Agent Fleet Management Systems
**Date:** 2026-11-18 | **Analyst:** Researcher | **Next due:** 2027-Q1 (quarterly)

## Scope
Three comparable multi-agent orchestration/management systems, compared against our
`agent_portal.py` fleet portal on feature parity and gap identification.

---

## System 1: CrewAI AMP (Agent Management Platform)

**Source:** https://docs-platform.crewai.com/platform/en/introduction
           https://crewai.com/agent-management-platform
           https://blog.crewai.com/crewai-amp-the-agent-management-platform/

### Fleet-Management Features
| Feature | Description |
|---------|-------------|
| Centralized control plane | Monitor every agent run in real-time; performance & outcome visibility in one dashboard |
| Agent registry | Discover, version, and redeploy agents from a unified catalog |
| No-code Studio | Visual builder for agent crews/flows without writing code |
| Observability integrations | Third-party observability (growing ecosystem); trace-level debugging |
| Checkpointing | SQLite-backed `@persist` decorator for state persistence between runs |
| Process modes | Sequential, hierarchical, consensus execution patterns |
| Planning agent | Meta-planning agent generates step-by-step plans before task execution |
| RBAC / Workspaces | Enterprise access control and team isolation |
| Auto-discovery | "CrewAI Discovery" scans tickets/chats/apps to rank automation opportunities |

### Architecture Notes
- Role-based team model (agents have role/goal/backstory)
- Task assignment is declarative; orchestrator decides execution order
- Black-box orchestration: limited fine-grained control over routing
- Single-process focus; horizontal scaling less mature than LangGraph

---

## System 2: LangGraph Platform / LangSmith Deployment

**Source:** https://www.langchain.com/blog/langgraph-platform-ga
           https://www.langchain.com/langsmith/deployment
           https://www.langchain.com/langsmith/observability

### Fleet-Management Features
| Feature | Description |
|---------|-------------|
| 1-click deployment | GitHub integration; select repo → ship in minutes |
| Agent registry | Discover available agents; version as "assistants" for reuse |
| Remote Graphs | Compose multi-agent architectures that run distributed across services |
| LangGraph Studio | Visual IDE: real-time trajectory view, branching logic, retry inspection |
| Checkpointing | SQLite/Postgres/Redis backends; supports rewind, edit, re-run failure points |
| Human-in-the-loop | Native `interrupt()` pattern for approval gates mid-workflow |
| Persistence layer | Memory, conversational history, async collaboration state |
| Horizontal scaling | Handles bursty, long-running traffic (serverless deployment) |
| LangSmith observability | Best-in-class tracing; cost/latency tracking; failure-mode analysis via Insights Agent |
| RBAC / Workspaces | Enterprise access control; workspace isolation |
| 30 API endpoints | Design custom user experiences over the agent runtime |

### Architecture Notes
- Explicit directed graph with cyclical state (deterministic, auditable)
- State object serialized at each step → full checkpointing granularity
- Largest LLM/tool ecosystem (500+ LangChain integrations, 20+ providers)
- Deployment options: SaaS, hybrid (SaaS control + self-hosted data), fully self-hosted

---

## System 3: Microsoft Agent Framework 1.0 (ex-AutoGen)

**Source:** https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/
           https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-autogen/
           https://turion.ai/blog/langgraph-vs-crewai-vs-autogen-comparison-2026/

### Fleet-Management Features
| Feature | Description |
|---------|-------------|
| AgentSession | Persistent conversation state across agent interactions |
| GraphFlow | Explicit workflow control (parallel to LangGraph's StateGraph) — new in 1.0 |
| MCP server support | Standardized tool integration via Model Context Protocol |
| A2A protocol | Agent-to-Agent interoperability protocol (native) |
| MagenticOneGroupChat | Automated task decomposition + result synthesis across agent groups |
| RoundRobinGroupChat | Structured multi-agent conversation with termination conditions |
| Azure Monitor integration | Enterprise observability; traces, metrics, alerts |
| Dual-language SDK | .NET and Python parity (unique in the space) |
| Hosted tools | Azure-native execution environment for agent tool calls |
| Responses API support | OpenAI Responses API format bridge (conversational ↔ imperative) |

### Architecture Notes
- Conversational multi-agent; emergent behavior from message patterns
- Unified AutoGen + Semantic Kernel into single production SDK (GA April 3, 2026)
- Cost amplification: round-robin chat = N× tokens vs sequential handoff
- Less deterministic than LangGraph; more flexible for exploratory tasks

---

## Our Portal — Current Feature Inventory

**Source:** agent_portal.py endpoint scan + memory/goals/ + ui/core.js

| Category | Endpoints / Features |
|----------|---------------------|
| Fleet status | `/api/fleet`, `/api/fleet/capacity`, `/api/fleet/roster-diff`, `/api/health/fleet` |
| Agent management | `/api/agents`, `/api/models`, `/api/models/status` |
| Goals/tasks | `/api/goals`, `/api/goals/history`, `/api/goals/slip-risk`, `/api/goals/timeline` |
| Chat/collaboration | `/api/chat`, `/api/group-run`, `/api/autoloop` |
| Memory/knowledge | `/api/memory`, `/api/memory-health`, `/api/memory/file`, `/api/kb/search`, `/api/knowledge-bases` |
| Activity/audit | `/api/activity`, `/api/history`, `/api/decisions` |
| Network probes | `/api/net/dns`, `/api/net/fleet`, `/api/net/http`, `/api/net/latency`, `/api/net/probe` |
| Evolution layer | `/api/evolution/accept`, `/api/evolution/reject`, `/api/evolution/stats` |
| File management | `/api/file`, `/api/file/raw`, `/api/git`, `/api/manifest` |
| Inference status | `/api/inference/status`, `/api/inference/active-generations` |
| Merge queue | `/api/merge`, `/api/merge-queue` |
| Ops | `/api/ops` |

---

## Gap Analysis Table

| Feature Dimension | CrewAI AMP | LangGraph Platform | MS Agent Framework | **Our Portal** | Gap? |
|-------------------|-----------|-------------------|--------------------|---------------|------|
| Agent registry + versioning | ✅ (AMP) | ✅ ("assistants") | ⚠️ (AgentSession, no formal registry) | ⚠️ (`/api/agents` exists; no versioning) | **Partial** — no agent version history |
| Real-time run monitoring | ✅ (centralized) | ✅ (LangSmith + Studio) | ⚠️ (Azure Monitor) | ⚠️ (`/api/health/fleet`, `/api/inference/status`) | **Partial** — status endpoints exist; no per-run trace view |
| Visual workflow IDE | ✅ (No-code Studio) | ✅ (LangGraph Studio) | ❌ | ❌ | **Gap** — no visual graph/tracer UI |
| Checkpointing / state persistence | ✅ (SQLite @persist) | ✅ (SQLite/Postgres/Redis) | ⚠️ (AgentSession) | ⚠️ (memory files, git) | **Partial** — file-based, not structured checkpoint store |
| Human-in-the-loop gates | ⚠️ (task delegation) | ✅ (native interrupt()) | ⚠️ (request-response) | ✅ (chat DM + group-run) | **Parity** — chat-based interaction is our equivalent |
| Horizontal scaling / multi-node | ❌ (single-process) | ✅ (serverless) | ✅ (.NET native) | ⚠️ (4-host fleet, manual) | **Gap** — no auto-scaling; manual capacity mgmt via `/api/fleet/capacity` |
| Observability / tracing | ⚠️ (growing) | ✅ (best-in-class LangSmith) | ⚠️ (Azure Monitor) | ⚠️ (`/api/activity`, evidence files) | **Gap** — no structured trace/span; file-based logging only |
| RBAC / multi-tenancy | ✅ (AMP enterprise) | ✅ (enterprise tier) | ⚠️ (Azure AD) | ❌ | **Gap** — single-user model currently |
| Goal/task tracking | ❌ (not a feature) | ❌ (not a feature) | ❌ (not a feature) | ✅ (`/api/goals`, slip-risk, timeline, history) | **Our differentiator** — purpose-built goal lifecycle |
| Agent auto-discovery / routing | ✅ (CrewAI Discovery) | ⚠️ (Remote Graphs) | ⚠️ (A2A protocol) | ⚠️ (goal router planned: `/api/research/route`) | **Gap** — router in progress, not shipped |
| Evolution / self-modification | ❌ | ❌ | ❌ | ✅ (`/api/evolution/*`) | **Our differentiator** — unique to our fleet |
| Network health probes | ❌ | ❌ | ❌ | ✅ (`/api/net/*` suite) | **Our differentiator** |
| Memory/knowledge base | ⚠️ (crew context mgmt) | ✅ (persistence layer) | ⚠️ (AgentSession) | ✅ (`/api/memory`, `/api/kb/search`) | **Parity** — comparable |
| Deterministic workflow control | ❌ (black-box) | ✅ (explicit graph) | ⚠️ (GraphFlow new in 1.0) | ❌ (chat-driven) | **Gap** — no explicit state-graph; emergent via chat |
| MCP / A2A interop | ❌ | ⚠️ (MCP via LangChain tools) | ✅ (native) | ❌ | **Gap** — no standardized inter-agent protocol |

---

## Key Findings

1. **We are differentiated on goal lifecycle + evolution layer.** No competitor has a purpose-built
   goal-tracking system with slip-risk prediction, timeline views, or a self-modification pipeline.
   This is our unique value proposition.

2. **Our biggest gaps are in observability and workflow control.** LangGraph's explicit state-graph
   with checkpointing and LangSmith tracing is the industry benchmark. Our file-based memory + chat-driven
   orchestration works for a 4-host fleet but won't scale to larger agent counts without structured
   tracing and deterministic routing.

3. **Auto-scaling is an infrastructure gap.** All three competitors offer some form of horizontal scaling.
   Our manual capacity management (`/api/fleet/capacity`) is fine at current scale (4 hosts) but becomes
   a bottleneck as the fleet grows.

4. **MCP/A2A standardization is emerging as table-stakes.** Microsoft Agent Framework ships both natively;
   LangGraph has MCP via LangChain tools. Adopting even one of these protocols would improve inter-agent
   interoperability without a full architecture rewrite.

## Recommendations (next 2 quarters)

| Priority | Action | Effort | Rationale |
|----------|--------|--------|-----------|
| P1 | Add structured per-run tracing (JSON spans with parent/child + timing) to `/api/activity` | Medium | Closes observability gap without full LangSmith clone |
| P1 | Ship the goal router (`/api/research/route`) — already in progress (Goal #6) | Low (in flight) | Parity with CrewAI Discovery for task assignment |
| P2 | Agent version history on `/api/agents` (git-backed, like our existing file system) | Medium | Closes registry/versioning gap; leverages existing git infra |
| P2 | Evaluate MCP server support for tool integration | Research | Future-proofing; low immediate ROI at 4-host scale |
| P3 | Structured checkpoint store (SQLite per-agent state snapshots) | High | Only needed if fleet grows >8 agents or we need rewind/re-run |

---

## Sources
1. https://turion.ai/blog/langgraph-vs-crewai-vs-autogen-comparison-2026/ (May 2026)
2. https://www.langchain.com/blog/langgraph-platform-ga (May 2025, GA announcement)
3. https://docs-platform.crewai.com/platform/en/introduction
4. https://crewai.com/agent-management-platform
5. https://blog.crewai.com/crewai-amp-the-agent-management-platform/ (Oct 2025)
6. https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/ (April 2026)
7. https://deepwiki.com/crewAIInc/crewAI/10-enterprise-features-(crewai-amp)
8. Local: agent_portal.py endpoint inventory (2026-11-18 scan)
