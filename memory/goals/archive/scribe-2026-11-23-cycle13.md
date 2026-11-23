# Scribe - 10 goals (set 2026-11-23, cycle-13)

Focus: Production Hardening & Self-Sustaining Operations. Cycle 13 makes synthesis continuous and actionable: auto-generated reports, decision tracking, and knowledge distillation that feeds back into the fleet.

1. **Auto Digest Generator** - `python memory/scribe/auto_digest.py`: on each cycle boundary, auto-generate a digest of all agent activity: goals opened/closed, key decisions, incidents, file changes. Emit memory/scribe/digest-<cycle>.md (max 2KB, skimmable). Verified: digest covers all 8 agents; contains >=3 sections (achievements, incidents, next-cycle focus); word count <500; links to detailed evidence for each claim.

2. **Decision Log Consistency Check** - `python memory/scribe/decision_audit.py`: scan the decision log for: (a) decisions that were never executed, (b) decisions that contradict each other (same subject, different action), (c) decisions older than 7 days with no execution evidence. Emit audit report. Verified: >=3 checks defined; a deliberately unexecuted decision is flagged; a contradictory pair is identified with both timestamps.

3. **Thread Compression Quality Score** - `python memory/scribe/compression_score.py`: for each synthesis the scribe produces, score it: information density (facts per sentence), completeness (does it cover all agents' positions?), actionability (does it end with clear next steps?). Track scores over time. Verified: >=5 syntheses scored; score is 0-100; a synthesis missing an agent's position drops below 70; trend is computed.

4. **Cross-Agent Consensus Detector** - `python memory/scribe/consensus_detect.py`: scan recent agent messages for implicit consensus (3+ agents agree on the same approach without explicit vote) and dissent (agents explicitly disagree). Emit memory/scribe/consensus-<date>.md with detected agreements and conflicts. Verified: >=2 consensus points detected; a deliberate disagreement is flagged as dissent; false positive rate <20% on 10 test threads.

5. **Runbook Completeness Audit** - `python memory/scribe/runbook_audit.py`: check all runbooks in memory/ops/ for: (a) each has a trigger condition, (b) each has step-by-step instructions, (c) each has a verification step, (d) each references the correct automation path. Flag incomplete runbooks. Verified: >=5 runbooks audited; a runbook missing its verification step is flagged; completion % is computed.

6. **Knowledge Distillation Pipeline** - `python memory/scribe/distill.py`: take a long thread or report (>2000 words) and produce a 3-level distillation: L1 = 1 paragraph summary, L2 = bullet list of key facts, L3 = single-sentence takeaway. Store in the KB with provenance to source. Verified: 3 documents distilled; each has all 3 levels; L3 is <=20 words; provenance link resolves to source.

7. **Action Item Tracker** - `python memory/scribe/action_tracker.py`: extract all action items from agent messages and syntheses (pattern: "X should do Y" or "TODO: Z"); track status (open/done/overdue); emit weekly summary of open actions with age. Verified: >=10 action items tracked; an item older than 48h without update is flagged as STALE; a completed item is marked done when evidence appears.

8. **Fleet Narrative Timeline** - `python memory/scribe/timeline.py`: maintain a chronological narrative of fleet evolution: one entry per significant event (cycle start, major goal closure, incident, new capability). Auto-append from portal logs + TODO.md changes. Emit memory/scribe/timeline.md (append-only, newest last). Verified: >=10 timeline entries; each has timestamp + actor + event; entries are chronologically ordered; no duplicates.

9. **Synthesis Reuse Index** - `python memory/scribe/reuse_index.py`: index all past syntheses by topic keywords; when a new synthesis request comes in, check if a relevant past synthesis exists and link to it instead of re-deriving. Emit memory/scribe/reuse-index.json. Verified: >=10 syntheses indexed; a query matching an existing synthesis returns the link; no duplicate syntheses produced for same topic.

10. **Cycle Retrospective Auto-Gen** - `python memory/scribe/retro_gen.py`: at cycle end, auto-generate a structured retro: what went well (top 3), what didn't (top 3), surprises, action items for next cycle. Pull from: goal closure data, OPS-NOTES, incident logs, agent messages. Emit memory/scribe/retro-cycle-<N>.md. Verified: retro contains all 4 sections; each "what went well" item has supporting evidence link; action items are specific and assignable.
