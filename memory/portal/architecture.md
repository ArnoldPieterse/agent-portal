# Portal architecture — how it runs (design notes, not bugs)
Last updated: 2026-11-13 ~18:1x (r29: TWO-WAY workspace sync + post-turn auto-commit + SMB mirror pull-back; NEW OPS processes: TODO pruning + local git repo; DM complete incl. human [DM]; SMB mirror live on all hosts).

## Ops processes: TODO pruning + local git repo (BUILT + LIVE-VERIFIED 2026-11-13 ~17:0x)
Two ops processes in agent_portal.py (code block "Ops (2026-11-13): TODO pruning + local git repo management"), both verified against the running portal.
**TODO pruning** — `POST /api/todo/prune` (also the ✂ button in the UI): splits TODO.md into preamble + `## ` sections; any section whose items are ALL `- [x]` (and at least one checked) moves to `TODO_completed.md`; sections with any open item stay put. Idempotent; returns {moved_sections, moved_items, completed_lines, chunks_split}. Auto-chunking: when TODO_completed.md outgrows DONE_MAX_LINES=240 lines, its oldest DONE_PART_SIZE=200 lines split off into `todo_done_parts/TODO_done_part_NNN.md` (numbered, chronological). First live run: 7 sections / 28 items → 58-line completed file.
**Local git repo** — Git was not installed on White → portable MinGit 2.45.2 in `mingit/cmd/git.exe` (GIT_EXE constant; no system install). Repo initialized at the workspace root (`-b main`, user "Agent Portal <portal@agent-portal.local>") with a curated ALLOWLIST `.gitignore` (~43 meaningful files: portal code, memory tree, TODO/MEMORY, ops scripts; ignores PNGs/logs/scratch dumps). Baseline commit `8f5e7d5` (5,287 insertions). Endpoints: `GET /api/git` → {repo, changed, log(last 12)}; `POST /api/git` with {"action":"commit","message":...} → add -A + commit (or "init" to re-init). UI: 🔧 Ops panel next to Fleet — git status, recent commits, commit box, ✂ Prune button.

### curl examples (BUILDER GOAL 9 — run verbatim 2026-11-16 against live PID 16164, curl 8.22.0 Windows)

A fresh agent can copy these three commands exactly as written; expected outputs captured below.

**1. Git status + recent commits** (read-only):
```
curl -s http://127.0.0.1:8099/api/git
```
Expected (200): JSON with `repo:true`, `changed:<n>`, full `status` text, and `log` = last 12 commits. Captured 2026-11-16 ~13:3x (clean tree after the goal-sweep commit):
```json
{"repo": true, "changed": 0, "status": "", "log": "5879833 auto: post-turn sync 2026-11-16 13:26:09\n610c6c6 feat(ui): D4 tokenized ..."}
```

**2. Commit the working tree** (no-op-safe on a clean tree — verified both paths):
```
curl -s -X POST http://127.0.0.1:8099/api/git -H "Content-Type: application/json" -d "{"action":"commit","message":"docs(ops): my change"}"
```
Expected (200): with changes → `{"ok": true, "committed": true, "out": "[main <hash>] ..."}`; clean tree → `{"ok": true, "committed": false, "note": "nothing to commit", ...}`. Captured 2026-11-16 (clean-tree path):
```json
{"ok": true, "committed": false, "note": "nothing to commit", "out": "On branch main\nYour branch is ahead of 'origin/main' by 7 commits.\n...\nnothing to commit, working tree clean"}
```

**3. Prune fully-completed TODO sections** (DESTRUCTIVE-by-design: moves all-[x] sections to TODO_completed.md with 240-line chunking; pre-gated by `_run_index_check` — returns 409 while any INDEX pointer dangles; auto-commits after):
```
curl -s -X POST http://127.0.0.1:8099/api/todo/prune -H "Content-Type: application/json" -d "{}"
```
Expected (200): `{"ok": true, "moved_sections": N, "items": M, "done_file_lines": L, "chunked": bool, "index_check": {"rc": 0|2, ...}}`. Live proof: 2026-11-15 run moved 4 all-[x] sections / 15 items, DONE file 110 lines (<240, no chunk due); NOT re-run on 2026-11-16 to avoid moving live TODO sections mid-turn.


## Private messaging / DM (BUILT + LIVE-VERIFIED 2026-11-13 ~12:4x)
Agent-to-agent private messages via `[DM @Name] ...` in a reply. Server-side per-viewer redaction (agent_portal.py): `parse_dm_segments()` splits text into public/dm segments - a marker opens a segment running to the next marker or end, so trailing text IS the DM body (multi-line OK); `render_dm_view(segs, viewer, sender)` gives each agent its view: public untouched, inbound DMs as `[Private message from X]: body`, foreign DMs as `🔒 [private message to Name]`. Redaction applies in group mode only and ONLY when every DM target in the message is a known roster name (unknown targets fail-open - hiding would lose content for everyone). Wired into `to_openai_messages` for agent messages after last_user; `_ack_nudge` cross-talk fires on inbound DM receipt ("respond briefly; visible only to the two of you") and name-scans the REDACTED view, so foreign DMs never false-nudge. Frontend (index.html): 🔒 private → Name chips (details/summary) + public text above. Human-typed `[DM @X]`: CLOSED 11-13 ~13:1x - the same per-viewer redaction now applies to human messages in group mode (unknown targets fail-open, no content loss), so a human DMing one agent is invisible to all others. Unit tests _dm_unit_test.py 18/20 (2 fails = wrong test expectations, not code bugs). LIVE-VERIFIED in the real UI 12:38-12:48: auto-continue bubble + 7 chips (6→Researcher, 1→Orchestrator) + ✓ Concluded (_dm_live_result.json).

## Workspace <-> sandbox sync (BUILT 2026-11-13, TWO-WAY since r29 ~18:1x)
Agent tools run in Studio's shared _default sandbox, not HERE (mount asymmetry). `_sync_workspace_to_sandbox()` is now TWO-WAY (r29): (1) **LWW set** - TODO.md / MEMORY.md + every memory/ leaf: last-writer-wins BOTH directions (mtime decides, 0.5 s tolerance) - agent edits made in the sandbox land in HERE (and therefore in git) instead of being clobbered; (2) **code/config** - the rest of the git-tracked allowlist (~43 files): PUSH-ONLY from HERE per the merge-queue rule (sandbox edits to code are experiments until merged via upgrade-plan.md); (3) **everything else** in the sandbox: NEW-ONLY pull - a file absent from HERE is copied home, an existing workspace file is NEVER overwritten; junk exclusions (Mingit/, MinGit.zip, project-clone trees AgentPortal_V1-git/_boot2/_bootstrap_test/gapfix-test, uploads/, __pycache__) + 20 MB size guard keep agent experiments out of the workspace. Called pre-stream AND post-turn on every POST /api/chat; `_auto_commit()` after each turn commits whatever the sync moved (repo drift <= 1 turn - Builder goal #5). mtime-guarded (copy2 preserves mtime -> steady state touches nothing); all errors swallowed - a sync hiccup must never break chat. History: originally one-way HERE->sandbox, so agent sandbox edits were overwritten next turn - that was the root cause of "work not landing", fixed in r29. Earlier trap: the sandbox held 5 reparse-point junctions (4 files + memory/) pointing at the STALE AgentPortal_V1 snapshot tree, so sync silently no-op'd; fix = remove the junctions (rmdir removes only the link), let sync materialize real files - verified (all 19 files byte/mtime-match HERE). Remote hosts: covered by the SMB mirror below.

## SMB push mirror to remote sandboxes (LIVE 2026-11-13 ~13:2x)
Pushes the git-tracked allowlist (~43 files via `git ls-files`, hardcoded fallback) + the full memory/ tree from HERE into each remote host's `_default` sandbox over `\\host\C$` (memory_mirror.py; same 0.5 s MTOL + copy2 as the per-turn White sync), and since r29 PULLS BACK each host's memory/ tree (newer/new files only, never overwrites a newer local copy) so Red/Pale/Black agent work lands in White. Hosts in memory_mirror_hosts.json: Red Red, Pale Pale, Black Black - **SMB passwords are EMPTY on all three** (Arnold 11-13: the `[REDACTED-CREDENTIAL]` string in smb_fix.ps1 is Unsloth Desktop remote access only, NOT an SMB password; it was rejected by Pale/Black with Win error 86 until empty-password `net use` was tried). Per-host `net use` with stale-connection cleanup (scheduled task may run in a different session); hosts independent - one dead host never blocks the others; every run appends one JSON audit line to memory_mirror.log. Scheduled task `\MemoryMirrorRun` runs it every 5 min as a fresh current-user task (no admin needed). Initial pushes verified on-disk: Red 19 files @13:08, Pale + Black 19 each @13:25, mtimes match HERE; steady-state runs push nothing. Non-memory files stay push-only by design: never deletes remote files; only memory/ trees flow back (r29), so per-agent note dirs the remote agents create elsewhere in their own sandboxes coexist untouched.

## Live plan injection into group prompts (LIVE 2026-11-13 ~13:1x)
`_live_plan_block()` appends to every GROUP prompt (via `_shared_memory_block()`): the top section of TODO.md (1200-char cap - newest-first, so it is always the live plan) + the GOAL line of MEMORY.md (600-char cap). Agents thus see the current plan without file access; failure-safe (any read error -> empty block, chat never breaks). Functionally tested against the real files (1911 chars total); live in the restarted portal (PID 24808).

## File & folder uploads (BUILT 2026-11-12 ~20:3x)
Humans attach files/folders to messages; agents see them in the shared agent folder.
- Storage: `uploads/` inside SANDBOX_DIR (C:\Users\<white>\.unsloth\studio\sandbox\_default) - same root agent tool calls write to and /api/file + /api/file/raw serve, so uploaded paths linkify exactly like agent-built files.
- Server (agent_portal.py): `POST /api/upload` = raw binary body + `X-Rel-Path` header (URL-encoded target under uploads/); streamed to disk in 1 MiB chunks (never fully buffered), 4 GB cap per file, returns the portal-relative path. Path guard `_safe_upload_path()`: rejects NUL, drive-letter absolutes (`C:/...`), POSIX absolutes (`/...`), `..` traversal, bare `uploads`. `GET /api/uploads` lists the tree (path/size/mtime, 2000 cap).
- Frontend (index.html): + button in composer -> popover ("Upload files…" multi-select / "Upload folder…"); drag & drop onto composer (folders walked recursively via DataTransferItem.webkitGetAsEntry); per-file chips with name/size/progress%/check/fail/abort; Send disabled while uploads in flight. On send, an `[Attached in shared folder: uploads/a.txt (1.2 KB), …]` line (first 15 + count) is appended to the message content so every addressed agent gets the paths in context.
- Caveat (mount asymmetry): uploads live on WHITE only. Remote agents' tools run in their own host sandboxes - they see the attachment list but cannot open the files locally; a remote agent needing contents must ask a local agent to read + relay. Follow-up candidate: mirror uploads into remote sandboxes.
- Deploy: portal restarted per RESTART TRAP (kill PID from _portal_pid.txt -> schtasks /run PortalRun -> verify new PID CreationDate > agent_portal.py mtime -> rewrite _portal_pid.txt); HARD-REFRESH the UI tab after index.html edits. Test junk cleaned from uploads/ after verification.
- Bugs caught in testing (all fixed + re-verified): double `uploads/uploads` prefix (parts[0] is the prefix itself - strip before joining UPLOAD_DIR); absolute paths silently relativized instead of rejected; bare-`uploads` check ran AFTER the prefix prepend so it never fired.

## Multi-host routing + networked-agent UI (BUILT 2026-11-11)
Per-agent remote Studio support, end to end (R2/R3 engine):
- agents.json: optional per-agent `studio` (base URL, e.g. http://Black:8888) + `api_key` (Bearer). Empty/missing = local 127.0.0.1:8888 keyless - fully backward compatible (White agents have no fields at all; defaults apply).
- agent_portal.py: `studio_base(agent)` / `studio_headers(agent)` helpers route BOTH /v1/chat/completions and RAG prefetch to the agent's own host with per-agent auth. New `POST /api/scan-models {base_url, api_key}` proxies GET `{base}/v1/models` (lenient about missing http://; 502 + error json on unreachable/bad key; 400 empty base) - unit-tested vs a fake remote Studio, 5/5 cases.
- index.html: New-agent modal has a "Networked host" checkbox -> reveals Studio base URL + API key fields + **Scan models** button (fills the Model dropdown from that host's live /v1/models). Untick restores the local model list; opening an existing networked agent auto-rescans its host; Save persists both fields. The model picker for EXISTING agents stays local-only on purpose.
- Deploy: kill portal PID first, then `schtasks /run /tn PortalRun` (Running-task no-op trap); HARD-REFRESH the UI tab after index.html edits.
- LIVE PROOF (2026-11-11 ~14:5x): agent 'black' in roster routes via studio_base() to http://Black:8888 with Bearer - first real networked agent; portal->host chat path works up to model load (host-side blocker, not portal). Load trap on v0.1.916-beta: NO auto-switch; must POST /api/inference/load {"model_path": <id>} before chat.
## Parallel async processing (BUILT 2026-11-10)
Symptom: group agents took turns thinking — one streamed while the others waited. Cause was
frontend-only; the backend was already parallel-ready.
- Frontend (index.html): prompt phase and EACH cross-talk round now fire all agents via
  `Promise.all(cast/active.map(a=>streamReply(...)))`. Rounds stay sequential (each round must see
  the previous round's replies); within a round everyone thinks at once on their own instance.
- Deterministic ordering: results are pushed to history in cast/active order (index-aligned), not
  completion order — concurrent finishes can't scramble message order.
- Busy hint is now a Set (`busyNames`): modeBar shows "⏳ <names> working…" (dynamic roster names,
  e.g. ex-Atlas/Quinn, now Orchestrator/Researcher) while streams
  overlap; each streamReply wraps its core in try/finally so one finishing never clears others.
- `lastConcluded` stays a global but is reset in streamReplyCore's SYNC prefix (before the first
  await) — under Promise.all every reset happens-before any set, so no race.
- Backend (agent_portal.py): ThreadingHTTPServer already gave one thread per SSE stream; dual
  residency means Orchestrator->Q8/GPU1 (ex-Atlas) and Researcher->Q4/GPU0 (ex-Quinn) run on SEPARATE
  llama-servers = true parallelism,
  not slot queuing. Real fix: counter read-modify-write was racy (two simultaneous replies could
  both read N, write N+1). Now `_lock` is an RLock with atomic `_bump_counter()`/`_reset_counter()`
  helpers used by stream_chat auto-reset and _finish_chat.
- Verification: e2e_parallel.py via schtask \PortalE2EPar (detached — in-turn probes deadlock on
  this chat's Q4 slot) fires BOTH agents concurrently, records per-stream first-token/done
  timestamps + meta counter values -> ⚠missing:e2e_parallel_result.json (expect overlap>0s and counter +2).
- After index.html edits: user must HARD-REFRESH the portal tab (old JS cached).

## Parallel verification - e2e results + Studio serialization finding (2026-11-10 22:18)
- e2e_parallel_result.json verdict SERIALIZED_NO_OVERLAP: phase1 overlap -0.91s, phase2 -2.40s
  (both agents' t_send within 0.5ms; Quinn's stream always finished BEFORE Atlas's first token).
  Counter atomicity PROVEN: meta frames saw distinct values {1,2} = exactly +2 across the two
  non-silent cross-talk replies; /api/memory/file?path=INDEX.md -> 200 clean.
- Diagnosis chain: portal is ThreadingHTTPServer (one thread per SSE stream) and stream_chat holds
  no lock -> portal NOT the bottleneck. llama.cpp side can't serialize either: Atlas->Q8/GPU1 and
  Quinn->Q4/GPU0 are SEPARATE llama-server processes on separate GPUs. Remaining suspect: Studio's
  /v1/chat/completions inference layer; GET /api/inference/active-generations reports
  parallel_slots=1 ("effective decode capacity") -> likely a global one-generation-at-a-time cap.
- probe_parallel.py (schtask \PortalProbePar, detached, self-waits for idle): fires quinn-q4 +
  atlas-q8 RAW at :8888 simultaneously with a mid-flight sampler of active-generations (count,
  parallel_slots, which models active). overlap>0 => cross-model concurrency exists and e2e's
  serialization had another cause (re-run e2e); overlap<=0 => Studio serializes globally -> true
  parallel group processing needs a Studio-side change (report to Arnold; busy indicators already
  mask the wait in the UI). Result -> ⚠missing:probe_parallel_result.json.
- PROBE RESULT (2026-11-10 ~22:40, read this turn): verdict SERIALIZED_NO_OVERLAP at RAW :8888
  level — both 'pong' replies completed in ~80ms each, overlap -0.12s, parallel_slots_seen=[1],
  peak_active_count=0 (sampler never caught two active). CONFIRMED: Studio's inference layer
  serializes generations globally across models; portal + llama.cpp exonerated. True parallel group
  decode needs a Studio-side change (reported to Arnold); busy indicators already mask the wait.
- Script bug fixed: e2e get_counter() regexed the raw /api/memory JSON envelope (escaped quotes ->
  "Expecting property name" error); now parses the {"text": ...} envelope first.
- Model-behavior note (not infra): Quinn's phase-2 cross-talk reply rambled mid-stream about
  [SILENT]/[CONCLUDED] and self-corrected to the one word; meta.silent=false so it counted as a
  real reply. Persona prompt could be tightened if this recurs.
- REAL-WORLD INSTANCE (2026-11-11, 6-agent group e2e): in cross-talk round 2 all six fired in
  parallel; Quinn's local Q4 request queued behind Atlas (88.9s) + the remote calls and hit the
  client 600s timeout -> SILENT -> settled=['Quinn']. Run still GREEN (concluded=true, active-
  generations clean afterwards). Expected behavior of the known global serialization under a
  6-way parallel round, not a regression. If full-roster rounds get routinely starved: raise the
  client timeout per host-distance, or fire local agents slightly staggered in group_e2e.py.


## Mount asymmetry across hosts (CONFIRMED in e2e 2026-11-12)
Each agent's LOCAL_TOOLS run in ITS OWN host's Studio sandbox (_default): from Red and Pale that
folder holds only .unsloth_sandbox (+ unsloth-tmp) - no memory/, TODO.md, or portal files; parent
listing fails (WinError 5). Remote agents therefore read project state via the portal (/api/memory,
/api/memory/file) + the INDEX block injected into every group prompt. Consequence for file-link
features: per-host path resolution stays on White's resolver (see llm/hosts.md durable rules).

## User message queue + refresh-safe state (BUILT 2026-11-15)
Problems fixed: (1) refreshing the portal wiped the conversation and lost in-flight runs; (2) send() early-returned while busy, so the user could not message a working group.
- user_messages.json: {messages:[{id,ts,text,mentions[],checked{agent:bool}}]} - UMQ_MAX cap, atomic os.replace writes under _umq_lock. Global index pointer added in memory/INDEX.md (all agents check via portal auto-injection or the CLI).
- Endpoints: POST /api/user-messages {text,mentions} -> entry; GET /api/user-messages -> last 50 + derived processed (every in-scope agent checked); POST /api/user-messages/check {id,agent|'*'} flips booleans. Scope: empty mentions = broadcast to all agents; @Name entries are private to that agent.
- stream_chat: per-agent prompt build calls umq_pending_for(who) and injects a USER MESSAGE QUEUE block (PRIVATE vs broadcast tag + rule: act on them, keep private ones private); once the request reaches Studio, umq_check(ids, who) marks THAT agent seen. Solo mode unaffected.
- Frontend: send() while busy now queues via POST and renders #queuePanel rows with spinner "n/N seen" (umqPoll every 1.5s); when idle, umqDeliver auto-sends pending entries in ts order - settleMsg marks all checked first so the triggered run never double-injects them. @Name regex reused for private scope.
- Refresh fix root cause: the 2026-11-13 localStorage restore (restoreMsgs) was only wired to mode-button clicks, never to page load - so refreshes looked like a reset even though saves happened. bootRestore() is now chained onto the initial refresh(): setMode(mode) restores the LS slot; restoreFromServer() falls back to GET /api/history?mode= when LS is empty (re-seeds LS); saveHistoryServer() POSTs history at run end.
- Run heartbeat: startHeartbeat/stopHeartbeat POST /api/run-state {busy,mode,ts} every 5s while busy; on load checkInterruptedRun() shows #intBanner if a run was in progress <15s ago, with "send continue prompt" (queues a continue instruction) or dismiss.
- CLI: user_messages.py list / pending <Agent> / check <id> <Agent|*> - API-based, for audit and for agents working outside the portal.
- Verified e2e (umq_test.py): add -> processed=false; check '*' -> n=8 (full roster); processed=true. Portal restart REQUIRED after backend edits (PortalRun trap: taskkill the real :8099 PID - _portal_pid.txt can be stale - then schtasks /run /tn PortalRun, confirm new owner via Get-NetTCPConnection).

## Group run engine (2026-11-15) — runs are BACKEND-owned; refresh-proof
Hard refresh used to cancel group runs because the whole pass/cross-talk/nudge loop lived in the tab's JS. Now:
- `start_group_run(text)` spawns a daemon thread: SEQUENTIAL prompt pass (one `stream_chat` per agent into a `_FrameSink`, agents dispatched one after another - see 2026-11-15 evening note) -> cross-talk rounds (only agents with new content) -> nudge loop (max 3, no [CONCLUDED] yet). Verdict is journaled at the end.
- Every SSE frame is journaled seq'd to `runs/<id>.jsonl` (`_journal_event`). `/api/run-events?run=<id>&cursor=N` replays from any cursor; live frames tail the journal. GET `/api/run-state` merges the live run (run_id + status) over the heartbeat state.
- Frontend: `send()` POSTs `/api/group-run` then `attachRun(run_id)` streams `/api/run-events`; on boot, `checkInterruptedRun()` finds a running run via GET /api/run-state and re-attaches from cursor 0 (replaying history). Stop button -> POST `/api/run-stop` (clean verdict, no "interrupted" lie).
- Group history is backend-owned: the engine appends each turn to `chat_history_group.json`; client POSTs of group history are ignored (200 {ignored}).
- `_clear_stale_busy()` at portal start clears a stale busy:true in run_state.json when no group run is live.
- Goal injection: `_agent_goals_block(name)` appends the agent's open goals from `memory/goals/<name>.md` to every group turn (prompt + cross-talk + nudge) — the goal-drift fix; solo turns unchanged.
- Restart trap still applies: taskkill real :8099 PID, schtasks /run /tn PortalRun.

## 2026-11-15 evening - "all agents stuck / send greyed" incident fixes
Symptom the user saw: all 8 bubbles on "thinking", 0 goal progress, Send disabled. Root causes + fixes:
- SEQUENTIAL DISPATCH (`_parallel_turns`): Studio serializes generations GLOBALLY (parallel_slots=1 across models), so firing all agents at once only piled N requests into one queue - everyone looked stuck for minutes and a single hung request wedged the whole pass. Now turns run one agent after another: same wall time, each agent visibly completes before the next starts.
- SEND NEVER DISABLED: the button was `disabled` while busy = dead end. It now stays enabled and relabels to "Queue"; send() already routes busy-mode messages into user_messages.json (UMQ) which every agent picks up on its next prompt build. Frontend helpers: setSendQueued/startStallPoll/stopStallPoll.
- STALL WATCHDOG: `_run_event` now stamps each journal line with `ts`; `/api/run-state` reports `last_frame_ts` + `stalled` (no frame for 240 s while busy). Frontend polls it every 15 s while busy and shows a wedge warning banner (Stop / RecoverAll hint).
- Journal cap raised 4000 -> 30000 (`RUN_MAX_EVENTS`) - 4000 silently dropped frames mid-run.
- The actual stall that day was a Q4 WEDGE (see memory/llm/instances.md): run-stop cannot drain a hung request because the stop event is only checked when frames arrive; kill portal + wedge_force_recover.py was the fix.

## 2026-11-15 - Parallel group dispatch + no-human-gates (supersedes any sequential-dispatch note)
Arnold directive: agents run in parallel async, not turn-taking. `_parallel_turns` now submits one worker thread per agent (ThreadPoolExecutor, context exit waits for all). Cross-host agents (Builder/Verifier .99, Designer/Archivist .39, Scribe/Mechanic .245) truly overlap; the two White-local agents are queued by Studio internally (parallel_slots=1) and start a beat apart - harmless. Concurrency safety: journal writes take _journal_lock per event, memory RMWs take _lock, UMQ takes _umq_lock; no lock is held across a generation.
Same day: NO HUMAN GATES - system prompt forbids agents from creating human decision gates; all existing gates removed from MEMORY.md/TODO.md (see TODO.md top section).
