<!-- state: {"inter_agent_replies": 16, "last_reset_by": "", "infinite_budget": true} -->
# Project Memory — Agent Portal (White)

HOT FILE ONLY (kept small on purpose). Newest first. Durable facts -> module under memory/ ; pointer map -> memory/INDEX.md.

## GOAL (live plan = TODO.md top; keep both in sync)
**FLEET PANEL BUILT + DM COMPLETE + FILE-ACCESS DONE** (11-13 ~14:0x): /api/fleet live per-host view (models+quant, busy/idle/unknown, 5s refresh) via on-demand Studio probes - first reveal: remotes UNLOADED overnight; [DM @Name] private messaging live-verified; workspace→sandbox sync + SMB mirror live all 3 hosts (empty SMB passwords). Portal PID 21988 (one-shot schtask relaunch; wmic gone, start reaped by wrapper). NEXT: optional - mirror uploads/ to remote sandboxes; move Red .245 to wired NIC.

## 2026-11-13 ~13:2x - File-access plan COMPLETE (all 4 steps) + last DM gap closed
Step 2 unblocked by Arnold's clarification: **SMB passwords are EMPTY on all hosts** - the `131991Apiet` string in smb_fix.ps1 is Unsloth Desktop remote access only, NOT an SMB password (hence Win error 86 on Pale/Black). Dropped empty passwords into memory_mirror_hosts.json (pending_creds -> ok); next mirror run pushed all 19 files to Pale (192.168.1.39) + Black (192.168.1.99), 0 errors; verified on-disk mtimes match HERE; steady-state runs no-op. \MemoryMirrorRun (5 min, current-user task) already live - picked it up automatically. Human-typed [DM @X] redaction gap also closed in to_openai_messages (same per-viewer logic, fail-open). Remote sandboxes hold extra per-agent note dirs (memory/archivist/ etc.) the agents created themselves - mirror is push-only by design, never deletes remote files. Detail: TODO.md top + portal/architecture.md.

## 2026-11-13 ~12:5x - Private messaging (DM) LIVE-VERIFIED + file-access steps 1+3
[DM @Name] = text only that agent sees: server-side per-viewer redaction in to_openai_messages (parse_dm_segments/render_dm_view; recipient sees body, others a 🔒 chip; unknown targets fail-open); _ack_nudge fires on receipt and name-scans the REDACTED view (no false nudge for foreign DMs). Unit 18/20 (2 fails = wrong test expectations). LIVE 12:38-12:48 real UI: auto-continue + 7 chips + ✓ Concluded. Gap: human-typed [DM] unredacted to all agents (queued). File access: _sync_workspace_to_sandbox() mirrors TODO/MEMORY/agents.json/agent_portal.py+memory/ into the White sandbox per /api/chat (canonical = HERE); INDEX.md FILE ACCESS block rewritten (1545 chars). Sandbox had 5 junctions at STALE AgentPortal_V1 tree -> removed + real files synced. Detail: TODO.md top + portal/architecture.md.

## 2026-11-12 ~21:4x - Auto-nudge on round end (stuck-run fix)
Group runs stalled on the MAX_CALLS=12 hard cap, not a timeout. index.html pass loop now auto-continues un-concluded passes up to 3 nudges (`↻ AUTO-CONTINUE n/3` bubble, fresh budget each pass, all-silent = natural end); verdict leads "⚠ Auto-continue limit reached" when spent; MAX_CALLS 16. LIVE-VERIFIED 11-13 12:39 (see line above).

## 2026-11-12 ~20:4x - File & folder uploads LIVE
uploads/ inside SANDBOX_DIR so /api/file + linkify work identically; POST /api/upload streamed in 1 MiB chunks, 4 GB cap, guarded (_safe_upload_path); UI chips + drag & drop + [Attached in shared folder:] line. Caveat: WHITE-only - remote agents can't open them locally (mirroring = file-access step 2). Detail: portal/architecture.md.

## Durable rules (detail in the tree)
Engine update kills instances -> \RecoverAll (llm/instances.md); Studio serializes globally, parallel_slots=1 (portal/architecture.md); Stop + [CONCLUDED] + budget (portal/bugs/xtalk-completion.md); smoke agents SERIALLY - parallel aborts wedge the local Studio (llm/instances.md Wedge incident); restart trap: taskkill PID before schtasks /run (ops/windows-runbook.md); multi-GB LAN copies: full-hash verify on the destination disk, never size+magic (ops/probes.md).

## Counter
- inter_agent_replies_this_prompt: 16 / ∞
- last_reset_by: —
