# AUTO-LOOP - idle agents re-enter the work queue within ~1 minute (2026-11-16, Arnold on user request)
<!-- parent: memory/ops/INDEX.md | code: agent_portal.py (_autoloop_watchdog + "solo" runs) -->

Rule: an idle agent NEVER waits for everyone else to finish. After AUTOLOOP_IDLE_S (60s) of idleness it
re-enters the queue as FIRST PRIORITY - (1) queued human messages, (2) its own open goals (one concrete
step + ledger evidence), (3) a rare maintenance sweep if at 100% ("what else can I do while we wait").

- Scheduler: `_autoloop_watchdog()` ticks every AUTOLOOP_TICK_S (15s); fires only when NO group run is active.
- Pass = solo group run (cast=[agent], extra {"solo": True}) -> ONE turn, then concluded; journaled,
  stall-guarded, evidence-swept + auto-committed like any run. Visible in chat as an "AUTO-LOOP ..." prompt.
- Priority: queued human UMQ first (oldest wins), else oldest-idle-first. At-100% agents get a maintenance
  sweep only after AUTOLOOP_MAINT_COOLDOWN_S (30 min). Streak cap AUTOLOOP_MAX_STREAK (40) consecutive auto
  passes without human input; any human message/run resets it (autoloop_note_human).
- Idle clock: autoloop_touch(name) on every completed turn (_parallel_turns terminal events); persisted in
  memory/ops/autoloop.json {last_active per agent, streak, last_pass, last_human_ts}. Fresh restart seeds
  with process start time (no burst of passes).
- View: GET /api/autoloop (idle_s + open_goals per agent, streak, paused flag).
