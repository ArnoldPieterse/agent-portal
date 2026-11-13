# Portal bugs — frontend UI fixes
Last updated: 2026-11-11 (split from memory/portal-bugs.md). Newest first.
## Reset mechanism (ADDED 2026-11-10)
One "↺ Reset" button in the modeBar (Solo + Group). onclick (index.html L403-411):
- guard: if busy -> alert, no reset while a reply is streaming; confirm() dialog before acting.
- POST /api/memory {action:"reset"} -> backend zeroes inter_agent_replies + last_reset_by in the
  memory.md state line (agent_portal.py do_POST L593-602); response carries limit for the UI.
- resetChat() clears client history + bubbles; setXtalk() refreshes the "n/6" display.
Counter lifecycle: backend stream_chat auto-zeroes on every NEW human group prompt (L356-362) -
that is the normal per-prompt reset, NOT a frontend call. The button is for manual mid-session
resets; an agent saying the RESET_PHRASE also zeroes it with last_reset_by (L473-475).
Verified 2026-11-10: esprima parse of both index.html script blocks clean (only ES2020 ?. / ??
tokens flagged by the python port); endpoint round-trip 200, state line on disk zeroed,
bad action -> 400. Visual pass pending user opening the portal tab in the browser panel.

## Shared thinking bubble crash (FIXED 2026-11-10)
Symptom: group mode - each agent's FIRST thinking chunk crashed streamReply (TypeError reading `.tb`
of a DOM div), killing that agent's reply stream; the shared thinking bubble never rendered.
Root cause: index.html L252-260. `let sec=thinkTarget.secs[agent.id]` is undefined for a new agent, so the
if-block reassigned `sec` to the freshly built `<div class="tsec">`; but L260 does `sec.tb.textContent+=...`
and only the STORED object `{tb:tb2}` has `.tb`. First chunk per agent always crashed.
Fix: build the div under a separate name (`sd`) and keep/append via the stored object:
`sec={tb:tb2}; thinkTarget.secs[agent.id]=sec; ... sec.tb.textContent+=o.thinking` (index.html L253-260).
Found while verifying TODO item 5 - the crash WAS the verification failure.

