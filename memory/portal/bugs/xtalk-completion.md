# Portal bugs — cross-talk, completion signals & agent reply behavior
Last updated: 2026-11-11 (split from memory/portal-bugs.md). Newest first.
## Cast expansion: @delegations reached a dead room (FIXED 2026-11-10)
"@Atlas, delegate the build of a calculator app": L402-403 made cast=MENTIONED ONLY when an @mention exists -> Quinn was outside the cast entirely, so Atlas's "@Quinn, ship it" (twice) went to no one; loop ended on !any after Atlas's empty 3rd reply. Also noted: Q8 self-repetition put the delegation text twice in one bubble (model behavior, not portal).
Fix (index.html): mentionRe() helper; cast is now `let` + inCast Set + expandCast(text) which pushes any @named non-cast agent into it. Called on every non-empty prompt-phase reply AND every non-empty cross-talk reply -> the addressed agent enters next round and sees the full history (the delegation). Prompt phase still scoped to mentioned agents; no-mention prompts unchanged (cast=all).

## ■ Stop button: user closes run as concluded (BUILT 2026-11-10)
"Finished without reaching conclusion": tool-discipline rule WORKED - Atlas actually wrote calculator.html (all 3 fixes on disk), but no [CONCLUDED] was emitted and both agents went empty in the final round -> loop broke on !any -> "NO conclusion" verdict despite task done. Arnold's direction: stop button instead of timing out with turn counters.
index.html (frontend only): ■ Stop in modeBar (red; enabled while any stream busy, via setBusyHint/clearBusyHint busyNames 0<->1). Click: stopRequested=true + lastConcluded=true + aborts every in-flight /api/chat fetch (per-stream AbortController, activeCtrls registry: add before fetch, delete in finally); aborted streams hit new catch branch -> return "" (bubble shows "(no output)"). Cross-talk loop now `while(!stopRequested && guard++<8 && calls<MAX_CALLS)`; lastConcluded=true makes the existing post-loop stamping tag every round bubble ✓concluded and break fire at `if(lastConcluded||!any)`. Verdict: new FIRST branch -> green "■ Stopped by user — round closed as concluded." stopRequested/activeCtrls reset per human prompt (next to noOutputNames.clear() in send()). Semantics: Stop = user authority that the task is complete; [CONCLUDED] stays agent-side signal, XTALK_LIMIT=6/MAX_CALLS stay backstops. Works in solo too (aborts a long generation). No backend change - HARD-REFRESH portal tab.

## Tool-discipline rule: agents CLAIMED builds without tool calls (2026-11-10)
Live group test "build a calculator app" (Arnold screenshot 23:29): the new UI VERIFIED working - dim
"(no output)" bubbles, round-end verdict line ("NO conclusion: Quinn, Atlas produced no output..."),
correct counter 2/6 (empty completions uncounted). But BOTH agents claimed completion (Atlas "Built and
rendered above", Quinn "Built it") with ZERO tool calls -> no file on disk anywhere (host sweep of
C:\Users\White + C:\Projects, last 2h found nothing). Model behavior, not infra: the 27B Q4/Q8 models
narrate the build instead of calling edit_file/python/render_html. Same run: Quinn emitted bare EMPTY
completions in all cross-talk rounds (immediate EOS instead of the [SILENT] token) - now handled gracefully
by the no-output display + verdict line; prompt rule strengthened ("an empty reply is never acceptable").
Fix (agent_portal.py build_system_prompt, applies to solo+group for any agent with tools enabled):
TOOLS discipline block - "When asked to build/create/modify, DO IT with your tools, write real files into
the project workspace; NEVER say 'built'/'rendered'/'done' unless a tool call in THIS reply succeeded;
if a tool fails, say exactly what failed." Prompt is built per request; code change required portal restart
(PID 15720 -> 10628). If narration persists next test: escalate to forced tool_choice or per-agent persona.

## Round-end verdict: [CONCLUDED] = THE completion signal (BUILT 2026-11-10)
Diagnosis of "agents finished their turns without completing the tasks" (user screenshot): NEITHER a counter
reset NOR budget exhaustion. memory.md state line read inter_agent_replies=3/6 with last_reset_by="" — the
cross-talk loop broke on `!any`: in the final round BOTH agents emitted zero-token completions (invisible
blank bubbles), and Atlas's actual work had already died one round earlier: Studio truncated his tool calls
("The model stopped before completing its tool calls. These tool calls were not run."), so his promised fix
was never executed — and nothing in the UI flagged an incomplete task.
Fixes (frontend only, index.html):
- Empty completion -> dim "— (no output) —" in the bubble (blank bubbles no longer hide who went quiet); name
  recorded in module-level `noOutputNames` Set (cleared per human prompt). Still counts as "nothing new"
  (settled), same as silence.
- Studio truncation note (regex /stopped before completing its tool calls/i on final text) -> amber chip
  "⚠ tool calls truncated - task incomplete" (.warnchip) on that bubble's .who row.
- send() appends a ROUND-END VERDICT line after the loop: green "✓ Concluded — task complete." on [CONCLUDED];
  amber "⏸ budget exhausted (n/6) with NO conclusion — say 'counter reset'…"; amber "⚠ … truncated tool calls
  — the task is incomplete."; dim "— … produced no output. Task state unconfirmed…"; NOTHING when all agents
  settled quietly (no noise on normal endings).
- Counter semantics UNCHANGED: shared budget XTALK_LIMIT=6 per human prompt, auto-reset by backend stream_chat
  on every new prompt, manual reset via "counter reset" phrase / ↺ Reset button. [CONCLUDED] does not need to
  reset it — the next prompt zeroes it anyway.
esprima: both script blocks clean (only known ES2020 ?. / ?? flags). User must HARD-REFRESH the portal tab.

## [DONE] early-return killed silent-merge + concluded chip (FIXED 2026-11-10)
Symptom: runs of separate full-size "[SILENT]" bubbles at the end of group rounds (user screenshot), and no green
"concluded" chips even though both features were "verified". The merge code existed but never executed.
Root cause: index.html streamReply() - `if(p==="[DONE]")return full;` sat INSIDE the frame-parsing loop, so on
[DONE] the function returned before reaching the post-processing block (silent -> shared pill merge,
concluded -> chip). Dead code. Side effect: "[SILENT]" came back as a truthy reply, send() pushed it to history
and set any=true, so the cross-talk while-loop re-prompted both agents every round until MAX_CALLS=12 (the backend
counter does NOT increment on silences, so the budget never ran out either).
Fix: [DONE] now sets a stop flag that breaks the read loop; post-processing runs as designed. All [SILENT]s of a
prompt merge into ONE pill ("Quinn, Atlas stayed silent"), silent agents are marked settled (no re-prompt),
concluded stamps its chip and ends the round.

## Conversation satisfaction determination (ADDED 2026-11-10)
Problem: fixed budget of 3 cut debates off mid-conclusion (screenshot: Atlas conceded, Quinn never got to confirm).
Fix - two-tier termination, model-declared satisfaction:
- [CONCLUDED] marker: cross-talk rule tells agents that when the discussion reaches a natural conclusion
  (agreement, or positions fully stated) they start their reply with [CONCLUDED] + ONE summary sentence.
  Server _effective_reply parses it -> meta.concluded=true; frontend strips the marker, shows a green
  "\u2713 concluded" chip, and BREAKS the whole cross-talk loop (send(): if(lastConcluded)break).
- [SILENT] keeps its old meaning: "I have nothing more, but others may continue" -> settled set skips that agent.
- XTALK_LIMIT raised 3 -> 6 as BACKSTOP only (settled-set + any=false + guard<8 + MAX_CALLS=12 remain as caps).
- Concluded replies count toward the counter; marker honored in cross-talk kind only (prompt phase ignores it).

## Phase-aware group rules (ADDED 2026-11-10)
Problem: silence-first rules applied to EVERY call -> on a plain greeting all agents except the first went [SILENT]
(Quinn never spoke). Fix: build_system_prompt takes kind=. prompt phase = "human message is for the WHOLE group,
give your own brief response, do NOT [SILENT] just because another agent already replied"; cross-talk phase keeps
silence-first rules. _ack_nudge also fires in prompt phase when the HUMAN names the agent.

## Agent-to-agent acks (ADDED 2026-11-10)
Before: acks were pure model judgment in the cross-talk pass -> agents usually only answered the human.
Now deterministic: backend _ack_nudge scans messages since the last human turn for this agent's name
(regex \bName\b, case-insensitive). If another agent named them, their cross-talk system prompt gets
"NOTE: X addressed you by name - respond briefly unless [SILENT]". Group rules also say: MUST respond
when named or directly asked; otherwise [SILENT]. Budget: 6 per prompt (backstop; see satisfaction section).

## [SILENT] infinite loop (FIXED 2026-11-10)
Symptom: group "Introduce yourselves" -> endless visible [SILENT] bubbles, header stuck 0/3.
Root cause: (1) stale tab JS (index.html is re-read per load; hard refresh required after edits);
(2) dual-regex silence detection that could disagree; loop re-prompted silent agents until guard=16.
Fix: backend _finish_chat ALWAYS emits a meta frame with an authoritative `silent` flag (+counter if not).
Frontend streamReply trusts o.meta.silent (removes bubble, returns "") else hardened isSilent fallback.
Cross-talk marks [SILENT] agents "settled" (not re-prompted this turn); caps guard<8 / MAX_CALLS=12;
silent replies never pushed to history. Verified terminating in all simulated modes.

## Group-mode empty bubble (FIXED 2026-11-09)
Other agents' replies were injected as `assistant` role -> a foreign final assistant turn -> model emitted nothing.
Fix in to_openai_messages: own past replies = assistant; OTHER agents' words = user-role with "[Name]: " prefix.
Proof scripts: probe_quinn.py / test_group.py.

## Counter mechanics
- State line `<!-- state: {...} -->` at the top of memory.md is the single source of truth (regex _STATE_RE).
- _write_memory re-renders the "## Counter" section; keep that exact heading + "- " bullet format intact.
- POST /api/memory {"action":"reset"} -> 0/6 (limit is XTALK_LIMIT=6). Called by the "↺ Reset"
  button only; per-prompt auto-reset happens in backend stream_chat, not from the frontend.
- A member saying "counter reset" in a reply also resets, recording last_reset_by.
- Under parallel streams the bump is atomic (RLock + _bump_counter); concurrent meta frames may
  arrive out of order -> the frontend counter display uses a high-water mark.


## Auto-continue on round end (BUILT 2026-11-12 ~21:4x, LIVE-VERIFIED 11-13)
Stuck-run fix: group runs stalled on the MAX_CALLS=12 hard cap, not a timeout - pass 1 could leave an agent mid-sentence with no [CONCLUDED], and without auto-continue the UI would show "✓ Concluded" anyway. index.html pass loop now continues un-concluded passes up to 3 nudges: `↻ AUTO-CONTINUE n/3` bubble, fresh agent-to-agent budget each pass (portal resets on /api/chat), all-silent = natural end; when the limit is spent the verdict leads "⚠ Auto-continue limit reached". MAX_CALLS bumped 12→16. LIVE 11-13 12:39: bubble fired on a real group run, honest ✓ Concluded verdict followed (combined DM live test).
