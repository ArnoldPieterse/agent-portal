# Outlet - Cross-Agent Leverage Map
Last updated: 2026-11-25. Which agent to DM for what, with concrete ask formats + expected turnaround.

---

## Quick reference (agent -> what to ask)

| Agent | Ask for | Format | Typical cost/time |
|-------|---------|--------|-------------------|
| Researcher | Current trends, verified data points, source URLs | DM: "Trend brief: top-5 items relevant to {topic}, each with 1 URL + 1-sentence finding" | ~1 cycle (same-day) |
| Archivist | Canonical KB references, past decisions, provenance links | DM: "KB lookup: {question} - need the canonical reference + date it was decided" | ~1 cycle |
| Designer | Visuals, layout suggestions, wording polish for a post | DM: "Polish pass on this draft: {paste body}. Keep under 600 chars, fleet voice." | ~1 cycle (Lumen/Reel if media) |
| Scribe | Compress a long thread or report into post-sized summary | DM: "Compress: {link or paste} into <=3 sentences that read as a standalone claim" | ~1 cycle |
| Builder / Mechanic | Technical accuracy on fleet architecture, model details | DM: "Fact-check this technical claim for a public post: {claim}. Confirm or correct." | ~1 cycle |
| Verifier | Pre-publish fact-check on any factual claim in a queued post | DM: "Fact-check gate: {paste evidence section from queue entry}. PASS/FAIL per claim." | ~1 cycle (blocking) |
| Orchestrator | Topic priority, what matters most right now | DM: "Priority check: we have {option A} vs {option B} for next post. Which serves the round topic better?" | ~1 cycle |
| Scribe (secondary) | Ship-readiness summary of queue state | DM: "Queue digest: count by status + list any blocked items with named unblockers" | ~1 cycle |

---

## Concrete DM ask formats

### Researcher - trend brief
```
[DM @Researcher] Trend brief request for {date}:
Topic filter: {round topic or specific angle}
Need: top-5 items, each = (title, 1-sentence finding, source URL, confidence)
Deliver to: memory/outlet/briefs/{date}-trend-brief.md
```

### Archivist - KB reference
```
[DM @Archivist] KB lookup for content pipeline:
Question: {exact question}
Context: we're drafting a post about {topic} and need the canonical answer
Deliver: pointer path + 1-line summary + date decided
```

### Designer - polish pass
```
[DM @Designer] Voice polish request:
Draft: {paste body text}
Constraints: fleet default voice, <=600 chars total, one concrete claim
Need: rewritten body or specific line suggestions
```

### Scribe - compression
```
[DM @Scribe] Compress for post:
Source: {paste or link}
Target length: <=3 sentences, reads as standalone
Tone: warm/candid, no corporate language
Deliver: the 3-sentence version + any caveats about what was cut
```

### Builder/Mechanic - tech accuracy
```
[DM @Builder] Tech fact-check for public post:
Claim: {exact sentence from draft}
Context: going into a milestone post about {topic}
Need: confirm / correct with the accurate phrasing
```

### Verifier - pre-publish gate
```
[DM @Verifier] Fact-check gate (blocking):
Queue entry: {filename}
Claims to verify:
  1. {claim 1} -> source: {evidence link}
  2. {claim 2} -> source: {evidence link}
Return: PASS/FAIL per claim + any corrections needed
```

### Orchestrator - priority
```
[DM @Orchestrator] Topic priority for next post:
Option A: {description, ~1 line}
Option B: {description, ~1 line}
Round topic: {current round topic}
Need: which one + 1-line reasoning
```

---

## Cost/time expectations
- "1 cycle" = within the same auto-loop batch pass (minutes to ~30 min depending on queue depth).
- Verifier gate is BLOCKING: do not mark a post ready-for-human until Verifier returns PASS.
- If an agent is unreachable (see MODEL LOAD STATUS), note it in the queue entry's Notes-for-ship and move to next goal; retry next pass.

## Anti-patterns (do NOT)
- Do not DM multiple agents for the same ask in parallel when one would suffice.
- Do not ask Researcher for KB references (that's Archivist) or ask Builder for trend data (that's Researcher).
- Do not skip Verifier on factual claims - "I'm confident" is not a fact-check.
