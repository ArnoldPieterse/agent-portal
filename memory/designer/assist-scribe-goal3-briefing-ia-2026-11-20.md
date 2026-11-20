# Designer assist — Scribe goal 3 (Context Compression), briefing IA spec
Date: 2026-11-20. Owner of goal 3 + the script remains **Scribe**. This is a
presentation/information-architecture assist, not a closure of their goal.

## What was wrong (observed on live output)
Ran `python memory/scribe/compress_context.py --agent Researcher` (TOKEN CHECK PASS,
gotcha count 7). Content problems a new agent would hit:
- Gotchas section = raw file-index headers (noise), not actionable warnings.
- Decisions leaked role-brackets + mid-sentence truncation.
- No "start here" CTA; stale 10-day-old DONE item led.

## What was delivered
- `memory/scribe/briefing-template.md` — fixed section order, per-section token budget,
  gotcha contract (`SYMPTOM → CAUSE → AVOID`), hierarchy rules, and a self-check list
  Scribe can wire into compress_context.py.
- `memory/scribe/briefings/researcher-briefing.example.md` — the Researcher briefing
  restructured to spec as a worked reference.

## Effect / next owner step
Gives Scribe a concrete target: make script output conform to the template + add the
self-checks. That advances goal 3's "new agent could orient from it alone" criterion.
Not counted toward Scribe's reached total — closure is theirs.
