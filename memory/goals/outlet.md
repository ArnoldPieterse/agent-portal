# Outlet - Cycle 23 Goals (set 2026-11-25 by Orchestrator)
Round topic: **Public Voice & Content Pipeline**
Pillars: (1) Profiles & voice system, (2) Content pipeline automation, (3) Cross-agent leverage + ship readiness
Focus: public voice; drafts uploads, replies and reposts with personality, leveraging every other agent strengths

1. **Profile Registry v1** - memory/outlet/profiles.md: schema for every profile (handle, platform, voice guide, cadence, hard lines); register the fleet default voice + one platform template profile. Verifier fact-checks one sample claim against it.
2. **Content Queue Convention** - memory/outlet/queue/: every staged post carries date, kind, platform, status, topic, body, rationale, evidence, ship notes; queue INDEX auto-updated; `python memory/outlet/queue_check.py` validates all entries (0 violations).
3. **Trend Intake DM Protocol** - standing request format to Researcher for a daily trend brief (top-5 trends + verified data points + sources); responses saved as dated briefs under memory/outlet/briefs/; >=1 brief file exists with >=3 sourced items.
4. **Fact-Check Gate** - every queued post gets Verifier sign-off before ready-for-human: evidence section lists each claim + check result; 100% of queue entries carry the fact-check field (queue_check.py enforces).
5. **Voice Consistency Lint** - `python memory/outlet/voice_lint.py`: checks drafts against the profile voice guide (length caps, banned corporate phrases, one-claim-per-post); flags a deliberately bad draft and passes a good one; run clean on all queue entries.
6. **Milestone Auto-Draft Trigger** - when fleet level or goal pct crosses a threshold (new level, +10% step), Outlet auto-drafts a milestone post from the level report + live ledger data into the queue with correct numbers.
7. **Reply & Repost Templates** - per-profile templates for replies and reposts (acknowledge, correct, amplify) written in the profile voice; >=3 template types per registered profile, each <=140 words, lint-clean.
8. **Cross-Agent Leverage Map** - memory/outlet/leverage-map.md: which agent to DM for what (trends->Researcher, KB->Archivist, visuals->Designer, compression->Scribe, accuracy->Builder/Mechanic, fact-check->Verifier, priorities->Orchestrator) with concrete ask formats + cost/time expectations; covers all 8 core agents.
9. **Ship Readiness Digest** - daily digest memory/outlet/digests/YYYY-MM-DD.md: queue status (ready/pending/needs-connection), blocked items with named unblockers, last-7-days shipped; >=1 digest exists matching live queue state.
10. **Platform Connection Runbook** - step-by-step runbook for Arnold to connect a platform account (auth, rate limits, API/tool needed) with the fleet default profile pre-wired; passes Mechanic's executability audit (every step = a command or a named human action); unblocks queue shipping on connection.
