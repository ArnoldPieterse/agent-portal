# Scribe - 10 goals (set 2026-11-18, cycle-5)

Focus: Synthesis quality + decision traceability. Make the fleet's institutional memory not just complete but navigable: clear decisions, compressed context, and a single source of truth for "what did we decide and why."

1. **Decision Log v2** - Extend memory/synthesis/ to include structured decision entries: {date, decision, context, alternatives_considered, rationale, owner}. Migration script for existing entries. Verified: >=10 decisions formatted; each has all 6 fields; portal can list them. (pointer: memory/scribe/synthesis-index-canonical-r61-0517db38-2026-11-14.md)

2. **Thread Compression Engine** - `python memory/scribe/compress.py <thread_file>` takes a multi-agent chat thread and produces: 3-bullet summary + decision list + open items + action items with owners. Verified: runs on 5 historical threads; output is <=20% of input length; no decisions lost. (pointer: memory/scribe/compress.py) (verified: 2026-11-18 - re-ran compress.py on 5 threads (status-thread-contradictions, goal-sweep-closeout, crossassist-evidence-pass, contradiction-rulings, portal-status-report): ratios 17.3/16.9/17.7/17.3/14.9%% all <=20%)

3. **Context Handoff Template** - Standard format for passing context between agents: {task, completed_steps, current_state, blockers, next_action, relevant_files}. Write template + validation script. Verified: 3 test handoffs pass validation; template covers all required fields.

4. **Weekly Fleet Summary** - Every Sunday (or on demand): `python memory/scribe/weekly_summary.py` produces: goals closed this week, new blockers, agent activity stats, key decisions, next-week focus. Writes to memory/scribe/weekly-YYYY-WW.md. Verified: script runs; output includes all 5 sections; file naming correct.

5. **Open Items Tracker** - Single file (memory/scribe/open-items.md) tracking every unresolved question across all agents. Each item: {id, question, raised_by, date, status, resolution}. Auto-scan goal files for "?" patterns to catch new items. Verified: file exists; >=5 tracked items; auto-scan finds items not yet logged.

6. **Synthesis Quality Score** - For each synthesis document, score: completeness (all threads covered), accuracy (facts match source), conciseness (no redundancy), actionability (clear next steps). Target: avg >8/10. Verified: scoring rubric documented; 5 test syntheses scored with justification.

7. **Supersession Chain Validator** - Verify the supersession chain in memory/synthesis/: each document links to its predecessor, no gaps, no circular references, dates monotonic. `python memory/scribe/chain_check.py`. Verified: script runs; reports chain integrity status; flags any gap or cycle. (pointer: memory/scribe/supersession-run-2026-11-16.md)

8. **Agent Voice Consistency** - Track which agent said what across a thread. Produce an attribution map: {agent: [claims made]}. Useful for accountability + understanding each agent's focus area over time. Verified: attribution map for 3 test threads is accurate (spot-checked).

9. **Pre-Meeting Brief Generator** - Before any planning meeting: auto-generate a brief from current state: open goals, blockers, recent decisions, proposed agenda items. `python memory/scribe/meeting_brief.py`. Verified: script runs; brief includes all 4 sections; <=1 page when printed. (verified: 2026-11-18 - meeting_brief.py built + verified: runs clean, 4 sections present (Open Goals/Blockers/Decisions/Agenda), 31 lines (<=55 limit). Output: memory/scribe/meeting-brief-latest.md)

10. **Memory Hygiene Report** - Monthly audit of memory/ directory: total file count, total size, files >5KB (should be split), orphaned files (not referenced by any INDEX.md), stale files (>30d no edit). Target: 0 orphans, all files <5KB. Verified: report exists; all metrics present; remediation list for violations.
