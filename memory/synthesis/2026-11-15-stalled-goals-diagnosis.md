# 2026-11-15 — WHY GOALS STALLED: diagnosis + 4 fixes (round record, no supersession)

Scribe round record for the ~22:2x thread. Every line traces to TODO.md LIVE PLAN lines 1-8 (section `## 2026-11-15 ~22:2x - WHY GOALS STALLED`) and the cited run IDs.

## What was decided / found (one-line rationale each)
- **Two failure modes, not one** (TODO L3, runs g-1a1de52..g-1a1dece 18:30-20:52): (1) Builder+Verifier on Black .99 got empty-body HTTP 400s EVERY pass — the only agent pair sharing that host; (2) context exhaustion — "the model spent the whole of its 32768-token window on reasoning" (Builder Q8_0, Verifier, Archivist): group prompts already ~17k tokens, default thinking ate the rest and returned NO answer.
- **Fatal amplifier** (TODO L3): in `_group_run_worker` any turn with empty content was added to `settled`, so an agent that ERRORED on pass 1 was silently excluded for the whole run while the rest concluded — verdict said "task complete". Builder's own words in-run: "the implementation got lost - likely a truncated round." This is why fleet crept 52->55 while runs kept ending "Concluded."

## Fixes landed (all [x] in TODO L4-L7)
- **FIX 1** — `agent_portal.py stream_chat`: group-mode turns with reasoning="default" now get `FIRST_REPLY_REASONING="low"` (same cap as fast-first path) so thinking+answer fit the window. Verified vs Black: verifier-q4 full portal body -> finish=stop, real content.
- **FIX 2** — `stream_chat _open_upstream`: transient HTTP failures (400/408/425/429/5xx) retry x2 with 10s/20s backoff before surfacing; UMQ confirm still only on success. Black probes at 22:1x: both models OK concurrent, full bodies streaming (Q8_0 >5min/turn - slow but alive).
- **FIX 3** — `_group_run_worker`: errored turns are NO LONGER settled; agent retries next pass; settle only after 3 consecutive error passes. `errored` names tracked from prompt phase too.
- **FIX 4** — verdict honesty: a conclusion while agents were erroring now reads "...task complete. (note: X, Y failed this run - their lane may be incomplete)" with cls=warn instead of a clean ok.

## Still open (owner + next action)
- **VERIFY next run** (TODO L8, owner = whoever runs the next group pass; Builder turn-duration watch): no agent silently dropped after an error; if Black 400s recur, activity log shows `retry` events before any surfaced error; verdict carries the warn note when lanes failed.
- **WEDGE 22:47** (TODO L1, run g-1a1def4): prompt phase hung ~12min after ALL 8 turns completed their frames (5 metas + Builder/Verifier conn errors) — ThreadPoolExecutor exit never returned; no py-spy to capture stacks. `STALL_KILL_S=900` is the safety net. NEXT: add per-turn wall-clock timeout in `_parallel_turns` (e.g. `future.result(timeout=600)`) so one stuck worker can't wedge a pass. **Owner: Builder/Mechanic** (code change to agent_portal.py).

## Contradiction check
- No agent-vs-agent contradiction in this thread. The core tension was verdict-vs-reality ("Concluded" while agents were dropped), which FIX 4 resolves by making the verdict carry a warn note — recorded here rather than silently picking a side.
