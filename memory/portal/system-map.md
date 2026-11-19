# System map (flowmap/) — deep flowchart to function/file level (2026-11-17)

User directive: complete the portal flowchart down to individual functions + files, keep it
small via the memory/modularity rules, link every file, and list files that link NOWHERE.
Deliverable = `flowmap/` (9 small pages, each with header pointer; open ROOT in browser):
http://127.0.0.1:8099/api/file/raw?path=flowmap/index.html

- -> ⚠missing:flowmap/INDEX.md          pointer dictionary for the set
- -> ⚠missing:flowmap/server-core.html  agent_portal.py: all 110 top-level defs + Handler methods, grouped by subsystem w/ line numbers; GET/POST route table
- -> ⚠missing:flowmap/frontend.html     index.html shell + ui/core.js (44 fns) + ui/uploads.js (46 fns), request flow UI->API
- -> ⚠missing:flowmap/llm-fleet.html    Studio :8888 layer, per-agent routing (agents.json), model-load governance, RAG, host table (.37/.39/.245)
- -> ⚠missing:flowmap/memory-system.html hot file + tree injection into prompts, aux memory, mirror sync, prune/commit chain
- -> ⚠missing:flowmap/ops-tasks.html    every schtask -> vbs/bat/py chain; 10 stale one-shot tasks flagged; restart trap
- -> ⚠missing:flowmap/split-plan.html   portal/ 12-module split (on disk, NOT wired) mapped to monolith functions; ui/ split done; TODO.md prune pending
- -> ⚠missing:flowmap/orphans.html      inbound-reference scan: 10 files linked only by stale tasks; 227 true orphans (1.1 MB); 157 auto-pruned journals (12.4 MB)

Key findings: PortalRun still runs the agent_portal.py MONOLITH (portal/ package unwired);
PortalFleetProbe runs fleet_probe.py (ops INDEX's "fleet_probe_v2" is stale, no v2 file exists);
portal_watchdog.py is dead (task runs portal_watchdog.vbs inline); watchdog.log lives in memory/ops/.

Pointers: modularity rule -> memory/portal/file-modularity.md | restart trap -> memory/ops/windows-runbook.md
