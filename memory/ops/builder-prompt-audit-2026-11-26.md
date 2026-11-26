# Builder.txt prompt-injection audit (2026-11-26)

## 1. Where the prompt is injected
- `C:\Projects\AgentPortal\_ap_test.py`: 7 markers
- `C:\Projects\AgentPortal\agent_portal.py`: 9 markers
- `C:\Projects\AgentPortal\agent_portal_test.py`: 9 markers
- `C:\Projects\AgentPortal\archive\orphaned_20261117\_gen_report2.py`: 1 markers
- `C:\Projects\AgentPortal\archive\orphaned_20261117\_probe_goals.py`: 1 markers
- `C:\Projects\AgentPortal\portal\group_run.py`: 3 markers
- `C:\Projects\AgentPortal\recover_seats.py`: 1 markers
- `C:\Projects\AgentPortal\studio_exec_7cao4dtp.py`: 9 markers

## 2. Exact injection lines (line numbers)
- L4368: reset_note = ("\n\n[GOAL CYCLE COMPLETE - 100% REACHED FOR ALL AGENTS] This run MUST begin "
- L4426: full_text = ("\nGOAL-SETTING ROUND (new cycle) - the previous goal set is 100% complete. "
- L4445: full_text += ("\n\n[SHELL] Shell is not elevated, but admin commands DO work via the helper: run "
- L4474: _note = "\n\n[MODEL LOAD STATUS]"
- L4640: prompt = ("\u21bb AUTO-RESUME %d/%d (backend watchdog): the previous group run was %s. "
- L4781: return ("BEHAVIOUR: your last pass left remaining work - continue from there, do NOT redo it: %s"
- L4787: return ("BEHAVIOUR: you reported a blocker last pass (%s) - take ONE step that does NOT depend "
- L4791: return ("BEHAVIOUR: your last auto-loop pass ended WITHOUT [CONCLUDED] - first finish whatever "
- L5010: body = ("Work your oldest open goal TO COMPLETION this pass. Your open goals:\n%s"
- L5024: body = ("your goals are 100% reached - contribute to the team while you wait - " + _generic_menu)
- L5042: prompt = ("AUTO-LOOP (batch pass, %d agents in parallel) - you have been idle. Work ONLY "

## 3. Transcript anatomy (the pasted Builder.txt)
file=C:\Projects\AgentPortal\.unsloth_attachments\f7b004ded926\🛠️ Builder.txt bytes=450559
- AUTO-LOOP (batch pass headers: 48
- [SHELL] blocks: 69
- [MODEL LOAD STATUS] blocks: 52
- GOAL-SETTING ROUND injections: 16
- GOAL CYCLE COMPLETE banners: 16
- AUTO-RESUME banners: 4
- @agent idle sections: 205
- BEHAVIOUR injections: 52
- [CONCLUDED] replies: 289
- [SILENT] replies: 128
- boilerplate bytes: autoloop_hdr=8016 shell=53806 modelload=72779 goalset=10832 cyclecomplete=5648## 4. Prompt assembly code (extracted)

### start_group_run (L4847-5026)
4847: def start_group_run(text, extra=None):
4848:     """Create + launch a backend-owned group run. Returns (run, error).
4849:     `extra` is merged into the run record BEFORE the first save (e.g. the auto-resume budget)."""
4852:         if _active_run_id:
4854:             # The caller gets a queue receipt (position + depth); 'at-capacity' deferral
4856:             wi, qerr = _aq.enqueue(text, extra)
4857:             if qerr:
4858:                 return None, "a group run is already in progress (%s) and the queue is %s (cap %d)" % (
4860:             return {"queued": True, "id": wi["id"], "position": wi["position"],
4861:                     "depth": wi["depth"], "maxCapacity": wi["maxCapacity"], "cast": []}, None
4862:         agents = load_agents()["agents"]
4863:         names = [a.get("name", "") for a in agents]
4864:         mentioned = [n for n in names if re.search(r"@" + re.escape(n), text or "", re.I)]
4865:         # Goal-cycle upgrade (2026-11-15): when every agent's goals are 100% reached, the
4870:         # GOAL_RESET_PENDING.json to 0 bytes via open("w") and left the flag corrupted).
4871:         rid = "g-%x-%s" % (int(time.time() * 1000), os.urandom(3).hex())
4872:         reset_note = ""
4874:             _gf = os.path.join(HERE, "memory", "goals", "GOAL_RESET_PENDING.json")
4875:             with open(_gf, encoding="utf-8") as _f:
4876:                 if json.load(_f).get("armed"):
4877:                     reset_note = ("\n\n[GOAL CYCLE COMPLETE - 100% REACHED FOR ALL AGENTS] This run MUST begin "
4878:                                   "with a NEW GOAL-SETTING round: Orchestrator chairs; each agent proposes ~10 new "
4879:                                   "goals for the next cycle; collect them verbatim into TODO.md '## AGENT GOALS' and "
4880:                                   "memory/goals/<name>.md (move old files to memory/goals/archive/ first). Old goal "
4881:                                   "files are replaced, not appended to.")
4882:                     _rec = json.dumps({"armed": False,
4883:                                        "consumed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
4884:                                        "run_id": rid})   # serialize BEFORE truncating the file
4885:                     with open(_gf, "w", encoding="utf-8") as _f:
4889:         if reset_note:
4895:                 _q = _rt.get("queue") or []
4896:                 if _q:
4898:                     if _rt.get("current") and (_rt["current"] or {}).get("topic"):
4899:                         _rt.setdefault("past", []).append(_rt["current"]["topic"][:120])
4900:                         _rt["past"] = _rt["past"][-10:]
4901:                     _rt["current"] = {"topic": (_nxt.get("topic") or "").strip()[:200],
4902:                                       "description": (_nxt.get("description") or "").strip()[:1200],
4903:                                       "set_at": time.strftime("%Y-%m-%d %H:%M:%S"),
4904:                                       "source": "user-queue"}
4906:                     reset_note += ("\n\n[ROUND TOPIC - USER QUEUED] This goal-setting round's focus: \"%s\". %s "
4907:                                    "Every agent's new goals MUST serve this topic - each goal traceable to it."
4908:                                    % ((_nxt.get("topic") or "").strip(), (_nxt.get("description") or "").strip()))
4910:                     _past = [t for t in (_rt.get("past") or []) if t]
4911:                     reset_note += ("\n\n[ROUND TOPIC] No user-queued topic this round. Orchestrator: BEFORE goals are "
4912:                                    "drafted, set this round's focus - a short topic + 2-3 sentence paragraph describing "
4913:                                    "the collection of goals for the round - by writing memory/goals/round_topic.json as "
4914:                                    "{\"current\": {\"topic\": \"...\", \"description\": \"...\"}} (move the previous topic into "
4915:                                    "\"past\"). Do NOT reuse a recent topic"
4916:                                    + ((" (recent: %s)" % ", ".join(_past[-5:])) if _past else "") + ".")
4918:                 if _closed:
4919:                     reset_note += ("\n\n[ANTI-REPEAT] These goals were already completed in earlier rounds - do NOT "
4920:                                    "re-set them verbatim or near-verbatim (if genuinely needed again, cite the prior "
4921:                                    "evidence pointer instead):\n" + "\n".join("- " + c for c in _closed))
4925:         if reset_note:
4927:             # CONSUMING this flag and merely appending the note to a partial-cast "work your open
4928:             # goals" prompt - the Orchestrator often wasn't even in the cast, so the new goal round
4931:             # chair prompt replaces the pass text); human-sent runs keep their text but still get
4934:             if (extra or {}).get("autoloop_why") or (extra or {}).get("auto_resume_count"):
4935:                 full_text = ("\nGOAL-SETTING ROUND (new cycle) - the previous goal set is 100% complete. "
4936:                              "This run's ONLY job is to produce the NEXT cycle's goals; do NOT work "
4937:                              "old-cycle goals - they are done and get archived by the Orchestrator. "
4938:                              "Orchestrator: CHAIR this round - open it, state the ROUND TOPIC first "
4939:                              "(see below), then collect every agent's ~10 proposed goals VERBATIM into "
4940:                              "TODO.md '## AGENT GOALS' and memory/goals/<name>.md (move each old file to "
4941:                              "memory/goals/archive/ as you go). Every other agent: propose your ~10 NEW "
4942:                              "goals for the next cycle NOW, in this run - each traceable to the round "
4943:                              "topic, none from the [ANTI-REPEAT] list. Reply [CONCLUDED] only after your "
4944:                              "new goal file is written." + reset_note)
4946:                 full_text = (text or "") + reset_note
4948:             full_text = text or ""
4949:         # 2026-11-17: admin is the DEFAULT for every agent (user directive). When this shell is
4953:             if not _shell_elevated():
4954:                 full_text += ("\n\n[SHELL] Shell is not elevated, but admin commands DO work via the helper: run "
4955:                               "`python elev.py <cmd...>` or `python elev.py --shell \"cmd string\"` (auto-escalates to SYSTEM). "
4956:                               "Admin is the default for all agents - never treat elevation as a blocker. "
4957:                               "Only if elev.py exits 5 (helper down) log NEEDS-HUMAN in memory/ops/blockers.md once, then move on.")
4970:             for n, s in _mls.items():
4971:                 if s.get("status") == "ok":
4978:                 if _sx and _sx["base"] != _studio_base(_agx):
4979:                     _relocated[n] = "%s (home %s)" % (_sx.get("host"), s.get("status"))
4982:             if _missing or _relocated:
4983:                 _note = "\n\n[MODEL LOAD STATUS]"
4984:                 if _relocated:
4985:                     _note += (" Relocated - home model down, running on another host, treat as NORMAL seats: " +
4986:                               ", ".join("%s -> %s" % (n, v) for n, v in sorted(_relocated.items())) + ".")
4987:                 if _missing:
4988:                     _note += (" Seats NOT ready anywhere at run start: " +
4989:                               ", ".join("%s=%s" % (n, s["status"]) for n, s in sorted(_missing.items())) +
4990:                               ". Do not wait for or cross-talk with these seats this round; their lanes are "
4991:                               "covered by the seat-drafted goals (memory/goals/).")
4992:                 full_text += _note
4994:                     with open(os.path.join(HERE, "memory", "ops", "model-load.jsonl"), "a", encoding="utf-8") as _f:
4995:                         _f.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "run": rid,
4996:                                              "missing": {n: s.get("status") for n, s in _missing.items()},
4997:                                              "relocated": _relocated}) + "\n")
5000:             if MODEL_LOAD_BLOCK and _missing:
5001:                 return None, ("blocked: model not loaded/unreachable for " + ", ".join(sorted(_missing)))
5004:         hist = _load_history("group")
5005:         run = {"id": rid, "status": "running", "prompt": full_text[:4000],
5006:                "cast": (_goal_round_cast or (extra or {}).get("cast_override") or mentioned or names),
5007:                "settled": [], "nudges": 0, "phase": "prompt",
5008:                "started": time.time(), "ended": None, "verdict": None, "error": None,
5009:                "hist_start": len(hist)}
5010:         if _mls is not None:
5011:             run["model_load"] = _mls
5012:         if extra:
5015:         _append_history("group", [{"speaker": "You", "content": full_text}])
5018:     _run_event(rid, {"run": "start", "prompt": full_text[:4000]})
5019:     _save_run_state({"busy": True, "mode": "group", "phase": "prompt",
5020:                      "ts": int(time.time() * 1000), "run_id": rid})
5026: def _agent_goals_block(name):

### _agent_goals_block (L5026-5085)
5026: def _agent_goals_block(name):
5027:     """One short nudge per agent: its own open goals from memory/goals/<slug>.md, so group
5032:     (verified:)/(pointer:) marker on the goal line does."""
5034:         path = os.path.join(HERE, "memory", "goals", name.lower() + ".md")
5037:             for g in _goal_ledger_mod().parse_agent_file(path):
5038:                 if g["status"] == "reached":
5041:                 it = g["text"].replace("\n", " ")
5042:                 items.append(it[:160])
5043:                 if len(items) >= 5:
5046:             with open(path, encoding="utf-8") as f:      # ledger import failed - naive fallback
5047:                 for ln in f.read(8000).splitlines():
5048:                     m = re.match(r"^\s*(?:\d+[.)]\s+|[-*]\s*\[ \]\s*)(.*)", ln)
5049:                     if not m or "(verified:" in ln:
5052:                     if it and len(it) >= 12:
5053:                         items.append(it[:160])
5054:                         if len(items) >= 5:
5056:         items_txt = ("\n".join(items) if items else "(none open - you are at 100%; assist other agents' open goals)")
5057:         base = ("YOUR OPEN GOALS (memory/goals/%s.md, %d/10 reached - make progress on these):\n%s"
5059:         base += ("\nCLOSURE PROCEDURE (chat claims do NOT count): when a goal's acceptance test passes, run "
5060:                  "`python memory/researcher/goal_ledger.py --record %s <goal#> --note '<what ran + artifact path>'` - "
5061:                  "it appends the (verified:) marker the dashboard counts. Or write an evidence leaf in memory/%s/ "
5062:                  "AND add a line to that lane's INDEX.md - the end-of-run sweep auto-links it." % (name.lower(), name.lower()))
5063:         base += ("\nTEAM RULES: (1) You may ASSIST another agent's open goal when you can unblock it - "
5064:                  "coordinate in cross-talk and credit the original owner in the evidence note. "
5065:                  "(2) ANTI-LOOP: if your last two turns produced no new file change, measurement or evidence, "
5066:                  "stop re-verifying and take ONE concrete next step (or hand off / assist). "
5067:                  "(3) ANTI-REPEAT: never re-issue a goal already in your file or closed in an earlier round "
5068:                  "(memory/goals/closed_topics.json); new work must be genuinely new.")
5070:             _rt = (_load_round_topic().get("current") or {})
5071:             if _rt.get("topic"):
5072:                 base += ("\nROUND TOPIC (this cycle's focus - new work should serve it): %s"
5073:                          % str(_rt["topic"])[:140])
5078:         return ""
5085: def _stall_killer(run_id):

### open-goals+behaviour-hint (L5231-5306)
5231: def _agent_open_goals(name, limit=5):
5232:     """One-line-per-open-goal list for pass prompts (2026-11-23): skips the ~minute of
5234:     re-reasoning about what state things are in."""
5236:         path = os.path.join(HERE, "memory", "goals", name.lower() + ".md")
5237:         items = [g for g in _goal_ledger_mod().parse_agent_file(path) if g["status"] != "reached"]
5238:         return [("%d. %s" % (i + 1, str(g.get("text") or "").strip()[:200])) for i, g in enumerate(items[:limit])]
5243: def _agent_open_goal_count(name):
5245:         path = os.path.join(HERE, "memory", "goals", name.lower() + ".md")
5246:         return sum(1 for g in _goal_ledger_mod().parse_agent_file(path) if g["status"] != "reached")
5251: def _autoloop_behaviour_hint(name):
5252:     """Behaviour analysis (2026-11-17): read this agent's LAST substantive group-chat reply and
5253:     derive a one-line context for its next auto-loop task, so the batch pass continues where the
5255:     Signals, in priority order: (1) remaining-work lines ('Remaining open: ...', 'next step: ...')
5256:     -> continue, don't redo; (2) blocker claims (unreachable / blocked by / powered off / must run
5257:     on X) -> work AROUND it, don't re-probe the same wall; (3) an auto-loop pass that ended WITHOUT
5258:     [CONCLUDED] -> finish the in-flight work first. [SILENT]-only tails are ignored."""
5260:         hist = _load_history("group")
5262:         return ""
5263:     last_text, last_concluded, was_autoloop = None, False, False
5264:     for m in reversed(hist):
5265:         who = (m.get("speaker") or "").strip().lower()
5266:         content = (m.get("content") or "").strip()
5267:         if not content:
5269:         if who == "you":
5270:             if last_text is None:   # the human message immediately before this agent's reply
5271:                 was_autoloop = content.lower().startswith("auto-loop")
5273:         if who != name.lower():
5276:         if is_silent:
5278:         last_text = content
5280:         last_concluded = concluded or "[concluded]" in content.lower()
5282:     if not last_text:
5283:         return ""
5284:     tail = last_text[-1400:]
5285:     # a real remaining-work line is 'Remaining open: ...' / 'Next step (...): ...' - keyword
5286:     # followed by a colon; narration like 'styles remain. Now I need...' has no colon and must not match
5287:     mrem = re.search(r"\b(remaining|next step|still open)\s+[(a-z) ]{0,20}:[^\n]{0,160}", tail, re.I)
5288:     if mrem:
5289:         frag = mrem.group(0).replace("**", "").strip()[:200]
5290:         return ("BEHAVIOUR: your last pass left remaining work - continue from there, do NOT redo it: %s"
5292:     mblk = re.search(r"[^\n]*(blocked by|unreachable|can'?t be started|must run on|powered off)[^\n]*",
5294:     if mblk:
5295:         frag = mblk.group(0).strip(" *#-").replace("**", "")[:160]
5296:         return ("BEHAVIOUR: you reported a blocker last pass (%s) - take ONE step that does NOT depend "
5297:                 "on it (another open goal, evidence/ledger upkeep, or assist another agent's lane); do "
5298:                 "not re-probe the same wall.") % frag
5299:     if was_autoloop and not last_concluded:
5300:         return ("BEHAVIOUR: your last auto-loop pass ended WITHOUT [CONCLUDED] - first finish whatever "
5301:                 "was in flight (check your evidence/ledger state), then take one more step on your "
5302:                 "oldest open goal.")
5303:     return ""
5306: def _autoloop_state():

### _autoloop_watchdog (L5332-5569)
5332: def _autoloop_watchdog():
5333:     """One scheduler tick every AUTOLOOP_TICK_S: when NO group run is active, ALL idle agents are
5337:     excluded from the batch (their lanes stay covered by seat-drafted goals)."""
5340:         if not _portal_live or _active_run_id:
5345:                 la = {k: float(v) for k, v in (d.get("last_active") or {}).items()}
5346:                 la.update({k: float(v) for k, v in _agent_last_active.items()})
5348:             names = [a.get("name", "") for a in load_agents()["agents"] if a.get("name")]
5349:             for n in names:
5351:             idle = [n for n in names if now - la[n] >= AUTOLOOP_IDLE_S]
5352:             if not idle:
5357:             # them for everyone else).
5364:             # fired, their turns hung tokenless for 20+ min and stretched every pass until a human stopped
5366:             ready = [n for n in idle if mls.get(n, {}).get("status") == "ok"]
5369:             for n in idle:
5370:                 if n in ready:
5375:                     if _s and _s["base"] != _studio_base(_ag):
5376:                         ready.append(n)
5389:             down = [n for n in idle if mls.get(n, {}).get('status') not in (None, 'ok')]
5390:             streaks = d.setdefault('down_streak', {})
5391:             busy_ticks = d.setdefault('busy_ticks', {})
5392:             for _n in list(streaks):
5393:                 if _n not in down:
5395:             for _n in list(busy_ticks):
5396:                 if _n not in down:
5398:             episodes = d.setdefault('down_episode', {})   # name -> {"since","reloads","last_reload","reboots","notified"}
5399:             for _n in down:
5400:                 _st = mls.get(_n, {}).get('status')
5402:                 if _st != 'ok' and _seat_busy(_agx):
5406:                     if busy_ticks[_n] >= 120:
5407:                         epb = episodes.setdefault(_n, {"since": now, "reloads": 0, "last_reload": 0.0})
5408:                         if epb["reloads"] >= 3 and now - epb.get("last_reload", 0) >= 1800:   # RE-ARM (2026-11-22)
5410:                         if epb["reloads"] < 3 and now - epb["last_reload"] >= 600:
5411:                             epb["reloads"] += 1
5412:                             epb["last_reload"] = now
5413:                             _recover_seat_async(_n, _agx, 'wedged')
5414:                         if now - epb.get("since", now) >= 2700 and epb.get("reboots", 0) < 1:
5419:                             if _ip:
5420:                                 epb["reboots"] = 1
5422:                                 def _rbw(ip=_ip, n=_n):
5425:                                         print('[autoloop] reboot %s (%s): %s - %s' % (n, ip, 'OK' if okk else 'FAIL', det[:80]))
5427:                                         print('[autoloop] reboot %s failed: %s' % (n, str(e)[:80]))
5431:                 ep = episodes.setdefault(_n, {"since": now, "reloads": 0, "last_reload": 0.0})
5434:                 if ep["reloads"] >= 4 and now - ep.get("last_reload", 0) >= 1800:
5436:                 if _st == 'not_loaded' and streaks[_n] >= 4 and ep["reloads"] < 4 and now - ep["last_reload"] >= 300:
5437:                     ep["reloads"] += 1
5438:                     ep["last_reload"] = now
5439:                     _recover_seat_async(_n, _agx, 'load')
5440:                 elif streaks[_n] >= 8 and ep["reloads"] < 3 and now - ep["last_reload"] >= 300:
5441:                     if _host_alive(_agx) or not _remote_host_ip(_agx):
5443:                         ep["reloads"] += 1
5444:                         ep["last_reload"] = now
5445:                         _recover_seat_async(_n, _agx, 'reload')
5446:                     elif streaks[_n] >= 60 and ep.get("reboots", 0) < 1:
5450:                         ep["reboots"] = 1
5451:                         ep["last_reload"] = now
5453:                         def _rb(ip=_ip, n=_n):
5456:                                 print('[autoloop] reboot %s (%s): %s - %s' % (n, ip, 'OK' if okk else 'FAIL', det[:80]))
5458:                                 print('[autoloop] reboot %s failed: %s' % (n, str(e)[:80]))
5462:                 if _st not in (None, 'ok') and streaks[_n] >= 180 and ep["reloads"] >= 3 and ep.get("reboots", 0) < 1:
5464:                     if _ip:
5465:                         ep["reboots"] = 1
5467:                         def _rbw2(ip=_ip, n=_n):
5470:                                 print('[autoloop] reboot %s (%s): %s - %s' % (n, ip, 'OK' if okk else 'FAIL', det[:80]))
5472:                                 print('[autoloop] reboot %s failed: %s' % (n, str(e)[:80]))
5474:                 if streaks[_n] >= 180 and not ep.get('notified'):   # ~45 min: whole chain exhausted
5475:                     ep['notified'] = True
5477:                         with open(os.path.join(HERE, 'memory', 'ops', 'blockers.md'), 'a', encoding='utf-8') as _bf:
5478:                             _bf.write('- [%s] OPS-NOTE (auto-retry continues, no human step required): seat %s down ~%d min (%s) - auto-reload x%d + reboot x%d 
5479:                                       % (time.strftime('%H:%M'), _n, streaks[_n] * AUTOLOOP_TICK_S // 60, _st, ep.get('reloads', 0), ep.get('reboots', 0)))
5484:                 _ds = os.path.join(HERE, 'memory', 'ops', 'down-seats.json')
5485:                 if down:
5486:                     with open(_ds, 'w', encoding='utf-8') as _f:
5487:                         json.dump({"ts": time.strftime('%Y-%m-%dT%H:%M:%S'),
5488:                                    "seats": [{"seat": _n, "status": mls.get(_n, {}).get('status'),
5489:                                               "down_ticks": streaks.get(_n, busy_ticks.get(_n, 0)),
5490:                                               "reload_attempts": episodes.get(_n, {}).get('reloads', 0),
5491:                                               "reboots": episodes.get(_n, {}).get('reboots', 0)} for _n in down]}, _f)
5492:                 elif os.path.exists(_ds):
5497:             for n in ready:   # per-agent task, steered by behaviour analysis of their last reply
5505:                 if pend:
5507:                     why_bits.append("%s:queued-msg" % n.lower())
5508:                     body = ("a queued human message is waiting and will be injected below - handle it "
5509:                             "FIRST, then take ONE concrete step on your open goals.")
5510:                 elif og > 0:
5512:                     why_bits.append("%s:%d-open" % (n.lower(), og))
5514:                     goal_list = ("\n".join(glines) + "\n") if glines else ""
5516:                     # "ONE step" per pass meant a goal needing N steps took N x (pass time + idle
5517:                     # gap); a single LLM iterates to done inside ONE turn - that's why it outpaced
5518:                     # the whole fleet. Pass cap (PASS_TIMEOUT_S) is the backstop for long work.
5519:                     body = ("Work your oldest open goal TO COMPLETION this pass. Your open goals:\n%s"
5520:                             "Iterate tool calls (terminal/python/edit_file) until its verification criteria are "
5521:                             "genuinely met, then mark it reached in memory/goals/%s.md with a timestamped evidence line. "
5522:                             "If budget remains, take the next-oldest open goal and do the same. Keep reasoning terse - "
5523:                             "act, don't deliberate. Reply [CONCLUDED] when you have reached a goal or hit a hard blocker "
5524:                             "(record blockers once in memory/ops/blockers.md)." % (goal_list, n.lower()))
5525:                 elif now - la[n] >= AUTOLOOP_MAINT_COOLDOWN_S:
5526:                     why_bits.append("%s:maint" % n.lower())
5527:                     _generic_menu = "pick ONE of: (a) write a prediction/forecast for another agent's open goal into memory/goals/, (b) draft a solution or work
5530:                     if rot and fm in ("MAINTENANCE", "IDLE"):
5531:                         body = ("your goals are 100% reached and the fleet is in %s mode - do this ONE role-specific maintenance task (rotated daily): %s. Compl
5533:                         body = ("your goals are 100% reached - contribute to the team while you wait - " + _generic_menu)
5535:                     continue   # at 100% inside maintenance cooldown - no task for this seat yet
5536:                 sections.append((n, "@%s (idle %d s): %s%s" % (
5537:                     n, idle_s, body, (" " + hint) if hint else "")))
5538:             if not sections:
5544:             # paused the loop for hours while Designer/Scribe/Mechanic still held 9 open goals.)
5545:             if not productive and int(d.get("streak", 0)) >= AUTOLOOP_MAX_STREAK:
5546:                 continue   # maintenance budget spent - wait for human input (autoloop_note_human resets)
5549:             batch = [n for n, _ in sections]
5550:             why = ", ".join(why_bits)
5551:             prompt = ("AUTO-LOOP (batch pass, %d agents in parallel) - you have been idle. Work ONLY "
5552:                       "YOUR section below; the other sections are for the other seats and need no reply "
5553:                       "from you. Record evidence via the ledger as you go, then reply [CONCLUDED].\n"
5554:                       "If a blocker has repeated across passes, do NOT re-probe it - record it once in memory/ops/blockers.md as an OPS-NOTE (exact command + er
5555:                       % len(batch)) + "\n".join(t for _, t in sections)
5556:             run, err = start_group_run(prompt, extra={"solo": True, "autoloop_why": why,
5557:                                                       "cast_override": batch})
5558:             if not err:
5559:                 d["streak"] = 0 if productive else int(d.get("streak", 0)) + 1
5560:                 d["last_pass"] = {"agent": ", ".join(batch), "batch": len(batch), "why": why,
5561:                                   "productive": productive,
5562:                                   "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
5569: def _reap_stale_group_run():

### goal-reset arm (L6290-6340)
6291:         return {"ok": False, "error": str(e), "agents": []}
6298:     # 100% / level-ups. Reported separately per agent ("scheduled" field).
6299:     total = sum(a["total"] - a.get("scheduled", 0) for a in agents)
6300:     done_all = sum(a["done"] for a in agents)
6301:     resp = {"ok": True, "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
6302:             "fleet_pct": round(100.0 * done_all / total, 1) if total else 0.0,
6303:             "fleet_done": done_all, "fleet_total": total, "agents": agents}
6304:     # Goal-cycle upgrade (2026-11-15): at 100% for ALL agents the backend arms a persistent
6306:     # re-arming refreshes 'at' while armed, never resurrects a consumed flag.
6308:     # "consumed" raise and re-armed on EVERY poll, so auto-loop passes kept consuming a flag
6311:     # 2026-11-24 fix: the 11-23 mtime test ("no agent-file newer than consumed_at") DEADLOCKED
6318:     if total and done_all >= total:
6319:         gf = os.path.join(HERE, "memory", "goals", "GOAL_RESET_PENDING.json")
6323:                 with open(gf, encoding="utf-8") as f:
6327:             if d.get("armed"):
6329:             elif not d or not d.get("consumed_at"):
6330:                 with open(gf, "w", encoding="utf-8") as f:
6331:                     json.dump({"armed": True, "at": time.strftime("%Y-%m-%d %H:%M:%S"),
6332:                                "note": "All agent goals 100% reached - next group run starts a new goal-setting round."}, f)
6336:                     _ca_t = time.mktime(time.strptime(d["consumed_at"], "%Y-%m-%d %H:%M:%S"))
6340:                 for f2 in os.listdir(gdir):

### [SHELL]/[MODEL LOAD] composition sites
4950: # not elevated, route admin commands through the elevated helper service (elev.py ->
4954: full_text += ("\n\n[SHELL] Shell is not elevated, but admin commands DO work via the helper: run "

### goal-set round forcing
4866: # backend armed memory/goals/GOAL_RESET_PENDING.json. Consume it here: this run MUST
4870: # GOAL_RESET_PENDING.json to 0 bytes via open("w") and left the flag corrupted).
4874: _gf = os.path.join(HERE, "memory", "goals", "GOAL_RESET_PENDING.json")
5879: lines += ["Next cycle: a new goal-setting round is armed (GOAL_RESET_PENDING); the next",
6319: gf = os.path.join(HERE, "memory", "goals", "GOAL_RESET_PENDING.json")
7842: level-up + GOAL_RESET_PENDING arming independent of both; same code path as /api/goals."""

## 5. Verdict + patch spec (2026-11-26)

Injection chain: `_autoloop_watchdog()` (L5332, 15s tick) builds per-agent sections
(`_agent_open_goals` L5231, `_autoloop_behaviour_hint` L5251, idle menu L5527) ->
`start_group_run()` (L4847) prepends GOAL-SETTING ROUND if `GOAL_RESET_PENDING.json`
armed (L4874/4935), appends [SHELL] (L4954) + [MODEL LOAD STATUS] (L4983) -> group run.

Measured cost (this transcript, 450,559 B): ~152 KB (34%) is repeated injection
boilerplate: [MODEL LOAD STATUS] 72.8 KB x52, [SHELL] 53.8 KB x69, AUTO-LOOP hdr
8 KB x48, GOAL-SETTING ROUND 10.8 KB x16 + CYCLE-COMPLETE banners 5.6 KB x16.

Bugs/corners found:
1. Goal-set re-arm loop (L6318+): by design re-arms on no-op round (11-24 fix chose
   retry over deadlock), but with seats unreachable it re-injected the round 16x in
   this transcript, each costing a full batch pass. No backoff/cap.
2. Goal text truncated at [:200] (L5238) - acceptance criteria cut mid-sentence
   ("Mismatch = auto-", "pe"); agents must re-read the file anyway.
3. Stale dispatch: reached goals re-dispatched for days (orchestrator Day-7,
   researcher/builder #11 dispatched ~6x after closure on disk). Root cause: SSOT
   ledger lags live files + 'Verified:' text in goal lines misread as markers
   (dispatch_audit.py: 93.63% conformance, all violations = researcher).
4. Idle menu (a/b/c/d) undifferentiated: >=5 agents wrote duplicate stale-claim
   resolution files for the SAME claims; 128 [SILENT] replies in transcript.
5. BEHAVIOUR quotes up to ~160 chars verbatim of last reply - noisy paragraphs.
6. Every seat sees all sections ("Work ONLY YOUR section") - ~12 KB/seat/pass of
   other seats' instructions in each model context (8-agent batch).

VERDICT: No full rewrite. Architecture is sound and carries a documented fix history
(clobber loop, stall killer, auto-resume budget, seat relocation) that a rewrite would
risk losing. Targeted surgery on the composer:

P0 (cheap, do first):
 - L6318 arming: add backoff - max 3 re-arms/day with rising cooldown, or gate on
   >=1 chair-capable seat reachable; store last_arm_ts in GOAL_RESET_PENDING.json.
 - L5238: drop [:200]; emit full goal line OR truncate at sentence boundary +
   " (full AC in memory/goals/<n>.md)".
 - L4954/L4983: hash-gate [SHELL]+[MODEL LOAD STATUS] - include only when text
   changed since the seat last saw it (per-seat seen-hash in autoloop state).
P1:
 - _agent_open_goals: annotate goals whose cited artifact exists on disk with
   "(verify-first)" to stop redo loops; or regenerate SSOT before dispatch.
 - Idle menu: dedup option (c) against claims resolved in last 48h; rotate options.
 - BEHAVIOUR: classified one-liner + pointer, not verbatim quote.
P2 (only if token cost stays high): per-agent sections via per-seat system prompt
 instead of one group message (touches cross-talk mechanics - needs careful test).

Estimate: P0+P1 removes ~35-45% of injected bytes/pass and kills the two observed
failure modes (goal-set loop, stale-dispatch redo).
