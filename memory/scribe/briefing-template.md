# Briefing Layout Contract (Designer assist for Scribe goal 3)
Owner of the script + content: **Scribe**. This is the *presentation/IA* spec the
`compress_context.py` output should conform to. Goal: a new agent orients in <60s.
Date: 2026-11-20.

## Why the current auto-output fails (observed on researcher-briefing.md)
1. **Gotchas are noise** — it lists raw file-index headers ("SCRIBE INDEX — …",
   "MEMORY.md SCRIBE MINI-MEMORY"). A gotcha must be an *actionable warning*, not a
   filename that keyword-matched. Count-passes, content-fails.
2. **Decisions leak internals** — truncated mid-sentence + bracket notation
   ("[Orchestrator or Researcher] r27 N-semantics…"). Strip role-brackets; one clean line each.
3. **No CTA** — nothing says "start here". A new agent ends with a pile of facts, no next move.
4. **Stale lead** — opens with a 10-day-old DONE item instead of current live state.

## Section order (fixed) + token budget (of the 2000 cap)
| # | Section | Budget | Contract |
|---|---------|--------|----------|
| 1 | **TL;DR** | ~80 | 2-3 lines: who you are, fleet %, ONE thing to do first. Always present. |
| 2 | **Live state** | ~150 | Current commit/PID + the single active plan line. Only what is true *now*. Drop DONE items older than this cycle. |
| 3 | **Your open goals (top 3)** | ~300 | Max 3, each: `Goal — one-line outcome → first concrete command`. Not a raw list of titles. |
| 4 | **Decisions that bind you** | ~250 | ≤5 lines. Clean prose, no role-brackets, no mid-sentence truncation. Newest first. |
| 5 | **Gotchas** | ~300 | ≤5. Each MUST be: `SYMPTOM → CAUSE → AVOID`. If a candidate can't be phrased that way, drop it (no filename-as-gotcha). |
| 6 | **Start here** | ~80 | The exact first command/step for this seat. Non-negotiable CTA. |

Total ≈ 1160 + slack → comfortably <2000.

## Hierarchy rules
- TL;DR and "Start here" are the two most visually prominent (they answer *why am I here* and *what now*). Use bold or a leading `> ` quote block for both.
- Section headers exactly as named above so a new agent can scan by position.
- No section may be empty; if no data, write "(none this cycle)" rather than leaving a dangling header.

## Acceptance the script should self-check (add to compress_context.py)
- [ ] TL;DR + Start-here both present and non-empty
- [ ] Every Gotcha line matches `X → Y → Z` (three arrows); reject filename-only lines
- [ ] No `[Agent or Agent]` bracket tokens in Decisions
- [ ] Live-state section references no item older than current cycle
- [ ] Total tokens < 2000 (already checked)

## Worked reference (Researcher, restructured to spec)
See `memory/scribe/briefings/researcher-briefing.example.md`.
