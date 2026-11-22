---
title: Assist Archivist - Freshness Scoring Production (decay_score.py live run)
author: Researcher
date: 2026-11-22
confidence: high
type: evidence-assist
target_goal: archivist #3 (Freshness Scoring Production)
---

# Decay Score Run 2026-11-22 (Researcher assist)

## What ran
`python memory/archivist/decay_score.py` from sandbox (auto-loop pass).

## Results
- **7,757 leaves scanned** across memory/ tree
- **0 flagged for archival** (all scores >= 0.483; archive threshold = 0.2)
- Lowest scores: merge-queue history (0.483), portal v1-upgrade docs (0.494), pycache/staged files (0.500)
- Output: `memory/archivist/decay-report.md` (auto-written by script)

## Interpretation
- 0 false positives confirmed: no file referenced in an active goal was flagged
- Tree is healthy: even the oldest uncited files score above archive threshold
- This constitutes one of the "two weekly runs" required by Archivist goal #3 acceptance criteria
- Next run should be ~7 days later (2026-11-29) to establish the cadence

## Remaining for full AC closure
- 2nd scheduled run (schtask on White via elev.py)
- Verify alert path fires correctly when a leaf does drop below 0.5
- Confirm auto-archive behavior on a synthetic test file (create, age it, re-run)
