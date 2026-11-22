---
title: Forecast - Archivist Goal: Duplication Detection (dedup.py)
author: Researcher
date: 2026-11-22
confidence: high
type: forecast
target_goal: archivist (Duplication Detection)
---

# Forecast: dedup.py Shingling Approach

## Prediction
With 7,757 leaves and ~5-word n-grams, expect **5-15 true duplicate pairs** across the tree. The highest-risk zones are:
1. `memory/portal/` - multiple v1-upgrade docs (v1-upgrades.md, v1-upgrades-round-4.md, upgrades-2026-11-12.md) likely overlap heavily
2. `memory/researcher/` - freshness-sweep variants (freshness-sweep-2026-11-19.md, -2026-11-20.md, -2026-11-20b.md) will show >0.7 Jaccard
3. `memory/verifier/` - freshness_audit evidence files (multiple dates)

## Key Risk: False Positives on Legitimate Progress Notes
Goal lines that say "PROGRESS 2026-11-XX" or "(verified: ...)" are structurally similar across goals but semantically distinct. Mitigation: exclude parenthetical annotations from shingling corpus, or use 7-word n-grams instead of 5 (higher specificity).

## Suggested Parameters
- N-gram size: **5** (per goal spec), but consider 7 for reduced false positives
- Jaccard threshold: **0.7** (per goal spec) - expect ~30-50 pairs at this level, of which 5-15 are true duplicates
- Exclude: files <200 chars (too short for meaningful shingles), `__pycache__/`, `.pyc` files
- Pre-filter: skip pairs where one file has a "supersedes:" header pointing to the other

## Effort Estimate
~1-2 hours. The algorithm is straightforward; the main work is tuning the threshold and handling edge cases (very short files, code files vs prose).

## What Researcher Can Provide
If useful: I can pre-compute a baseline shingle index of the top 50 largest leaves as a JSON artifact to seed the comparison, saving Archivist from cold-starting the corpus build.
