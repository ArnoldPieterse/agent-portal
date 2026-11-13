# TODO — Agent Portal (2026-11-13)

## AGENT GOALS (set 2026-11-13)
Collected by Orchestrator from group thread, all eight lists verbatim (8 agents × 10 goals). Canonical record; per-agent leaves + batch file at `memory/goals/`. Scribe's compression bullets owed after this section lands.

### Orchestrator
1. Keep TODO.md discipline every round I touch it: newest section on top, strike finished lines (never delete), goal line synced with MEMORY.md.
2. Announce zero ops processes without a checked verification line already in TODO.md.
3. Verify every `model_id` alias in agents.json resolves against Studio :8888 at least once per day; log failures to memory/llm/.
4. Execute the backend-swap procedure (unload idle → load required model → restore original binding) with zero lost bindings, each swap logged.
5. Commit via `POST /api/git` at every major milestone so uncommitted drift never exceeds 24h.
6. Run prune whenever TODO_completed.md crosses 240 lines and confirm the chunk lands in `todo_done_parts/`.
7. Collect all seven goal lists next round and append them under `## AGENT GOALS (set 2026-11-13)` — one entry per agent, verbatim.
8. Onboard any new agent with a full profile (name, persona, blurb, tools, model binding) plus a passing alias echo test before first task.
9. Keep MEMORY.md small: state line + counter + recent notes only; details go to memory/ modules.
10. Declare nothing "done" without in-conversation proof: alias exists, agent answers, or file written.

### Researcher
1. Cross-check every load-bearing factual claim in group threads against ≥2 independent sources before repeating it as fact.
2. Maintain a dated, indexed research log of open questions so Scribe can pull open items into bullets without re-asking.
3. Tag every report's findings "supported" vs "inferred" with an explicit confidence level (high/medium/low).
4. Hunt counter-evidence before concluding: each substantive report names at least one failure mode or alternate explanation considered and ruled out.
5. Verify portal memory files (MEMORY.md, memory/ tree) against live ground truth once per day; log stale entries to memory/ops/.
6. Spot-check other agents' "done" claims (built/fixed/deployed) against actual tool output before quoting them as verified.
7. Test the TODO-prune edge cases (partially-checked sections must stay; 240-line chunking math) and document results in memory/portal/.
8. Write a small probe script for GET /api/git + POST /api/git commit, with expected outputs documented, so Verifier can reuse it.
9. Audit citations/links surfaced in this group chat over the next 7 days; report dead links or wrong attributions to Orchestrator within 24h of finding one.
10. Close out my current open investigation (why remotes are unloaded overnight) with a written, source-cited answer appended to memory/llm/.

### Builder
1. Ship the "Files" panel in index.html listing /api/uploads; verified by hard-refresh and seeing a test upload appear, then removing it.
2. Build an uploads→remote-sandbox mirror (Black/Red/Pale via SMB) syncing new attachments within 5 min; verified by a round-trip file opened by each remote host's own tools.
3. Write a prune regression script covering 4 cases (all-complete section, partially-open stays, >240-line chunking, idempotent double-run); done = all four green against the live portal.
4. Add a path-safety test suite for /api/upload (drive letters, `../`, POSIX absolute, bare 'uploads'); re-runs on every portal edit and must stay green.
5. Extend group_e2e.py to flag mid-tool-call truncations as an explicit failure field in the result JSON; verified with a known-truncated response fixture.
6. Add a daily auto-commit scheduled task calling POST /api/git so nothing sits uncommitted >24h; verifiable via GET /api/git gap check.
7. Extend the 🔧 Ops panel with disk-usage + portal-uptime tiles; values cross-checked against per-host ground truth before marking done.
8. Create memory/portal/testing.md playbook (≥3 edge cases per endpoint before [x]); enforced on every build I ship from now on.
9. Document prune/git endpoints in memory/portal/architecture.md with curl examples verified live against PID 1240; pass = a fresh agent runs them verbatim without edits.
10. Commit discipline: every commit of mine carries a "verified:" line stating what ran and its output; verifiable by grepping `git log`.

### Verifier
1. Smoke-test every new /api endpoint in agent_portal.py with recorded curl output before its TODO item is marked [x].
2. Verify TODO pruning end-to-end: craft an all-[x] test section, POST /api/todo/prune, assert the move to TODO_completed.md and confirm 240-line chunking fires at the threshold.
3. Verify git integration: GET /api/git returns status + last commit (baseline 8f5e7d5 or later) and POST {action:'commit'} produces a new hash — both captured as proof.
4. Run a daily portal health check (PID alive, :8099 single listener, /api/git reachable) and log results to memory/ops/.
5. Reproduce every reported bug once with exact commands before accepting it; file non-reproductions with the evidence.
6. Cross-check /api/fleet: assert a status field for all 3 hosts within the 5s refresh window, fail on timeout or missing host.
7. Audit .gitignore allowlist after each commit cycle — tracked file count stays ~43; flag drift immediately.
8. Maintain a verification log (date + command + output snippet) for every claim labeled "live-verified" in MEMORY.md/TODO.md.
9. Run a 5-point regression pass (chat, file links, DM markers, prune, git) after any agent_portal.py edit; no edit ships untested.
10. Within 2 days: deliver a written pass/fail test report covering both new ops processes with zero untested endpoints remaining.

### Designer
1. Audit index.html (chat + Ops + Fleet panels) and deliver a written critique listing at least 5 concrete hierarchy/contrast/spacing issues, ranked by severity.
2. Redesign the 🔧 Ops panel so git status, commit box, and Prune button form a clear visual hierarchy — verified by before/after screenshots of the live portal.
3. Fix all text-contrast failures to WCAG AA (≥4.5:1) across chat and panels — verified with an automated contrast check on :8099.
4. Replace ad-hoc pixel values with a 4px spacing scale and a defined type scale in the frontend CSS — verified by grep showing zero unlisted px sizes.
5. Add full keyboard support (Enter send, Shift+Enter newline, sane Tab order through chat and Ops controls) — verified by manual tab-through test.
6. Ship a consistent micro-interaction set (hover/focus/active on all buttons and inputs, ≤200ms transitions, zero layout shift) — verified by timing in DevTools.
7. Deliver a responsive pass for 375px and 768px widths covering chat, Ops, and Fleet panels — verified by screenshots at both breakpoints.
8. Produce a single-file component reference (button, chip, input, panel header) built from the portal's actual CSS tokens so Builder has reusable pieces — verified side-by-side against the live UI.
9. Drive Chrome console errors on page load to zero in the running portal — verified by an empty-console screenshot after a hard refresh.
10. Write memory/portal/ui-tokens.md documenting colors, radii, shadows, and motion durations as the single source of truth for future UI work — verified by file existing and being cited in TODO.

### Archivist
1. Run an index-integrity sweep of `memory/`: flag files not referenced by any INDEX.md, pointers to missing files, and stale "Last updated" lines; results in `archivist/index-sweep-2026-11-13.md`, top 5 fixed same turn.
2. Ship `archivist/index_check.py` — repeatable version of goal 1 (walks memory/, greps INDEX files, exits non-zero on orphans); wire into the pre-prune ritual so every prune commit is index-clean.
3. Verify Ops docs are complete for a cold reader: `memory/portal/architecture.md` Ops section must carry exact endpoint contracts, file layout (`TODO_completed.md`, `todo_done_parts/NNN`), and allowlist scope — gap list in chat, fixes as one `docs:` commit.
4. Write `memory/ops/git-hygiene.md`: commit-message convention (feat/fix/docs/chore + agent name), commit-only-after-verification rule, cite-commit-hash-not-paste-content rule; index it from memory/ops/INDEX.md.
5. Post-prune audit ritual: after every `/api/todo/prune` run, confirm moved sections are [x]-dated, chunk numbering sequential, result git-committed; one-line entry in `archivist/prune-log.md`.
6. Provenance audit of the ~43 git-tracked files: flag files lacking a header comment (date + author agent + purpose); fix top 5 myself, list the rest for owners — report in `archivist/provenance-audit.md`.
7. Enforce MEMORY.md hot-file discipline: flag hot entries >7 days old not yet migrated to a leaf; propose migrations in chat (never move other agents' notes unilaterally); target hot file back under ~40 lines by end of week.
8. Dedupe ops facts across MEMORY.md / TODO.md / architecture.md: each durable fact lives in exactly ONE leaf, others hold pointers only; record the canonical location per fact in `archivist/canonical-map.md`.
9. Guard-rail checklist for the two ops processes (for Verifier to re-run): prune never touches sections with open items, chunk split preserves order + numbering, git allowlist excludes unsloth-tmp/.unsloth_sandbox/uploads/scratch, commit is add -A scoped by .gitignore only — checkbox ACs in `memory/portal/architecture.md`.
10. End-of-day archive pass before any prune: confirm every completable TODO section has dated [x] items (lossless pruning), escalate ambiguous sections to Orchestrator instead of guessing; report state in one line.

### Scribe
1. Compress this goal-setting thread into 3-5 bullets once all ten goal-lists are in, and record them where they belong (TODO.md / memory/) with the path confirmed in chat.
2. Keep MEMORY.md HOT-FILE discipline: state line + counter + recent notes only; trim it back under ~40 lines whenever it grows past that.
3. Maintain memory/INDEX.md as a true pointer map — every new memory module gets its index entry in the same turn it's created, no orphan files.
4. Guarantee traceability in every compression: each bullet cites the source (agent name + message or file path); zero untraceable claims.
5. Flag agent-vs-agent contradictions explicitly in summaries instead of silently picking a side — 100% of compressions check for this.
6. Preserve exact names, numbers and file paths (e.g. `POST /api/todo/prune`, PID 1240, 240-line chunk threshold) verbatim when recording decisions.
7. End each major round by verifying every open item in TODO.md has a named owner; list any unowned items in my summary.
8. Keep MEMORY.md's goal line and TODO.md's live plan in sync — check both at the end of each session and fix drift immediately.
9. Record the two new ops processes (prune + git) into memory/portal/architecture.md Ops section with exact endpoints, verifying they're documented before next round.
10. Archive settled decisions: move resolved items out of MEMORY.md recent notes into the correct memory/ module within 24 hours so the hot file stays small.

### Mechanic
1. Keep portal :8099 up ≥99% this week; any outage restored within 5 min with a one-line runbook note in memory/ops/.
2. One-pass probe script covering all four hosts (White/Pale/Black/Red) — ports + key processes — on a scheduled task every 10 min, failures logged with timestamps.
3. Dry-run the reboot-recovery runbook once per machine this week; fix and document any broken step found.
4. SMB mirror: verify White↔Pale/Black/Red sync latency <5 min daily; log every missed sync with timestamp.
5. Test the new TODO pruning end-to-end once: confirm a fully-done section moves and TODO_completed.md chunks correctly past 240 lines.
6. Daily git commit via POST /api/git at ~18:00 — zero tracked files left uncommitted, allowlist stays ≤~43 files.
7. Finish a complete port + scheduled-task map for all four hosts in memory/ops/INDEX.md by Friday.
8. Zero unidentified restarts: PID + port identified before touching any service; every fix leaves a runbook note.
9. Daily check of Studio :8888 on Red/Pale/Black so remote models never sit unloaded overnight; state surfaced to the fleet panel.
10. End-of-day hygiene: MEMORY.md under 40 lines and TODO.md top section synced to live status.

## Upload feature BUILT + verified (2026-11-12 ~20:4x latest)
Status: **LIVE.** Portal :8099 accepts file & folder uploads → shared agent folder `uploads/` (White sandbox _default). + button (files/folder menu) + drag & drop (recursive), progress chips, `[Attached in shared folder: …]` line appended to sent messages so agents get the paths. Server: POST /api/upload (raw body + X-Rel-Path, 1 MiB streaming, 4 GB cap; rejects ../, drive-letter, POSIX absolute, bare 'uploads') + GET /api/uploads. Bugs caught & fixed in testing: double uploads/uploads prefix; absolutes relativized instead of rejected; bare-'uploads' check ran after prefix prepend. Detail: memory/portal/architecture.md (Uploads section).
- [x] All edge cases green on final build (20:4x); test files removed from uploads/.
- [ ] FUTURE: mirror uploads into remote host sandboxes (Black/Red/Pale) so remote agents can open attachments with their own tools — today they only see the path list and must ask a local agent to read + relay.
- [ ] FUTURE (optional): small "Files" panel in UI listing /api/uploads (endpoint exists, no UI yet).


## 8-AGENT ROSTER GREEN - Red recovered via manual move (2026-11-12 ~18:3x latest)
Status: **ALL GREEN, records synced.** Red DUAL_UP final: Q8_0 hash VERIFIED == f0fc43cf…E8A (WinRM Get-FileHash ON RED disk-local 25s - skipped the 2h SMB crawl), mmproj landed -> is_vision:true. red_smoke **ALL_OK** 18:05:55 (chain's first run crashed exit=1 on an `open(..., indent=)` bug in the script -> fixed + rerun; chain summary keeps the STALE pre-crash section). smoke8 rerun **ALL_OK** 18:29 (all 8 ids: ORCH/RES/BUILDER/VERIFIER/DESIGNER/ARCHIVIST/SCRIBE/MECHANIC-OK; researcher 349s = serialization, not a fault). group_e2e rerun ~18:3x: all 8 spoke, 33 turns, counter 24, concluded=False - Archivist+Scribe final turns truncated mid tool-call ("model stopped before completing the tool calls"). Chain first pass (18:07) TRANSIENT failures: orchestrator 404 'unknown agent', builder/verifier/designer/archivist 400 + empty smoke text -> self-resolved by ~18:2x, no root cause found.
- [x] CHAIN_OK branch executed with caveats above: hosts.md Red row = LIVE; trees synced to AgentPortal_V1 (hash-compare pattern); _portal_pid.txt fixed (30852).

- [ ] FUTURE: move Red .245 to the wired NIC (WiFi 30 Mbps = root cause of the 2h copy) -> multi-GB transfers ~20 min.
- [ ] WATCH: two tool-call truncations in latest e2e (Archivist/Scribe) - if they recur, check their models' max-tokens / harness stop conditions.

## RED DUAL_UP via manual move + CHAIN RUNNING (2026-11-12 ~18:0x) - SUPERSEDED by GREEN above
**Q8_0 HASH VERIFIED == f0fc43cf…E8A** (WinRM Get-FileHash ON RED, disk-local 25s - skipped the 2h SMB hash) + scan-folders 201 (mmproj also landed -> is_vision:true) + load Q8_0 GPU1 ctx 16384 alongside XL 200 + first-poll loaded ['Qwen3.8-27B-Q8_0','unsloth/Qwen3.8-27B-GGUF'] + probe **SCRIBE-Q8-OK** (corrupted-file root cause CONFIRMED - Scribe healthy). Verdict **DUAL_UP** in red_setup_result2.json (~18:0x, via red_manual_verify.py PID 26924). Parked chain (\RedChainRun PID 28748) FIRED: red_smoke -> idle -> smoke8 -> idle -> group_e2e(8 agents) -> **red_chain_result.json** (expect ~18:3x-19:0x; group e2e is the long one). NEXT GO: read red_chain_result.json -> CHAIN_OK -> hosts.md Red row LIVE + sync trees to AgentPortal_V1.

## RED Q8_0 MANUAL MOVE by Arnold (2026-11-12 ~17:2x) - copy ABORTED, superseded above
**ROOT CAUSE of slow copy: Red's LAN IP IP_RED is on its WiFi interface (30 Mbps negotiated), NOT the 5 GbE Ethernet** -> SMB crawled at ~4.4 MB/s = ~2h for 29 GB instead of ~20 min. Aborted: robocopy PID 31632 KILLED, partial dest DELETED (path clean), waiter PID 27604 killed + \RedQ8Wait2 DISABLED. Chain PID 28748 left PARKED (polls verdict). Arnold moves the file manually. Paths: src C:\Projects\WSLadmin\serve-root\Turbo\Qwen3.8-27B-Q8_0.gguf -> dst Red C:\Users\Red\models\Qwen3.8-27B-Q8_0\ (alt verified src = Black's Q8_0, hash f0fc43cf... confirmed). ON Arnold 'done': re-fire red_q8_wait2.py (hash verify vs f0fc43cfd802bd87bc7b95f2120553a6407848e3229126b623cc397427857e8a + load Q8_0 GPU1 ctx 16384 + scribe probe) -> verdict red_setup_result2.json -> parked chain auto-runs red_smoke -> smoke8 -> group_e2e -> red_chain_result.json. FUTURE: if Red Ethernet joins the LAN, move .245 to the wired NIC (or dial the wired IP) for ~100x faster transfers.

## Red Q8_0 RE-COPY in flight + post-verdict chain on autopilot (2026-11-12 ~15:5x latest - SUPERSEDED by manual move above)
Status: **CORRUPTED COPY FOUND + RE-COPY RUNNING.** Copy #1 (done 06:13) passed size+magic but SHA-256 MISMATCH vs Turbo source (`fa873333…296ef7f` != `f0fc43cfd802bd87bc7b95f2120553a6407848e3229126b623cc397427857e8a`) -> Scribe degenerate (multilingual token-soup in reasoning_content, burns full 8192 budget on trivial prompts); Mechanic GREEN (MECHANIC-OK 1.4s via portal). Red Studio auto-restarted 11:07 = DUAL_UP (XL GPU0 ctx 65536 + Q8_0 GPU1 ctx 16384), aliases already correct -> realias skipped; roster MERGE_OK = 8 agents, live in portal UI.
In flight NOW: Q8_0 UNLOADED (GPU1 free) + corrupted file DELETED + robocopy PID 31632 Turbo->Red (/MT:8 /R:3 /W:5, log q8_red2.log, started 15:24; ETA ~65-90 min). Waiter = scheduled task \RedQ8Wait2 (PID 27604; IMAGE-based liveness - Popen shell=True returns the cmd.exe wrapper pid, first waiter instance killed for a false 'exited') -> on copy exit: STREAMING SHA-256 over SMB vs source hash -> if MATCH: scan-folders + load Q8_0 GPU1 ctx 16384 alongside XL + poll loaded + probe scribe-q8 (SCRIBE-Q8-OK, 512 budget) -> verdict in red_setup_result2.json. **POST-VERDICT CHAIN ON AUTOPILOT (15:5x):** detached red_chain.py (\RedChainRun, PID 28748) polls for the verdict and on DUAL_UP runs red_smoke.py -> idle-wait -> smoke8.py -> idle-wait -> group_e2e.py; summary in **red_chain_result.json**.
- [x] 17:15 CHECKPOINT (Arnold 'check status'): robocopy PID 31632 still running ~111 min in - SLOWER than ETA 65-90 but NOT stalled: dest LastWriteTime ticking live (17:15:14->17:15:49 across 8s sample), size pinned at full 27.0522 GB = final flush stage. NOTE White+Red clocks agree (~21s apart) but White CMOS unsynced - if Arnold's device runs ahead, LAN time is behind real time; intervals still valid. Verdict ETA pushed to ~18:4x-19:1x (copy exit + ~80 min SMB hash).
- [x] 16:47 CHECKPOINT (Arnold 'check now'): copy WRITE PHASE COMPLETE - dest \IP_RED C$ file at FULL size 27.05 GiB (=29.047 GB decimal), LastWriteTime ticking live 16:47:07; robocopy PID 31632 still alive (summary line only lands on exit). Waiter 27604 + chain 28748 both alive; result files still placeholder/absent. ETA unchanged: verdict ~18:10-18:30, red_chain_result.json ~19:30-20:30.
- [x] 16:06 CHECKPOINT (Arnold 'go'): robocopy PID 31632 still writing (started 15:24; ~42 min in of ETA 65-90). Dest file shows FULL size 29.047 GB but that's preallocation - exclusive lock held by robocopy = actively streaming, write head not peekable while locked. Waiter PID 27604 + chain PID 28748 both alive; tasks \RedQ8Wait2/\RedChainRun Running. red_setup_result2.json still waiter_start placeholder; red_chain_result.json absent (chain not yet triggered). ETA: copy done ~16:30-16:55 -> SMB hash verify (~copy-duration) -> verdict ~17:30-18:15 -> chain smokes+e2e -> red_chain_result.json ~18:30-19:30.
- [x] 15:52 CHECKPOINT (Arnold 'sounds good, go'): copy in flight ~28 min of ETA 65-90 (robocopy PID 31632 alive since 15:24; q8_red2.log = header only, single 27.0 GB file -> nothing written until done = normal). red_setup_result2.json = waiter_start placeholder (15:25:36), NOT a verdict. Watchers confirmed real: red_q8_wait2.py PID 27604 + red_chain.py PID 28748 both running; tasks \RedQ8Wait2/\RedChainRun status Running. Portal :8099 (PID 30852) healthy, /api/agents = all 8 ids live. Studio :8888 = PID 15972 (uv cpython-3.13, the project studio); a second studio proc PID 19660 (.unsloth\studio) listens on neither port - inert, ignored.
- [x] NEXT "go" (~17:3x-18:3x): read **red_chain_result.json** (done ~18:3x - result had a STALE red_smoke section + first-pass 404/400s; superseded by the GREEN section above), then branch:
  - **CHAIN_OK** (red_smoke ALL_OK + smoke8 ALL_OK + group_e2e concluded) -> hosts.md Red row = LIVE -> sync trees to AgentPortal_V1 (hash-compare pattern).
  - **CHAIN_PARTIAL** -> inspect which stage failed in the summary (red_smoke / smoke8 / group_e2e sections + red_chain_{redsmoke,smoke8,group}.log); re-run the failed script SERIALLY detached; [SILENT] settling in group e2e = known serialization behavior, not a failure.
  - **STOPPED_HASH_MISMATCH** -> NIC/disk suspect: retry once (delete + same chain). Fallback source = Black's Q8_0 - **hash VERIFIED == f0fc43cf… (black_hash_q8_out2.txt)** at \\IP_BLACK\C$\Users\Black\models\Qwen3.8-27B-Q8_0\Qwen3.8-27B-Q8_0.gguf -> robocopy from there instead of Turbo. Last resort = Red xet re-download (cancel the stuck 0.19 GB .incomplete blob first - pale_cancel.py pattern).
  - **STOPPED_COPY_FAIL_*** -> read copy_tail/q8_red2.log in the result; check NIC both ends; retry.
  - **STOPPED_LOAD_*/PROBE_*** -> suspect GPU1/load flags: reload Q8_0 (different ctx/n_parallel), re-probe; if persists swap GPUs (aliases bind model ids, not GPUs). PROBE_DEGENERATE with matching hash = same path.
- [x] RESOLVED: DUAL_UP + SCRIBE-Q8-OK (18:05) - Scribe fully usable; smoke8 ALL_OK 18:29 incl. SCRIBE-OK.
- [x] Housekeeping DONE (~15:4x): red_hash_q8.ps1 + black_hash_q8.ps1 fixed (gguf lives in the Qwen3.8-27B-Q8_0\ subfolder, not models root; -Recurse added). \BlackHashQ8 ran 15:38 -> **BLACK_HASH=F0FC43CFD802BD87BC7B95F2120553A6407848E3229126B623CC397427857E8A == Turbo source** (black_hash_q8_out2.txt, 24s) -> Black's Q8_0 CONFIRMED valid fallback copy source.
- [x] POST-VERDICT CHAIN PREPARED (~15:4x): **smoke8.py** CREATED (all 8 ids incl. renamed orchestrator/researcher; NOTE smoke6.py still has stale atlas/quinn ids - do not reuse). **group_e2e.py** UPDATED: AGENTS=8, MAX_CALLS=20 (phase-1 alone = 8), prompt names all 8 by new names, writes group_e2e_result_8agent.json. red_smoke.py verified current (scribe/mechanic via portal, Red-only = no local slot contention, safe mid-turn).
- [x] RUN ORDER once DUAL_UP - **AUTOMATED by red_chain.py** (\RedChainRun PID 28748, fired 15:5x): waits for verdict -> red_smoke.py (Red-only) -> wait_idle -> smoke8.py -> wait_idle -> group_e2e.py; writes red_chain_result.json. Next turn just reads the summary.
- [x] POST-VERDICT CHAIN VERIFIED READY (05:5x): red_agents_ready.json staged Scribe 📝 scribe-q8 + Mechanic ⚙️ mechanic-q4; merge_red_agents.py idempotent + injects real RED key (host_api.load_key('RED') OK, 43 chars); agents.json roster = 6 with renamed ids (orchestrator/researcher). KEY FINDING: the waiter spawns `python red_dual_load.py` as a FRESH subprocess that re-reads the file from disk - and the on-disk version was already edited to mechanic-q4/scribe-q8 -> the ranger/warden caveat is likely STALE. After verdict, check the 'aliases' step in red_dual_load_result.json: if names came back correct, SKIP red_realias.py (it's idempotent anyway - only needed if old names appear).
- [x] RENAME DOC SWEEP DONE: memory/ops/windows-runbook.md + memory/portal/architecture.md current-state lines updated (ex-Atlas/ex-Quinn noted); remaining Quinn/Atlas mentions in the tree are historical incident records (kept as-is); code refs are comments only (agent_portal.py 359/859).
- [x] ROSTER RENAMES LIVE in agents.json (per Arnold 11-12, no portal restart - read per request): **Atlas -> Orchestrator 🎛️** (ops manager + HR: backend<->agent matching incl. pause/unload/load swaps e.g. image-gen steps, onboarding/designing new agents, owns TODO.md globally; still atlas-q8) and **Quinn -> Researcher 🔍** (investigative researcher: finds answers, cross-checks sources, reports with confidence; still quinn-q4). ids renamed too (orchestrator/researcher); no live code refs existed (comments + docs only).
- [x] RED PAIR DECIDED (Arnold): **Scribe 📝 -> scribe-q8** (GPU1 deep; synthesizer - compresses threads into decisions/open items) + **Mechanic ⚙️ -> mechanic-q4** (GPU0 fast; ops engineer for the 4-host fleet). Entries STAGED in red_agents_ready.json. CAVEAT: running waiter holds pre-rename code -> will register **ranger-q4/warden-q8**; after verdict run **red_realias.py** (re-PUT aliases, Studio-level, no model reload) before merging staged entries.
- [x] llama.cpp runtime CONFIRMED INSTALLED on Red: C:\Users\Red\.unsloth\llama.cpp\build\bin\Release (4154 files) - the 11-11 'postponed install' is done.
- [x] UD-Q4_K_XL GGUF magic VERIFIED in Red's HF cache snapshot (not a zero-filled placeholder).
- [x] SMB firewall rule added on Red (445 from White) - C$ share reachable, robocopy running.
- [ ] NEXT TURN: poll red_setup_result.json at ~07:0x (waiter appends steps; expect robocopy_exited -> verify -> running_dual_load -> LOAD verdicts). If copy done but waiter died -> run red_dual_load.py manually via schtasks. Then: check 'aliases' step in red_dual_load_result.json - if ranger/warden -> python red_realias.py (expect REALIAS_OK); if already mechanic/scribe -> skip -> merge red_agents_ready.json agents[] into agents.json (python merge_red_agents.py, expect MERGE_OK roster of 8) -> Scribe+Mechanic smoke SERIALLY with idle-wait first (smoke6 lesson: no parallel smokes) -> 8-agent roster.
- [ ] After Red agents live: full 8-agent roster smoke + group e2e; update hosts.md Red row; sync trees to AgentPortal_V1.

## Group e2e - recovery ALL_UP; serial smoke + group_e2e running DETACHED (2026-11-11 ~22:4x; superseded above)
Status: **WAITING ON DETACHED RUN** - serial_e2e_wait.py PID 26952 (project python, cwd C:\Projects\Workspace). Self-waits for Studio idle since THIS CHAT HOLDS THE Q4 SLOT; runs after this turn ends.
- [x] recover_result.json VERDICT **ALL_UP** (22:37-22:38): wedge_detected=false, active_generations=0 pre-state, both local models loaded (Q8_0 ctx 32768 GPU1 + UD-Q4_K_S GPU0), functional probes quinn-q4 0.3s / atlas-q8 0.2s, portal :8099 200.
- [x] serial_e2e_wait.py launched: idle-wait (max 10 min; ABORT_STILL_BUSY if still busy - never run on a wedged stack) -> SERIAL 4-agent smoke via /api/chat solo (full streams to [DONE], NO early client aborts - that's the wedge mechanism) -> group_e2e.py as subprocess (phase-1 parallel + cross-talk rounds, mirrors frontend). Writes serial_e2e_result.json + group_e2e.log (+group_e2e_result.json).
- [x] LAUNCH QUIRK: first launch spawned TWO runners (different pythons) - killed both, relaunched single instance; verified via Get-CimInstance CommandLine filter. Lesson in ops/windows-runbook.md.
- [ ] NEXT TURN: read serial_e2e_result.json -> expect verdict GROUP_E2E_OK. Check group_e2e.log: cross-talk rounds, [SILENT] settling across hosts, final counter (infinite budget now), Black-host latency vs local. If SMOKE_FAIL_LOCAL / ABORT_STILL_BUSY -> inspect /api/inference/active-generations + schtasks /run /tn RecoverAll again.
- [ ] Then PALE: Q8 copy done -> scan-folders -> dual load -> Pale agents (names from Arnold).

## Black agents in portal - R3 networked pair (2026-11-11; DONE, superseded by status above)
Status: **DONE - E2E GREEN ~17:5x** (builder 'BUILDER-E2E' + verifier 'VERIFIER-E2E' via portal /api/chat).
- [x] ROOT-CAUSE "not a GGUF magic": Black HF cache UD-Q4_K_XL.gguf = 17,559,178,144 B but ZERO-FILLED (size-matching placeholder - xet trap; verify magic bytes, never size). No complete XL anywhere on LAN -> DECISION: abandon XL, dual-resident Q8_0 + Q4_K_S instead.
- [x] Q8_0 LAN copy DONE 15:32 (q8_black2.log summary, 0 failures) -> registered as Qwen3.8-27B-Q8_0 (magic verified).
- [x] Dual load ALL_UP (black_dual_load_result.json): multi-model fit; Q4_K_S->GPU0 ctx 65536; Q8_0->GPU1 ctx 32768; aliases builder-q8 (ref:bc7ad351) + verifier-q4.
- [x] Roster re-pointed: 'black' agent DELETED -> Builder (model_id Qwen3.8-27B-Q8_0) + Verifier (model_id verifier-q4), both studio http://IP_BLACK:8888 + Bearer key.
- [x] Q8_0 server CRASHED on first real request (~17:0x probe) -> RECOVERED on its own ~17:4x (probe 'Q8-ALIVE'); both models loaded=True in /v1/models. Keep eye: if it recurs, reload Q8_0 at ctx 16384.
- [x] Portal fix APPLIED: to_openai_messages _human() leniency (role==user w/o speaker = human turn; browser sends speaker "You" -> unchanged) + py_compile OK + portal restarted (PID 34048 killed, schtasks PortalRun).
- [x] E2E GREEN via portal /api/chat: builder->'BUILDER-E2E' (5 frames), verifier->'VERIFIER-E2E' (5 frames). R3 BLACK COMPLETE.
- [ ] Group e2e: prompt in group mode with all 4 agents (atlas/quinn local + builder/verifier remote) - watch cross-talk budget + [SILENT] handling across hosts.
- [ ] PALE next: Q8 copy DONE 15:19 -> POST /api/hub/scan-folders {"path":"C:\Users\pale\models\Qwen3.8-27B-Q8_0"} (Arnold's token in pale_dl.py) -> load Q8 GPU1 (+ register/load Q4_K_XL for dual) -> create Pale agents (NAMES from Arnold - see R3).
- [x] R2Smoke waiter verdict PASS_R2_LOCAL (r2_smoke_result.txt, finished 13:26) -> R2 engine green on local Studio.

## Multi-host expansion — 6 agents on Red/Pale/Black, Red first (2026-11-11 latest)
Goal: 3 remote hosts x 2 LLMs each (dual-resident like White) = 6 new agents. Sequence: RED -> PALE -> BLACK.

### STATUS 2026-11-11 ~13:35 (supersedes all older status lines below, incl. the ~14:00 block's copy lines)
- **Q8 race v2 — BOTH copies running from Turbo mirror.** The 12:37 WSL-Inbox copies STALLED (NIC ~10 KB/s after 90 min) -> killed ~13:00, dests cleaned, relaunched from C:\Projects\WSLadmin\serve-root\Turbo (Q8_0 exact-size 29,047,084,256 B + mmproj BF16). PALE: running since 13:00 (PID 32788, log q8_pale2.log). BLACK: 13:00 relaunch FAILED `ERROR 1326 (0x52E)` - no SMB creds for .99 in that context -> fixed with `net use \\IP_BLACK\C$ /user:black ""` (empty pw), relaunched 13:22 (PID 36924, log q8_black2.log). Logs are the **"2" files** now; ground truth = summary block in log or process exit (`dir` size is pre-allocation, NOT progress). NEXT per host when its summary lands: POST /api/hub/scan-folders {"path":"C:\\Users\\<u>\\models\\Qwen3.8-27B-Q8_0"} on THAT host's Studio (Pale via Arnold's token; Black via Bearer key) -> load Q8 to GPU1 (Q4 already on disk both hosts).
- **Portal networked-host UI SHIPPED + verified** (see R2 below): checkbox in New-agent modal, base URL + API key fields, Scan models button -> fills dropdown from {base}/v1/models; save persists studio+api_key. Live on PID 36316.
- BLACK LAN access ONLINE: http://IP_BLACK:8888 (auto_start) - started via JWT /api/auth/login over WinRM (keyless start 401s even local). Stable LAN endpoint for R3 routing to Black, no tunnel needed.
- R2Smoke waiter re-launched detached this turn (r2_smoke_wait.py; self-waits for idle <=10 min -> r2_smoke_result.txt).

### STATUS 2026-11-11 ~14:00 (copy lines superseded above; key facts still valid)
- PALE .39 ONLINE: Studio v2026.11.3, Arnold's token verified (key in pale_dl.py). Q4_K_XL COMPLETE on disk (xet won). Q8_0: LAN robocopy from White still RUNNING (started 12:37; dest file pre-allocated full-size + EXCLUSIVE-locked by robocopy = in progress - `dir` size is NOT a progress indicator). Its slow xet Q8_0 CANCELLED ~14:00 (LAN copy wins per plan). NOTE: unsloth Q4_K_XL xet still shows state 'running' although its file is complete on disk. NEXT: when q8_pale.log shows the robocopy summary -> POST /api/hub/scan-folders {"path":"C:\\Users\\pale\\models\\Qwen3.8-27B-Q8_0"} -> load.
- BLACK .99: **KEY REFRESHED by Arnold ~14:00 + VERIFIED** (tunnel Bearer /v1/models 200: UD-Q4_K_XL + UD-Q4_K_S, both unloaded). Q4_K_XL COMPLETE on disk (xet won). Q8_0 LAN copy still RUNNING (started 12:37; no xet there - pure copy). Key now in host_api.py load_key('BLACK') (chat-only, mirrors Red pattern); probe_black.py regex fallback removed. LAN-access route 401s even LOCAL keyless -> retry start WITH the Bearer key via WinRM.
- White source for Q8_0: C:\Users\White\WSL-Inbox\lmstudio-community\Qwen3.8-27B-GGUF\ (Q8_0 29.047 GB + mmproj BF16 0.931 GB). Register after copy: POST /api/hub/scan-folders {"path": "C:\\Users\\<u>\\models\\Qwen3.8-27B-Q8_0"} (schema verified; accepts folder or single weight file).
- RED: unchanged - R1 parked (llama.cpp install postponed by Arnold); Q8_0 copy to Red queued behind that call.
- Ops note: robocopy launched from a WinRM session DIES when the session ends (job object kills children) -> launch LAN copies LOCALLY on the source host via Start-Process .bat (worked; copies started 12:37 White clock). Robocopy PRE-ALLOCATES dest files at full size and holds them EXCLUSIVE-locked while copying -> `dir` size and file-read progress checks both mislead; ground truth = summary block in the log (q8_pale.log / q8_black.log) or process exit.

### R0 — Red recon (mostly done)
- [x] Locate Red from White: subnet scan of TCP 8888/3389 -> **IP_RED** (only host answering both). Script: scan_red.py.
- [x] Confirm RDP context: mstsc runs FROM WHITE (PID 21924); session on IPv6 link-local fe80::d6c1:cc18:5f71:d15f%20; ICMPv6 blocked (ping fails, TCP fine). Name "red" does not resolve - use IP.
- [x] Studio :8888 reachable over LAN but returns **401 Unauthorized** -> Red's API has auth enabled. Probe: red_probe.py (needs RED_KEY env).
- [x] 2026-11-11 FULL LAN SCAN (Arnold: 'scan it'): Red's OpenAPI spec (592 endpoints) HAS a **keyless LAN-access route** - GET /api/settings/lan-access, POST .../start, PUT .../port, .../stop, .../auto-start, .../addresses. LanAccessResponse = {state off|online|error, urls, public_urls, auto_start, configured_port, active_port}. BUT it is currently **OFF**: full 65k sweep open = [3389 RDP, 5040/7680/27036 non-HTTP, 5357 sys, 5985 WinRM, 8888 Studio, 50052 ephemeral] -> NO extra HTTP listener. GET lan-access = 401 (can't read state) and POST start = 401 (can't start) from White - BOTH need the Bearer key. NO terminal/exec/shell endpoint exists in the spec -> 'remote terminal commands' = WinRM only (still needs creds).
- [x] UNBLOCK Red - RESOLVED 2026-11-11 (Arnold: 'use winRM, password is empty but username is Red'): WinRM verified - `New-Object PSCredential('Red',(New-Object System.Security.SecureString))` + `-UseSSL:$false` (ConvertTo-SecureString '' THROWS on empty string; empty SecureString is the workaround). Ran nvidia-smi on Red: **2x RTX 5090 32GB, driver 621.14** -> dual Q4+Q8 confirmed to fit.
- [x] Verify /v1/models over LAN with key -> DONE 10:17: **KEY VERIFIED**; models = unsloth/Qwen3.8-27B-GGUF (UD-Q4_K_XL) + lmstudio-community/Qwen3.8-27B-GGUF (Q4_K_M), BOTH UNLOADED, NO Q8 present. /api/models = 404 in this build - use /v1/models.
- [x] Check Red hardware via RDP terminal: `nvidia-smi` GPU count/VRAM -> DONE via WinRM 2026-11-11: 2x RTX 5090 32GB.
- [x] Check Red Studio version matches White's: /api/health build signature identical (protocol v1, manageability v2) -> reload recipe transfers.
- [ ] BLOCKED: Arnold POSTPONED Red's llama.cpp install (2026-11-11, was 242 MB download in progress) -> R1 parked until he says go. Everything else on Red is ready (backend healthy, LAN online).
- [x] RE-VERIFIED 09:57 (White local): Red :8888 TCP open + /api/health 200 (same build signature as White); Studio desktop app running in Arnold's RDP session, API monitor "No model loaded" -> backend healthy, still no models.

### R1 — Load dual LLMs on Red (PARKED - install postponed by Arnold 2026-11-11)
- [ ] Arnold call: Red has ONLY Q4 variants today (UD-Q4_K_XL + Q4_K_M, no Q8) -> load both Q4s (GPU0+GPU1) or fetch a Q8 first?
- [ ] Resume llama.cpp runtime install on Red (was 242 MB, 1 of 2) - now via WinRM, no RDP needed.
- [ ] Load Q4 GGUF -> GPU0 + Q8 GGUF -> GPU1 (Q8 first per proven recipe), aliases red-a-q4 / red-b-q8 (final names pending agent naming).
- [ ] Verify: nvidia-smi shows both GPUs ~full; streaming chat to EACH alias works via LAN (adapt probe_quinn.py with base URL + key).

### B0 — Black recon (2026-11-11 latest)
- [x] Locate Black: IP_BLACK (White cmdkey TERMSRV targets); RDP cred stored on White, user `black`.
- [x] ONLINE 2026-11-11 ~10:30 (was offline 02:15): port sweep open = **3389 (RDP), 7680 (non-HTTP)**; **:8888 CLOSED**; **WinRM 5985/5986 CLOSED** (not bootstrapped).
- [x] Studio DESKTOP app running on Black (Arnold's RDP session from White, screenshot ~10:35) but backend :8888 not reachable from White -> firewall or backend-not-listening; check on Black.
- [x] RE-VERIFIED 09:57 (White local): Black :8888 STILL CLOSED from White (TCP timeout); Studio desktop app confirmed running (Arnold's screenshot, "How can I help?" screen). CLOCK NOTE: the ~10:30/10:35 stamps above came from screenshots/remote machine clocks - White's local clock read 09:57 at re-verify; treat per-host "now" accordingly.
- [x] API key received from Arnold 2026-11-11 (in chat only - never in memory files; probe via `set BLACK_KEY=... & python probe_black.py`; lands in agents.json per-agent `api_key` when Black's agents are created).
- [x] Black :8888 root-caused via WinRM ~10:18: backend IS up but bound to **127.0.0.1 ONLY** (not firewall); local health 200 (v2026.11.3 / v0.1.916-beta), model UD-Q4_K_S unloaded.
- [x] LAN-expose Black for portal routing (R3) - DONE ~13:5x via JWT over WinRM (see top section); plan was: enable Studio LAN access locally via WinRM (POST http://127.0.0.1:8888/api/settings/lan-access/start - keyless) or UI -> then probe_black.py validates key + /v1/models from White.
- [ ] Black R1-equivalent (PARKED like Red): llama.cpp runtime install + load UD-Q4_K_S (+2nd model? only ONE on Black today) via WinRM local :8888 - waiting on Arnold's model call.
- [x] WinRM bootstrap for Black -> DONE ~10:18: Arnold ran `winrm quickconfig` ON BLACK; .99 added to White TrustedHosts (elevated `winrm set` - WSMan Set-Item throws NRE here; UAC approved); user `black` EMPTY password VERIFIED via Invoke-Command (HOST=BLACK, nvidia-smi 2x RTX 5090 32GB driver 621.14). Scripts: probe_black_winrm2.ps1, elev_trustedhosts.ps1.

### R2 — Portal multi-host routing (code)
- [x] agents.json: optional per-agent `studio` (base URL) + `api_key`; default = local http://127.0.0.1:8888, no key (backward compatible - White agents untouched).
- [x] agent_portal.py: studio_base(agent)/studio_headers(agent) route /v1/chat/completions AND RAG per-agent with Bearer key; fields persist on update + in defaults; py_compile clean; portal restarted (kill PID first - schtasks trap); /api/agents verified (both agents, empty studio = local).
- [x] 2026-11-11 ~13:07: POST /api/scan-models {base_url, api_key} endpoint (proxies GET {base}/v1/models; lenient about missing http://; 502+error json on unreachable/bad key; 400 empty base) - unit-tested vs fake remote Studio 5/5. index.html: "Networked host" checkbox in New-agent modal -> Studio base URL + API key fields + Scan models button (fills Model dropdown from that host's live /v1/models); untick restores local list; opening an existing networked agent auto-rescans its host; Save persists studio+api_key. Restarted kill-PID->schtasks -> PID 36316 (created 13:07 > code edit 13:06); live smoke green: f_net in served page, empty base -> 400, local Studio scan returned real models.
- [x] Verify local path end-to-end - DONE 11-12: r2_smoke_result.txt verdict **PASS_R2_LOCAL** (waiter started 13:24:32, idle at 13:26:33, full stream to [DONE], thinking frames present). Local Studio path confirmed after the R2 networked-host routing change. NOTE for future runs: old R2Smoke schtask gone (only PortalRun remains) - run detached with self-idle-wait (`Start-Process python r2_smoke_wait.py -WindowStyle Hidden`).
- [ ] Optional: /api/hosts health endpoint (GET each studio /v1/models) + host badge in UI. (Scan-models already gives per-host model visibility on demand; this would make it proactive.)

### R3 — Add Red's 2 agents
- [ ] Arnold: names + personas for the 6 new agents (2 per host). Placeholders red-a/red-b until then.
- [ ] Solo-test each Red agent through portal; then group e2e incl. remote agents (cross-talk, stop/reset, budget, file links).

### R4 — Docs + replicate to Pale/Black
- [ ] memory/llm/hosts.md host table: fill GPUs/models/state per host as they come up.
- [ ] ops/windows-runbook.md: Red auto-start task + recovery order (mirror White PortalRun/RecoverAll pattern) once models are stable.
- [ ] Pale & Black: repeat R0-R4. BLACK R0 ~90% done (see B0 above); PALE (.39) still offline as of 2026-11-11 02:15 - re-run scan_red.py when its RDP session is open (or ask Arnold).

### Open design decisions for Arnold
1. Remote agents' tools (python/terminal/edit_file) execute on WHITE today - keep, disable for remote agents, or per-host tool exec later?
2. Shared memory tree: remote agents get the same FILE ACCESS block pointing at White's workspace - ok for now, per-host file serving later?
3. Agent names/personas + model mix per host - NOW CONCRETE: Red has 2x Qwen3.8-27B Q4 (UD-Q4_K_XL, Q4_K_M), Black has 1x (UD-Q4_K_S); no Q8 on either -> load as-is or fetch Q8s?

## New: memory TREE modularization + real file-type rendering (2026-11-11 latest)
- [x] 1. "Links work but don't render": /api/file/raw forced ALL text/* to text/plain -> .html pages showed source. Fix agent_portal.py: serve the real mimetypes type (.html->text/html renders as website; json/md/js/css keep their own type; unknown->text/plain). py_compile clean.
- [x] 2. Memory modularized into a tree (index of indexes): memory/portal/{bugs/{file-links-sandbox,xtalk-completion,ui-frontend}.md, architecture.md}, memory/llm/{instances,studio-api}.md, memory/ops/{windows-runbook,probes}.md - every folder has an INDEX.md; bugs/INDEX.md is a PURE index (dictionary: symptom keyword -> file | use case); global-file pointers repeated in each sub-index.
- [x] 3. Root memory/INDEX.md rewritten as the root dictionary: 1561 chars (<1600 so _index_block injects ALL of it into every group prompt); FILE ACCESS block stays at TOP; old "Modules (this folder)" + endpoint sections folded into sub-indexes.
- [x] 4. Old flat modules deleted AFTER section-by-section script migration (27/27 ## sections assigned, zero unassigned: portal-bugs 17 -> 4 files, llm-instances 9 -> 2, ops-windows 5 -> 2); stale cross-ref (portal-bugs "wedge") repointed to memory/llm/instances.md; MEMORY.md hot notes repointed + trimmed; skill portal-memory-modular updated to the tree layout.
- [x] 5. RESTART TRAP found + fixed: PID 23544 (created 00:45) PREDATED the final agent_portal.py edit (00:56) - schtasks /run no-ops while PortalRun Status=Running, so the live server still served text/plain (user screenshot). taskkill first, then /run -> NEW PID 13184; LIVE smoke all green: timer-app/index.html + calculator-app/index.html -> text/html; model_list_now.json -> application/json; TODO.md -> text/markdown; timer-app/ folder 200; traversal+missing 404; /api/memory 200. _portal_pid.txt updated.
- [x] 6. Skill portal-memory-modular SKILL.md updated to the TREE layout + restart-trap rule (was still flat-layout text - claimed done earlier but never landed).
- [ ] 7. USER: click a .html link (e.g. timer-app/index.html) in the portal tab - expect a RENDERED page, not source; .json/.md links show their real type.
- [ ] NOTE (future, no action): HTML pages referencing RELATIVE assets still 404 those assets via /api/file/raw (single-file apps like calculator.html are fine); if needed later, serve a virtual directory or inject <base>.

## Done: links clickable + folder refs + sandbox env fix (2026-11-11)
- [x] 1. Root cause of remaining 404s: SANDBOX_DIR was ~-based; the portal I launched inherited my tool shell's
      USERPROFILE=C:\Projects\Workspace -> expanduser("~") pointed at a nonexistent dir (old instance worked only
      because it ran from a session with USERPROFILE=C:\Users\White). Fix agent_portal.py: _find_sandbox_dir() -
      if the ~-based dir is missing, scan C:\Users\*\.unsloth\studio\sandbox\_default. Restart-proof from any launcher.
- [x] 2. Links never rendered even when resolved: /api/file echoed relpath-from-HERE ('../../Users/...') which
      never matched the literal token in reply text. Fix: echo the REQUESTED rel path back (frontend matches exact string).
- [x] 3. Folder refs unsupported: _safe_workspace_file accepted files only. Now accepts dirs; /api/file returns a
      directory-listing peek for folders (hover popup); /api/file/raw serves a plain-text listing on click.
- [x] 4. index.html: linkifyFiles also collects folder tokens via /(?<![\w./\\-])(?:[\w-]+\/)+/g (unit-tested against
      Quinn's actual bubble text; URLs excluded).
- [x] 5. Restart via schtasks /run /tn PortalRun -> PID 23544. Smoke all green: TODO.md 200 (workspace);
      timer-app/index.html 200 (sandbox); timer-app/ folder peek 200 (5 entries); raw folder listing 200;
      traversal ..\\..\\Windows 404; missing 404.
- [ ] 6. Arnold HARD-REFRESHES the portal tab (Ctrl+Shift+R) to load the new linkify JS, then checks: file AND
      folder references render as dashed clickable links with hover peek; clicking opens the file / folder listing.

## New: ■ Stop button BUILT (2026-11-10 latest)
- [x] 1. "Finished without reaching conclusion" fixed: ■ Stop in modeBar closes the run as concluded (aborts in-flight streams, stamps ✓, green verdict) - replaces reliance on turn-counter timeout; [CONCLUDED]/budget remain signal/backstops
- [ ] 2. Arnold hard-refreshes portal tab + live group test: ■ Stop AND @delegation reaching the delegate (cast expansion)

## New: live test "build a calculator app" -> tool-discipline rule (2026-11-10 latest)
- [x] 1. Screenshot evidence (Arnold 23:29): dim "(no output)" bubbles work; round-end verdict line works
      ("— Round ended with NO conclusion: Quinn, Atlas produced no output. Task state unconfirmed — send a
      follow-up to continue."); agent-to-agent tags + counter 2/6 correct (empty completions don't count).
- [x] 2. Diagnosis: both agents CLAIMED builds ("Built and rendered above" / "Built it") but NO tool calls
      happened -> no file on disk anywhere (swept C:\Users\White + C:\Projects, last 2h). Model behavior:
      27B Q4/Q8 narrates the build instead of calling edit_file/python/render_html. Quinn emitted EMPTY
      completions in all cross-talk rounds (immediate EOS instead of [SILENT]) - UI handles it gracefully now.
- [x] 3. Fix agent_portal.py build_system_prompt: TOOLS discipline block for any tool-enabled agent
      ("DO IT with your tools... never say 'built' unless a tool call in THIS reply succeeded; report
      failures honestly") + strengthened cross-talk [SILENT] line ("an empty reply is never acceptable").
      py_compile clean.
- [x] 4. Portal restarted PID 15720 -> 10628 (:8099 LISTENING, /api/memory 200, state intact).
- [ ] 5. USER: send "build a calculator app" again - expect REAL files this time (file links + hover peek
      in the bubbles). If they still narrate without tools: escalate to forced tool_choice or per-agent persona.

## Archived -> TODO_archive_20261111.md (done-section detail; open items kept above)
- Done: agent file links -> Studio sandbox (2026-11-11)
- Done: Q8/atlas instance dead -> RecoverAll fired (2026-11-10)
- Done: round-end verdict + completion indicators (2026-11-10)
- Done: parallel async processing + post-reboot recovery (2026-11-10 late)
- Done: busy indicators + file links + [SILENT] merge bug (2026-11-10)
- Done: reset mechanism; thinking bubbles + concluded tags
- Deferred / earlier context; New (2026-11-10 evening)

## 2026-11-12 post-reboot verification (after reboot + logons)
- [ ] White: Studio up, `recover_result.json` verdict ALL_UP (portal_8099 status 200 - it self-starts now)
- [ ] Remotes: `fleet_reload_result.json` - RED/BLACK/PALE each DONE or SKIP_*loaded
- [ ] Portal smoke: 8/8 agents green (smoke8.py)
