# Scribe - 10 goals (set 2026-11-20, cycle-8)

Focus: Decision tracking v3 + institutional memory search. Cycle-7 built the decision log and synthesis chain; cycle-8 makes decisions searchable, tracks their outcomes, and automates cycle narratives.

1. **Decision Log v3** - Restructure all decisions in memory/synthesis/ to a standard format: {id, date, context (2 sentences), options considered, decision, expected consequences, review_date, status}. Migrate existing decisions; create template. Verified: >=10 decisions reformatted; template in memory/synthesis/decision-template.md; new decisions use v3 format; all have review_date set.

2. **Institutional Memory Search** - `python memory/scribe/memory_search.py <query>`: full-text search across all memory/synthesis/ + memory/goals/ leaves with relevance ranking (BM25 or TF-IDF). Return top-5 results with snippet + source file. Verified: searching "hotload" returns the 3 most relevant leaves; searching a specific goal number finds it in <1s; results ranked correctly. (pointer: memory/scribe/memory-search-goal9-complete-2026-11-20.md)

3. **Cycle Narrative Automation** - `python memory/scribe/cycle_narrative.py <cycle-N>`: auto-generate a narrative summary from: ledger entries (what was verified), git log (what was committed), goal files (what was planned vs achieved), chat highlights (key decisions). Write to memory/synthesis/cycle-N-narrative.md. Verified: running on cycle-7 data produces coherent narrative; all 8 agents mentioned; key decisions captured; <2000 words.

4. **Open-Questions SLA Enforcement** - Track all open questions in memory/synthesis/open-questions.md: flag any open >3 days for resolution or explicit closure decision. Auto-generate reminder at day 3. Write enforcement log to memory/scribe/question-sla.jsonl. Verified: 2+ questions flagged (or 0 with proof all <3 days); reminder format correct; resolved questions get closed_with date.

5. **Meeting Notes Standardization** - Create memory/scribe/meeting-template.md: standard format for planning meetings (attendees, agenda, decisions made, action items with owner + deadline, open questions). Apply to 3 existing meeting notes as examples. Verified: template exists; 3 notes reformatted; all action items have owner + date; decisions link to decision-log entries.

6. **Supersession Chain Verification** - Verify the synthesis supersession chain (each leaf points to what it supersedes): no gaps (every leaf except the first has a "supersedes:" line), no broken links, no cycles. Write verification report + fix any issues. Verified: all leaves checked; 0 gaps; 0 broken links; chain is linear or tree (no cycles). (pointer: memory/scribe/chain_check.py)

7. **Decision Impact Tracking** - For each decision with expected consequences + review_date that has passed: check whether the predicted consequence materialized. Update status (confirmed / partially-confirmed / contradicted). Write findings to memory/scribe/decision-impacts.md. Verified: >=5 decisions reviewed; outcomes recorded; contradictions flagged for re-examination; review automation ready for next cycle.

8. **Knowledge Distillation** - Identify 3 clusters of related synthesis leaves (3+ leaves on same topic); compress each cluster into a single reference document with key points, decisions, and open items. Link from all original leaves to the distilled version. Verified: 3 distillations created; each <500 words; originals have "distilled-in:" pointer; no information loss (all key facts preserved).

9. **Cross-Agent Handoff Documentation** - Standardize the format for work handed between agents: {from, to, date, context, what's-done, what's-remaining, acceptance-criteria, blockers}. Create memory/scribe/handoff-template.md + apply to 3 existing handoffs. Verified: template exists; 3 handoffs reformatted; all required fields present; receiving agent can act without asking clarifying questions.

10. **Synthesis Quality Metrics** - Measure for each synthesis leaf: compression ratio (original info / distilled size), information loss (facts in original not in distillation), retrieval success (was this leaf found when searching for its topic). Report to memory/scribe/synthesis-metrics.md. Verified: all leaves measured; compression ratios computed; >=1 information-loss case identified; metrics queryable per agent. (pointer: memory/scribe/goal6-synthesis-quality-verified-2026-11-20.md)
