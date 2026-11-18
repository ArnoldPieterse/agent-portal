# Goal 9: Pre-Meeting Brief Generator - Evidence (2026-11-18)

**Status:** CLOSED

## What was built
`memory/scribe/meeting_brief.py` — generates a 1-page pre-meeting brief from live fleet state.

## Acceptance criteria check
| Criterion | Result |
|-----------|--------|
| Script runs | PASS (exit 0, clean output) |
| Brief includes all 4 sections | PASS (Open Goals, Active Blockers, Recent Decisions, Proposed Agenda) |
| <=1 page when printed | PASS (31 lines, limit 55) |

## Data sources used
- `memory/goals/*.md` — open goal counts per agent
- `memory/ops/blockers.md` — unresolved blockers only
- `memory/scribe/decision_log.md` — last N decisions by date

## Output artifact
`memory/scribe/meeting-brief-latest.md` (regenerated each run)

## Usage
```
python memory/scribe/meeting_brief.py [--output PATH] [--decisions N]
```
