# AUTO-LOOP - idle agents re-enter the work queue within ~1 minute (2026-11-16, Arnold on user request;
# 2026-11-17 BATCH FIRE: all idle agents get their tasks at once)
<!-- parent: memory/ops/INDEX.md | code: agent_portal.py (_autoloop_watchdog + _autoloop_behaviour_hint + "solo" runs) -->

Rule: an idle agent NEVER waits for everyone else to finish. After AUTOLOOP_IDLE_S (60s) of idleness it
re-enters the queue as FIRST PRIORITY - (1) queued human messages, (2) its own open goals (one concrete
step + ledger evidence), (3) a rare maintenance sweep if at 100% ("what else can I do while we wait").

- Scheduler: `_autoloop_watchdog()` ticks every AUTOLOOP_TICK_S (15s); fires only when NO group run is active.
- BATCH FIRE (2026-11-17, Arnold): the watchdog no longer picks ONE agent per tick. For(allThatsIdle) giveTask:
  one solo pass whose cast is EVERY idle seat (cap AUTOLOOP_BATCH_MAX=8), all firing in parallel in a single
  prompt phase. The broadcast prompt has one "@Name" section per seat; each seat works ONLY its own section.
  Seats whose model is not ready (_model_load_status) are excluded from the batch that tick.
- Pass = solo group run (cast=[all idle], extra {"solo": True}) -> ONE parallel turn per seat, then concluded;
  journaled, stall-guarded, evidence-swept + auto-committed like any run. Visible in chat as an
  "AUTO-LOOP (batch pass, N agents in parallel)" prompt.
- BEHAVIOUR ANALYSIS: `_autoloop_behaviour_hint(name)` reads the agent's last substantive group-chat reply and
  steers its task - (1) 'Remaining open: ...' / 'Next step (...): ...' lines -> continue, don't redo;
  (2) blocker claims (unreachable / blocked by / powered off / must run on X) -> work around it, don't re-probe
  the same wall; (3) last auto-loop pass ended WITHOUT [CONCLUDED] (start or end of reply) -> finish in-flight
  work first. The hint is appended to the seat's section.
- Priority per seat: queued human UMQ first (injected into its prompt), else oldest open goal, else maintenance
  sweep only after AUTOLOOP_MAINT_COOLDOWN_S (30 min). Streak cap AUTOLOOP_MAX_STREAK (40) consecutive auto
  passes without human input; any human message/run resets it (autoloop_note_human).
- Idle clock: autoloop_touch(name) on every completed turn (_parallel_turns terminal events); persisted in
  memory/ops/autoloop.json {last_active per agent, streak, last_pass{agent,batch,why,ts}, last_human_ts}.
  Fresh restart seeds with process start time (no burst of passes).
- View: GET /api/autoloop (idle_s + open_goals per agent, streak, paused flag).
