# Portal architecture — how it runs (design notes, not bugs)
Last updated: 2026-11-13 ~17:0x (NEW OPS processes: TODO pruning + local git repo; DM complete incl. human [DM]; workspace sync; SMB mirror live on all hosts).

## Ops processes: TODO pruning + local git repo (BUILT + LIVE-VERIFIED 2026-11-13 ~17:0x)
Two ops processes in agent_portal.py (code block "Ops (2026-11-13): TODO pruning + local git repo management"), both verified against the running portal.
**TODO pruning** — `POST /api/todo/prune` (also the ✂ button in the UI): splits TODO.md into preamble + `## ` sections; any section whose items are ALL `- [x]` (and at least one checked) moves to `TODO_completed.md`; sections with any open item stay put. Idempotent; returns {moved_sections, moved_items, completed_lines, chunks_split}. Auto-chunking: when TODO_completed.md outgrows DONE_MAX_LINES=240 lines, its oldest DONE_PART_SIZE=200 lines split off into `todo_done_parts/TODO_done_part_NNN.md` (numbered, chronological). First live run: 7 sections / 28 items → 58-line completed file.
**Local git repo** — Git was not installed on White → portable MinGit 2.45.2 in `mingit/cmd/git.exe` (GIT_EXE constant; no system install). Repo initialized at the workspace root (`-b main`, user "Agent Portal <portal@agent-portal.local>") with a curated ALLOWLIST `.gitignore` (~43 meaningful files: portal code, memory tree, TODO/MEMORY, ops scripts; ignores PNGs/logs/scratch dumps). Baseline commit `8f5e7d5` (5,287 insertions). Endpoints: `GET /api/git` → {repo, changed, log(last 12)}; `POST /api/git` with {"action":"commit","message":...} → add -A + commit (or "init" to re-init). UI: 🔧 Ops panel next to Fleet — git status, recent commits, commit box, ✂ Prune button.

## Private messaging / DM (BUILT + LIVE-VERIFIED 2026-11-13 ~12:4x)
Agent-to-agent private messages via `[DM @Name] ...` in a reply. Server-side per-viewer redaction (agent_portal.py): `parse_dm_segments()` splits text into public/dm segments - a marker opens a segment running to the next marker or end, so trailing text IS the DM body (multi-line OK); `render_dm_view(segs, viewer, sender)` gives each agent its view: public untouched, inbound DMs as `[Private message from X]: body`, foreign DMs as `🔒 [private message to Name]`. Redaction applies in group mode only and ONLY when every DM target in the message is a known roster name (unknown targets fail-open - hiding would lose content for everyone). Wired into `to_openai_messages` for agent messages after last_user; `_ack_nudge` cross-talk fires on inbound DM receipt ("respond briefly; visible only to the two of you") and name-scans the REDACTED view, so foreign DMs never false-nudge. Frontend (index.html): 🔒 private → Name chips (details/summary) + public text above. Human-typed `[DM @X]`: CLOSED 11-13 ~13:1x - the same per-viewer redaction now applies to human messages in group mode (unknown targets fail-open, no content loss), so a human DMing one agent is invisible to all others. Unit tests _dm_unit_test.py 18/20 (2 fails = wrong test expectations, not code bugs). LIVE-VERIFIED in the real UI 12:38-12:48: auto-continue bubble + 7 chips (6→Researcher, 1→Orchestrator) + ✓ Concluded (_dm_live_result.json).

## Workspace -> sandbox sync (BUILT 2026-11-13)
Agent tools run in Studio's shared _default sandbox, not HERE - agents could not read project state with their own python/terminal tools (mount asymmetry: remote sandboxes held only .unsloth_sandbox). `_sync_workspace_to_sandbox()` mirrors TODO.md / MEMORY.md / agents.json / agent_portal.py + the memory/ tree from HERE into SANDBOX_DIR, mtime-guarded (0.5 s tolerance; copy2 preserves mtime so unchanged files are never touched), called on every POST /api/chat; all errors swallowed - a sync hiccup must never break chat. Canonical copies stay in HERE (portal endpoints read/write HERE); an agent edit made directly in the sandbox is overwritten next turn. Trap hit: the sandbox held 5 reparse-point junctions (4 files + memory/) pointing at the STALE AgentPortal_V1 snapshot tree, so sync silently no-op'd (stat/copy through dead junctions raised OSError -> swallowed). Fix: remove the junctions (rmdir removes only the link), let sync materialize real files - done + verified (all 19 files byte/mtime-match HERE; zero reparse points left). Remote hosts: covered by the SMB push mirror below (step 2, LIVE 11-13 ~13:25).

## SMB push mirror to remote sandboxes (LIVE 2026-11-13 ~13:2x)
One-way mtime-guarded push of TODO.md / MEMORY.md / agents.json / agent_portal.py + the memory/ tree from HERE into each remote host's `_default` sandbox over `\\host\C$` (memory_mirror.py; same 0.5 s MTOL + copy2 as the per-turn White sync). Hosts in memory_mirror_hosts.json: Red IP_RED, Pale IP_PALE, Black IP_BLACK - **SMB passwords are EMPTY on all three** (Arnold 11-13: the `[REDACTED-CREDENTIAL]` string in smb_fix.ps1 is Unsloth Desktop remote access only, NOT an SMB password; it was rejected by Pale/Black with Win error 86 until empty-password `net use` was tried). Per-host `net use` with stale-connection cleanup (scheduled task may run in a different session); hosts independent - one dead host never blocks the others; every run appends one JSON audit line to memory_mirror.log. Scheduled task `\MemoryMirrorRun` runs it every 5 min as a fresh current-user task (no admin needed). Initial pushes verified on-disk: Red 19 files @13:08, Pale + Black 19 each @13:25, mtimes match HERE; steady-state runs push nothing. Push-only by design: never deletes remote files - per-agent note dirs the remote agents create in their own sandboxes (memory/archivist/, memory/designer/, ...) coexist untouched.

## Live plan injection into group prompts (LIVE 2026-11-13 ~13:1x)
`_live_plan_block()` appends to every GROUP prompt (via `_shared_memory_block()`): the top section of TODO.md (1200-char cap - newest-first, so it is always the live plan) + the GOAL line of MEMORY.md (600-char cap). Agents thus see the current plan without file access; failure-safe (any read error -> empty block, chat never breaks). Functionally tested against the real files (1911 chars total); live in the restarted portal (PID 24808).

## File & folder uploads (BUILT 2026-11-12 ~20:3x)
Humans attach files/folders to messages; agents see them in the shared agent folder.
- Storage: `uploads/` inside SANDBOX_DIR (C:\Users\White\.unsloth\studio\sandbox\_default) - same root agent tool calls write to and /api/file + /api/file/raw serve, so uploaded paths linkify exactly like agent-built files.
- Server (agent_portal.py): `POST /api/upload` = raw binary body + `X-Rel-Path` header (URL-encoded target under uploads/); streamed to disk in 1 MiB chunks (never fully buffered), 4 GB cap per file, returns the portal-relative path. Path guard `_safe_upload_path()`: rejects NUL, drive-letter absolutes (`C:/...`), POSIX absolutes (`/...`), `..` traversal, bare `uploads`. `GET /api/uploads` lists the tree (path/size/mtime, 2000 cap).
- Frontend (index.html): + button in composer -> popover ("Upload files…" multi-select / "Upload folder…"); drag & drop onto composer (folders walked recursively via DataTransferItem.webkitGetAsEntry); per-file chips with name/size/progress%/check/fail/abort; Send disabled while uploads in flight. On send, an `[Attached in shared folder: uploads/a.txt (1.2 KB), …]` line (first 15 + count) is appended to the message content so every addressed agent gets the paths in context.
- Caveat (mount asymmetry): uploads live on WHITE only. Remote agents' tools run in their own host sandboxes - they see the attachment list but cannot open the files locally; a remote agent needing contents must ask a local agent to read + relay. Follow-up candidate: mirror uploads into remote sandboxes.
- Deploy: portal restarted per RESTART TRAP (kill PID from _portal_pid.txt -> schtasks /run PortalRun -> verify new PID CreationDate > agent_portal.py mtime -> rewrite _portal_pid.txt); HARD-REFRESH the UI tab after index.html edits. Test junk cleaned from uploads/ after verification.
- Bugs caught in testing (all fixed + re-verified): double `uploads/uploads` prefix (parts[0] is the prefix itself - strip before joining UPLOAD_DIR); absolute paths silently relativized instead of rejected; bare-`uploads` check ran AFTER the prefix prepend so it never fired.

## Multi-host routing + networked-agent UI (BUILT 2026-11-11)
Per-agent remote Studio support, end to end (R2/R3 engine):
- agents.json: optional per-agent `studio` (base URL, e.g. http://IP_BLACK:8888) + `api_key` (Bearer). Empty/missing = local 127.0.0.1:8888 keyless - fully backward compatible (White agents have no fields at all; defaults apply).
- agent_portal.py: `studio_base(agent)` / `studio_headers(agent)` helpers route BOTH /v1/chat/completions and RAG prefetch to the agent's own host with per-agent auth. New `POST /api/scan-models {base_url, api_key}` proxies GET `{base}/v1/models` (lenient about missing http://; 502 + error json on unreachable/bad key; 400 empty base) - unit-tested vs a fake remote Studio, 5/5 cases.
- index.html: New-agent modal has a "Networked host" checkbox -> reveals Studio base URL + API key fields + **Scan models** button (fills the Model dropdown from that host's live /v1/models). Untick restores the local model list; opening an existing networked agent auto-rescans its host; Save persists both fields. The model picker for EXISTING agents stays local-only on purpose.
- Deploy: kill portal PID first, then `schtasks /run /tn PortalRun` (Running-task no-op trap); HARD-REFRESH the UI tab after index.html edits.
- LIVE PROOF (2026-11-11 ~14:5x): agent 'black' in roster routes via studio_base() to http://IP_BLACK:8888 with Bearer - first real networked agent; portal->host chat path works up to model load (host-side blocker, not portal). Load trap on v0.1.916-beta: NO auto-switch; must POST /api/inference/load {"model_path": <id>} before chat.
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
  timestamps + meta counter values -> e2e_parallel_result.json (expect overlap>0s and counter +2).
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
  mask the wait in the UI). Result -> probe_parallel_result.json.
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
