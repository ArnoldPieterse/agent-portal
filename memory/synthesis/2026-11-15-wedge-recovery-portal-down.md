# 2026-11-15 — Wedge recovery fixes landed, then unplanned portal-down blocks verification

Round record (no supersession). Every bullet traces to a named source. Scribe.

## What was decided / done (WEDGE RECOVERY + STUCK-RUN FIXES ~18:25)
- Root cause of "all agents stuck / 0 progress": Q4 (quinn-q4) request queue wedged at ~17:52 — SECOND occurrence; probe timeout + cancel returned cancelled:0. Portal run `g-1a1de312535-a23478` frozen; `/api/run-stop` could not drain it. [source: TODO.md LIVE PLAN, WEDGE RECOVERY line 1]
- Recovery action: killed portal PID **28984**; Q8 left alone (probe 0.4s healthy); Q4 force-reload scheduled via schtask `\WedgeQ4Recover` @18:27 with `force_cancel=True` (Studio 409s on active_generations otherwise — this chat's own thread counts as active). [source: TODO.md line 2]
- Code fix (agent_portal.py): `_parallel_turns` is now **SEQUENTIAL** (Studio serializes globally anyway; parallel fire = everyone queued behind one slot, no visible progress); journal events carry `ts`; `RUN_MAX_EVENTS` 4000 -> 30000. [source: TODO.md line 3]
- Code fix (index.html): Send is **NEVER disabled** while busy — relabels to "Queue" and routes via `user_messages.json`; stall watchdog polls `/api/run-state` (stalled flag = no frames >240s) and warns in the busy hint. [source: TODO.md line 4]

## Still open — now BLOCKED
- VERIFY after 18:30: `recover_force_result.json` post-probe quinn-q4 ok + `trigger_group_run.log` shows group-run POST 200 (fresh run auto-picked-up; old run marked interrupted w/ verdict). [source: TODO.md line 5, unchecked]
- Watch first sequential pass: each agent completes visibly one-by-one; if any single agent hangs the stall banner appears after ~4 min (sequential = no parallel fault isolation yet — per-turn timeout considered for next round). [source: TODO.md line 6, unchecked]
- **Blocker:** portal :8099 is DOWN since ~18:25 (unplanned), so neither VERIFY item can be executed from an agent seat until the portal is restored. Mirror propagation also stalled while down; each seat sees divergent file states — treat local disk as unreliable until restore. [source: MEMORY.md Hot Notes, lines "Portal :8099 DOWN since ~18:25" + "Mirror propagation stalled"]

## Contradictions / flags
- No new agent-vs-agent factual contradiction this round.
- Recurring known issue (NOT a fresh contradiction): mirror sync repeatedly overwrites local edits (TODO.md, INDEX, index.html) and Designer's WCAG `--acc-strong` token; pattern confirmed 3x, all seats proven sandbox-isolated. Scribe's writes to memory/ remain clobber-at-risk until the mtime-guard fix lands — White stays canonical. [source: MEMORY.md Hot Notes]

## Owner of next action
- Portal restore (Mechanic / portal lifecycle runbook) is the gating step; once :8099 is back, re-run the two VERIFY items and confirm the first sequential pass. Scribe to append a closeout line here when verification evidence lands.
