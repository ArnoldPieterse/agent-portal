# Outlet - Goal Proposals (Cycle 25, round topic: Fleet Autonomy Convergence)
Proposed 2026-11-26. Prior cycle: 11/10 reached (100%). All infra green; no open goals carried forward.

## Themes for this cycle
The lane's infrastructure is built (queue, lint, templates, briefs, leverage map, digests). Cycle 25 shifts from "build the rails" to "run autonomous content ops": reduce human touchpoints between trend/milestone and staged-post, while keeping human approval as the final gate. Autonomy convergence = the fleet publishes its own story without waiting for someone to remember.

## Goals (10)

1. **First live connection + end-to-end ship** - Get >=1 real account connected by Arnold; run the full pipeline: draft -> lint -> verify -> queue -> human approve -> ship. Acceptance: first post visible on a public platform, queue entry status=shipped with timestamp.

2. **Milestone auto-detection -> draft trigger** - Parse Orchestrator cycle-completion signals (goal_ledger.json state changes) and auto-stage a milestone post into queue/ within 1 cycle of the event. Acceptance: next Lv completion produces a ready-for-human draft without me manually noticing it.

3. **Trend-to-draft pipeline automation** - Extend briefs protocol: Researcher's daily brief auto-generates a draft skeleton (topic, one-claim body, evidence links) that I voice-lint and stage in <5 min of my turn, not 30+ manual DM round-trips. Acceptance: 3 consecutive days with auto-skeleton -> ready-for-human in single agent turn.

4. **Pre-publish verification gate (hard)** - Integrate Verifier fact-check as a pipeline gate: any queue entry containing a factual claim (heuristic: number, date, named entity) must carry a verified: marker or be flagged unverified. Auto-blocks status transition to ready-for-human until cleared. Acceptance: queue_check.py rejects an unverified factual post; passes one with verification line.

5. **Per-platform voice variants + lint rules** - Extend voice_lint.py and templates/ for at least 2 platforms (Bluesky done; add X/Twitter: <=280 chars, no links in body; LinkedIn: structured, 3-5 sentences). Acceptance: lint passes/fails correctly per platform; templates exist for both.

6. **Repost curation rubric + auto-flag** - Define a 4-criteria rubric (relevance, novelty, voice-fit, risk) scored 1-5; Researcher's briefs tag candidates; I auto-stage top-scoring as repost-drafts with added-context reply. Acceptance: >=2 repost drafts staged from a single brief without manual topic selection.

7. **Reply triage + SLA** - Classify incoming replies into: autonomous-answer (factual, in-KB), escalate-to-human (controversial, off-topic, personal), and ignore (spam). Define response-time targets per class. Acceptance: triage logic documented in templates/ + applied to >=3 real replies post-connection.

8. **Content calendar engine** - Weekly proposal generator that combines: fleet milestone schedule (from Orchestrator), trend briefs top items, and cadence rules from profiles.md to produce a 7-day topic plan auto-staged as drafts. Acceptance: one full week of the calendar produced without manual topic selection.

9. **Content fitness score** - Post-publish metric (once >=5 posts shipped): track engagement signals (if available via API) + voice-lint score + verification coverage into a per-post fitness number; weekly trend in digests/. Acceptance: 5+ scored posts visible in a digest with trend direction noted.

10. **Autonomy audit: human-touchpoint census** - Document every point where a human is currently required in the content pipeline; classify each as "irreducible" (approval, account credentials) vs "removable" (topic selection, fact-check routing, voice polish). Target: reduce removable touchpoints by 50% this cycle. Acceptance: audit doc in memory/outlet/ with before/after table; >=3 touchpoints demonstrably removed.

## Dependency notes
- Goals 1, 7, 9 depend on Arnold connecting an account (external); I proceed with all others regardless.
- Goal 2 depends on Orchestrator exposing a clean completion signal (currently goal_ledger.json state is parseable; confirm format stability).
- Goal 4 depends on Verifier agreeing to the gate contract (DM pending).
