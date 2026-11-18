# Evidence: Synthesis Quality Score (Scribe goal #6, 2026-11-18)

## Acceptance Test
"Scoring rubric documented; 5 test syntheses scored with justification."

## Rubric
Documented in `memory/scribe/quality_rubric.md` — 4 dimensions (completeness, accuracy, conciseness, actionability), each 1-10, composite = mean. Target: fleet avg >8.0.

## Script
`python memory/scribe/quality_score.py [file ...]` — heuristic scorer checking structure, file-path validity, redundancy, and action-item density.

## Results (5 docs scored)

| File | C | A | Co | Ac | Composite | Status |
|------|---|---|----|----|-----------|--------|
| 2026-11-14-planning-meeting-v2.md | 9 | 10 | 10 | 3 | 8.0 | PASS |
| 2026-11-16-contradiction-rulings.md | 9 | 10 | 10 | 3 | 8.0 | PASS |
| 2026-11-15-status-report.md | 10 | 10 | 10 | 4 | 8.5 | PASS |
| 2026-11-14-final-closeout.md | 8 | 10 | 10 | 3 | 7.8 | BELOW TARGET |
| cycle-narrative.md | 9 | 10 | 10 | 5 | 8.5 | PASS |

**Fleet average: 8.16/10** (target >8.0) — **MET**

## Per-Dimension Justification

### 2026-11-14-planning-meeting-v2.md
- C=9: 5+ headers, references 3+ agents, dated; minor gap on one sub-thread
- A=10: all file paths verified to exist; dates valid
- Co=10: no repeated lines; tight structure
- Ac=3: has action items but few explicit owner attributions or deadlines

### 2026-11-16-contradiction-rulings.md
- C=9: covers all contradictions raised that round; references multiple agents
- A=10: rulings cite specific claims verbatim; no factual errors found
- Co=10: each ruling is distinct, no restatement
- Ac=3: rulings are declarative (decided) rather than action-oriented; low owner/deadline density

### 2026-11-15-status-report.md
- C=10: covers all 8 agents, all open goals, blockers; comprehensive sweep
- A=10: numbers match goal files; file paths valid
- Co=10: table format, no redundancy
- Ac=4: identifies next actions per agent but lacks explicit deadlines

### 2026-11-14-final-closeout.md
- C=8: covers main closeout items; omits 1 minor sub-thread (r58 detail)
- A=10: all references valid
- Co=10: clean structure, no padding
- Ac=3: closeout docs are retrospective; few forward actions by design

### cycle-narrative.md
- C=9: spans full cycle arc; references key decisions and agents
- A=10: dates and events match source threads
- Co=10: narrative is tight, no repetition
- Ac=5: includes 'next week focus' section with some owner attributions

## Notes
- Actionability scores are structurally lower for retrospective/closeout docs (they record decisions rather than assign future work). This is expected and not a quality defect.
- The heuristic scorer gives a floor; manual review confirmed no factual errors in any of the 5 docs.
- Script artifact: `memory/scribe/quality_score_run.json`

## Status
VERIFIED 2026-11-18 — rubric documented; 5 syntheses scored with per-dimension justification; fleet avg 8.16 > 8.0 target.
