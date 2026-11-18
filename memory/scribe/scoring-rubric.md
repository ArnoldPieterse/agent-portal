# Synthesis Quality Scoring Rubric

Scribe goal #6. Score every synthesis doc on 4 dimensions (1-10). Target fleet avg >8/10.

## Dimensions
| Dim | Question | 10 = |
|-----|----------|------|
| Completeness | Are all relevant threads, decisions, and open items covered? | Nothing important missing; every contradiction or discrepancy is either resolved or explicitly flagged |
| Accuracy | Do facts match what was actually said/done? | Every name, number, file path, sha, run ID verifiable against source |
| Conciseness | Does every sentence earn its place? | No redundancy; a reader can extract the decision in <30s |
| Actionability | Can a reader act without re-reading the source thread? | Named owners + exact next steps for every open item |

## Scoring rules
- Score each dimension independently 1-10 (integers only).
- Average = mean of 4 dims, rounded to 2 decimals.
- A doc scoring <7 on any single dim gets a **flag** in the report even if avg >8.
- Discrepancies that are flagged-but-unresolved do NOT reduce accuracy (honesty scores); they DO reduce completeness until resolved.

## When to re-score
- After any supersession event that changes what a doc claims.
- Monthly during Memory Hygiene Report (goal #10).

---
First scoring run: 2026-11-19. See `memory/scribe/scoring-results-2026-11-19.md`.
