# Round Record - 2026-11-18 (r2) [DRAFT]
Auto-drafted by round_record_draft.py at 2026-11-18T12:18:28.630493

## DECIDED
- Goals "blocked" false positive fixed: _goals_snapshot now counts only explicit "(blocked: ...)" / [BLOCKED] markers (Mechanic cycle-2 #6 "outbound blocked + logged" prose was the 1-blocked artifact); standing rule teaches agents the marker form.
  - owner: Mechanic | source: TODO.md
- BUG 1: per-turn prompt listed CLOSED goals as open (naive regex ignored evidence markers) -> agents re-verified finished work every turn. FIXED: _agent_goals_block now uses the strict ledger + spells out the CLOSURE PROCEDURE (--record command); truncation budget fixed (team rules were cut off at 1400 chars).
  - owner: Builder | source: TODO.md
- BUG 2: agent code edits in the Studio sandbox silently destroyed by push-only sync; index.html additionally reverted by PIN_GUARD every mirror cycle (observed live on my own edit today). FIXED: merge queue snapshots diverged files BEFORE clobber (memory/ops/merge-queue/) + GET /api/merge-queue + POST /api/merge restore+commit + Ops panel UI; TOOLS prompt now teaches the repin procedure; pin advanced 2c6399f2d853 -> e0679e5f0844 (2026-11-16d).
  - owner: Builder | source: TODO.md
- BUG 3: real progress never registered as evidence markers; sweep only matched .md leaves so Builder's .py artifacts could never count. FIXED: sweep now matches index-linked artifacts; first run auto-linked Builder#1 + Designer#1 (legit on-disk scripts).
  - owner: Builder | source: TODO.md
- GIT AS PROGRESS TRACKER: goals ARE registered in git (memory/goals/*.md tracked, auto-committed per turn) - new GET /api/goals/history reads goal files at recent commits (true counts, not diff arithmetic) + stall detection; Goals panel renders the curve. Verified history: cycle-1 0->7->49->52->60->66 -> cycle-2 reset 5 -> live ~22/80.
  - owner: Builder | source: TODO.md
- RESTART portal to load all of the above; then live-verify /api/goals, /api/goals/history, /api/merge-queue and confirm Goals panel renders git-progress row. — DONE 2026-11-18 ~06:50: portal rebooted (PID 35912); live-verified /api/goals, /api/goals/history, /api/merge-queue all 200.
  - owner: Mechanic | source: TODO.md
- Goal-cycle transition completed: cycle 1 closed 80/80 verified; new goals set for all 8 agents x 10 (set 2026-11-16) - canonical memory/goals/<name>.md, record below in `## AGENT GOALS (set 2026-11-16)`; cycle-1 files archived to memory/goals/archive/
  - owner: Orchestrator | source: TODO.md
- Coherence pass applied (SLO pipeline Mechanic#4->Builder#8->Verifier#4; fleet endpoint Mechanic#8; supersession Archivist#5/Scribe#5; memory-health Archivist#2/Scribe#9; Designer#5 replaced - responsive already shipped) - detail: memory/goals/cycle2-kickoff-2026-11-16.md
  - owner: Archivist | source: TODO.md
- Goal-logic bug fixed in agent_portal.py (rid NameError corrupted GOAL_RESET_PENDING.json on consumption); flag repaired with true consumed record; /api/goals live: 0/80, goal_reset_pending=false
  - owner: Orchestrator | source: ./agent_portal.py
- WEDGE SEEN 22:47 (run g-1a1def4): prompt phase hung ~12min after ALL 8 turns completed their frames (5 metas + Builder/Verifier conn errors) - ThreadPoolExecutor exit never returned; no py-spy available to capture stacks. STALL_KILL_S=900 is the safety net. NEXT: add per-turn wall-clock timeout in _parallel_turns (e.g. future.result(timeout=600)) so one stuck worker can't wedge a pass. — FIXED: wall-clock wedge guard in agent_portal.py (~L2753): if NO frame journaled for STALL_KILL_S=900s the run is stopped and the auto-resume watchdog recovers; socket-timeout-only behavior removed.
  - owner: Builder | source: ./agent_portal.py
- FIX 1 (agent_portal.py stream_chat): group-mode turns with reasoning="default" now get FIRST_REPLY_REASONING="low" (same cap as the fast-first path) so thinking + answer fit the window. Verified against Black: verifier-q4 full portal body -> finish=stop, real content.
  - owner: Verifier | source: ./agent_portal.py
- Killed portal PID 28984; Q8 verified healthy (probe 0.4s) and left alone; Q4 force-reload scheduled via schtask \WedgeQ4Recover @18:27 with force_cancel=True (Studio 409s on active_generations otherwise - this chat's own thread counts as active).
  - owner: Verifier | source: TODO.md
- DECISION (human) 11-15: CHG-0002 ACCEPTED - island engine records status=living, accepted=14:50:07, note "all 3 pre-written tests green (T1 live stats 5/5, T2 scratch round-trip 9/9, T3 restart trap honored)". Endpoints live: GET /api/evolution/stats + POST accept/reject verified on PID 26288
  - owner: Orchestrator | source: TODO.md
- Verified end-to-end: portal restarted windowless (new PID **54008**, /api/memory 200, PortalRun Status=Running); MemoryMirrorRun fired 10:57:31 -> fresh log entry, zero visible windows; PortalFleetProbe fired 11:01:01 -> first ever successful scheduled run ("OK all hosts up"); process sweep after both runs: only cmd.exe present is the HIDDEN portal host (53968), no net.exe anywhere.
  - owner: Mechanic | source: TODO.md
- Mechanic #4 CLOSED (SMB mirror <5 min daily): full 3-leg run 10:57:31, all pushed, 0 errors; power-down window's missed syncs timestamped in memory_mirror.log. Mechanic #9 CLOSED (daily remote Studio check): probe + cross-check surfaced live state - **all 3 remotes UP but NO model resident in VRAM** (remote agents can't generate until loaded).
  - owner: Mechanic | source: ./memory_mirror.log

## OPEN
- Continue completing remaining open cycle-3 goals (main lists now unblocked) [owner: Orchestrator]
- SPLIT PENDING (cycle-2 work, decide seams first): agent_portal.py ~173 KB -> modules under a single importable entry (PortalRun task must keep working); TODO.md prune via POST /api/todo/prune (145 KB -> completed sections to TODO_completed.md). [owner: Builder]
- Fleet to adopt: every future file edit follows memory/portal/file-modularity.md (header pointers + budgets); oversized files logged in TODO top section. [owner: Orchestrator]
- NEXT ROUND: load Orchestrator + Researcher models on White (LM Studio), then have both agents ratify/revise their seat-drafted goal sets [owner: Orchestrator]
- VERIFY next run: no agent silently dropped after an error; if Black 400s recur, activity log shows `retry` events before any surfaced error; verdict carries the warn note when lanes failed. Watch Builder turn duration (Q8_0 >5min) - if passes stall on it, per-turn timeout is the next lever. [owner: Verifier]
- VERIFY after 18:30: recover_force_result.json post-probe quinn-q4 ok + trigger_group_run.log shows group-run POST 200 (fresh run picked up automatically; old run marked interrupted with verdict). [owner: Verifier]
- Watch first sequential pass: each agent should complete visibly one-by-one; if any single agent hangs, the stall banner appears after 4 min (sequential = no parallel fault isolation yet - consider per-turn timeout next round). [owner: Builder]
- Round-table wiring: Builder proposes candidates, Verifier runs pre-written tests before any accept ask [owner: Verifier]
- Decision: evolution CLI as agents.json tool for Builder/Verifier lanes [owner: Builder]
- DECISION NEEDED (human): ~50 OTHER tracked files still contain internal 192.168.x.x IPs (you deleted only hosts.md). Scrub the rest (in-place redact / history purge) or leave as-is? [owner: Researcher]
- NEXT (unblocked, follow-up round): Builder H1 `.frow` one-line fix + Designer M3-M6 from the critique; Researcher ledger EVIDENCE_PAT tightening; Mechanic #3 remote legs (pending human OK above). [owner: Designer]
- NEXT (follow-up round, unblocked): Builder H1 fix = rename/scope the dialog `.frow` class in index.html (one-line); Designer M3-M6 fixes from the critique; Researcher: tighten goal_ledger.py EVIDENCE_PAT - bare "verified"/"[x]"/"pass"/"source-cited" inside acceptance criteria currently count as closure (e.g. Builder truly ~7/10, not 10/10; Researcher #10 likewise) - match only explicit `(verified:` / `— recorded` markers. [owner: Researcher]
- NEXT (blocked on human power-on of .39/.99): Mechanic #3 remote reboot dry-runs, #4 full 3-leg SMB latency, #9 all-hosts-up studio day; remote alias half (5 seats) per memory/llm/model-id-check-2026-11-14.md - Red leg now re-testable (.245 up). [owner: Mechanic]
- Researcher #9 (7-day citation audit): in progress, window ongoing, zero dead links reported so far. [owner: Researcher]
- NEXT (blocked on human power-on): Verifier #6 fleet cross-check; Mechanic #3 remote reboot dry-runs, #4 SMB latency, #9 remote Studio checks; remote alias half (5 seats) per memory/llm/model-id-check-2026-11-14.md. [owner: Mechanic]

## METRICS (auto-filled from evidence files)
- orphan_rate: 74.1%
- supersession_broken: 55
- owner_coverage: 0/63 (0.0%)

## AGENTS ACTIVE THIS TURN
- unknown

---
*DRAFT - review and fill before recording. Fields marked TBD need human/agent confirmation.*