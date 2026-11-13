# Portal V1 Upgrade Effort — Intake Log
Recorded by Scribe · 2026-11-12 · Human kickoff: "This is your portal, work together and apply upgrades"

## Baseline snapshot (uploads/AgentPortal_V1/)
Core: agents.json (8.5 KB) · agent_portal.py (54.1 KB) · DESIGN.md (6.1 KB) · docs_chat.md (15.0 KB) · index.html (50.6 KB)
memory/: INDEX.md (1.6 KB) · llm/{INDEX 1016 B, hosts 14.7 KB, instances 3.3 KB, studio-api 1.9 KB} · ops/{INDEX 604 B, probes 2.2 KB, windows-runbook 5.9 KB} · portal/{architecture 9.2 KB, bugs/file-links-sandbox 7.0 KB} … + 26 more files not itemized in the attachment list

## Decisions
(none yet)

## Open
1. Scope: which upgrades to apply and in what order — no spec given yet.
2. uploads/AgentPortal_V1/ vs live portal root: is the upload a snapshot to merge, or the new source of truth? (uploaded agent_portal.py = 54.1 KB)
3. Attachment list truncated ("…and 26 more files") — full inventory pending.

## Ownership / next actions
- Orchestrator: add upgrade work plan to TODO.md (owns it).
- Scribe: log each decision here as it lands; update memory/portal/INDEX.md pointer once this file's contents are confirmed.
