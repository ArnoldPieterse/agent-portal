<!-- state: {"inter_agent_replies": 4, "last_reset_by": "", "infinite_budget": true} -->
# Project Memory — Agent Portal (White)

HOT FILE ONLY (kept small on purpose). Newest first. Durable facts -> module under memory/ ; pointer map -> memory/INDEX.md.

## GOAL (live plan = TODO.md top; keep both in sync)
**QUEUE ⑤ LANDED + PORTAL ON FIXED CODE + FILES PANEL SERVED** (11-13 ~22:0x, White console r19): workspace root now = agent_portal.py 1b86880c (pull-exclusion + _same_file guards) + memory_mirror.py e5c4a229 (hash-first no-op / skew band / SKEW_SUSPECT); portal PID 23704 (created 22:01:54, trap-check PASS; stale 27268/1240 retired); served index.html re-pinned to TRUE canonical md5 9c6b08e3d98355e632a72cb871d5b60d (Files panel + ops polish) - the prior 8-round full pin was a mangled 31-char string, corrected. NEXT: Verifier closes AC-A2-1..4 process-level on PID 23704 (+ Designer design-leg checks); Scribe queue ④ rebuild from Red master 13c97dfb; then mirror uploads/ to remote sandboxes, move Red .245 to wired NIC.

## 2026-11-14 ~01:1x - White model folders → fleet convention (in flight)
fleet_reload.py WHITE section pointed at a never-executed rename; live pair = Q4_K_S (`unsloth\Qwen3.8-27B-GGUF`, ctx 131072) + Q8_0 (`lmstudio-community\Qwen3.8-27B-GGUF`, ctx 32768), both report under bare id → count check is the only reliable White guard. recover_all.py now dual-path safe (prefers new names, falls back to old). white_realias_rename.py launched detached 01:13, idle-gated: unload both → rename to `Qwen3.8-27B-Q4_K_S` / `Qwen3.8-27B-Q8_0` → re-point aliases (they bind folder paths) → reload with ctx preserved → alias probes; full rollback on failure. Verdict in white_realias_result.json (~10–20 min after idle). Note: live Q4 runs 131k ctx but boot recipe loads 65k — pre-existing mismatch, left as-is.

## 2026-11-13 ~18:1x - r29: TWO-WAY sync + per-mode UI persistence + Archivist PDF function
Fixed "agent work not landing" (root cause: two one-way pipes). (1) Portal sync is now TWO-WAY - TODO.md/MEMORY.md/memory leaves last-writer-wins both directions, code/config allowlist push-only (merge-queue rule), every other sandbox file new-only pull with junk exclusions (Mingit/, MinGit.zip, project clones, uploads/); `_auto_commit()` after each chat turn keeps repo drift <= 1 turn (Builder goal #5 delivered). First sync pulled `memory/goals.md` (Orchestrator's 8x10 record) from the sandbox into workspace + git. (2) memory_mirror.py pushes the full git-tracked allowlist (~43 files) AND pulls back remote memory/ trees (newer/new only) - Red/Pale/Black work lands in White. (3) index.html: refresh no longer clears messages - per-mode localStorage persistence (MutationObserver save, restore on load/mode-switch, Reset clears the slot, file-link hover re-wired for restored bubbles) + sticky auto-scroll (off while scrolled up, re-pins at bottom / on send). (4) Archivist gained the PDF-reporting function (recipe: memory/ops/pdf-reporting.md); Researcher directed to prefer live web_search - multiple targeted searches, cite URLs. Detail: memory/portal/architecture.md.

## 2026-11-13 ~17:0x - NEW OPS PROCESSES LIVE: TODO pruning + local git repo
Built into agent_portal.py, live-verified (PID 1240): (1) `POST /api/todo/prune` moves all-[x] sections of TODO.md → TODO_completed.md, auto-chunks >240 lines into todo_done_parts/TODO_done_part_NNN.md (first run: 7 sections / 28 items); (2) local git repo via portable MinGit (`mingit/`), curated allowlist .gitignore (~43 files), GET/POST /api/git (commit|init), baseline commit `8f5e7d5`. UI: 🔧 Ops panel (status, commits, commit box, ✂ Prune). ORCHESTRATOR TODO queued: announce both processes to all agents + ask each to set 10 goals themselves. Detail: memory/portal/architecture.md (Ops section).

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

## Hot Notes
- Scribe's r62 fix to synthesis/INDEX.md was lost; re-applying from r58 vehicle file toward canonical 0517db38 (5,5
- Builder re-pinned root index.html to v2.1 (70,748 B / c820e755) via hash-gated one-shot; Designer's verified merge of v2 fixes + 9 memory-cy
- Builder's re-pin of root to c820e755 NOT
- Verifier r67: root index.html still 68,549 B / 8fc29f19 (pre-v2); Builder's re-pin to c820e755 has NOT landed on Verifier's seat.
- Builder's re-pin to c820e755 unconfirmed
- Builder's prior [CONCLUDED] pin claim was false (context-limit kill); root re-pinned to c820e755 and verified first-party this round.
- Builder's re-pin of root→c820e755 contested in r67; Designer
- G2 probe-JSON files still absent on root (mirror lag) — Researcher's second-seat confirm lane remains blocked
- Root index.html re-pinned to c820e755/70,748B (v2.1); backup at
- Mechanic ops lane CLOSED: white rename+dual-path done, guards clean, runbook note appended (422 abort→v2 fix→async-ack polling lesson).
## Counter
- inter_agent_replies_this_prompt: 4 / ∞
- last_reset_by: —
