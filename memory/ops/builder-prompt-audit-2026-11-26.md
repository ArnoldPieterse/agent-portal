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
- boilerplate bytes: autoloop_hdr=8016 shell=53806 modelload=72779 goalset=10832 cyclecomplete=5648