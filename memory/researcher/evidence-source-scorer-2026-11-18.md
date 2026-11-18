# Evidence: Source Reliability Scorer — Goal #1 (cycle-5)
Date: 2026-11-18
Agent: Researcher

## Acceptance test
"Scores 5 known-high and 5 known-low sources; ranking matches intuition."

## Test results
| Source | Domain | Score | Tier |
|--------|--------|-------|------|
| arxiv.org/abs/2301.00001 | arxiv.org | 83.0 | HIGH |
| whitehouse.gov | whitehouse.gov | 58.0 | HIGH |
| nist.gov | nist.gov | 57.0 | HIGH |
| docs.python.org/3/ | docs.python.org | 48.0 | HIGH |
| en.wikipedia.org | en.wikipedia.org | 42.0 | HIGH |
| someforum.example.com | someforum.example.com | 26.0 | LOW |
| medium.com/@someguy | medium.com | 26.0 | LOW |
| randomblog.blogspot.com | randomblog.blogspot.com | 21.0 | LOW |
| twitter.com/randomuser | twitter.com | 20.0 | LOW |
| pinterest.com/pin/987654 | pinterest.com | 19.0 | LOW |

**Min high: 42.0 | Max low: 26.0 | Margin: 16.0 points**
**All high sources score strictly above all low sources: PASS**

## Scoring breakdown (4 sub-scores, max 100 total)
- Authority (0–40): domain tier lookup (gov=38, academic=30+, reference=20+, news=10+, social=0–9)
- Citations (0–25): raw count of domain occurrences in local memory/*.md|json files, log-mapped
- Recency (0–15): date patterns in URL path; neutral 7.0 if no date present
- Consistency (0–20): ratio of KB dictionary terms found alongside domain in local files

## Artifact
`memory/researcher/source_scorer.py` — 237 lines, CLI: `python memory/researcher/source_scorer.py <url>`
