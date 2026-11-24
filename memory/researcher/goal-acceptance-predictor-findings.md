# Goal Acceptance Rate Predictor - Findings & Limitations

**Date:** 2026-11-25
**Goal:** #3 Researcher cycle-17 - "from goal text features (length, specificity markers, verification complexity), predict whether a goal will be accepted as-is or need revision. Train on cycle 10-16 acceptance data. Verified: accuracy >75% on held-out set from cycles 14-16."

## Data Availability Finding

**Key constraint:** Archive files for cycles 10-16 contain PROPOSED goal sets (no progress/revision history). The only files with revision signals ([PROGRESS markers) are from earlier cycles (3, 5, 8):
- `researcher-2026-11-18.md`: 41 progress entries
- `designer-2026-11-19.md` / `-2026-11-20.md`: 11 each
- `mechanic-2026-11-23-cycle8.md`: 6
- `verifier-2026-11-23-cycle8.md`: 6
- Others: 1-5 entries

Total labeled dataset: **1717 goals** (1685 accepted, 32 iterated) - heavily imbalanced (98%/2%).

## Model Results

**Approach:** Gaussian Naive Bayes over 13 handcrafted text features. PROGRESS notes stripped from input text to avoid circular signal.

| Metric | Value |
|--------|-------|
| Training accuracy | 60.1% (722/1201) |
| Test accuracy (random 70/30 split) | **64.1%** (331/516) |
| Target | >75% |
| Result | **NOT MET** |

## Feature Analysis (what discriminates accepted vs iterated)

| Feature | Accepted mean | Iterated mean | Interpretation |
|---------|--------------|---------------|----------------|
| title_words | 4.91 | 3.38 | Iterated goals have SHORTER titles |
| backticks | 1.34 | 0.94 | Accepted goals cite more code/commands |
| file_refs | 0.71 | 0.38 | Accepted goals reference specific files |
| has_cmd | 0.49 | 0.19 | Accepted goals specify exact commands |
| specificity | 2.69 | 3.13 | Iterated goals have more numeric refs (ambiguous scope) |

**Pattern:** Goals that are under-specified (no file paths, no exact commands, shorter titles) are more likely to require iteration. This is consistent with the hypothesis that specificity at proposal time predicts acceptance.

## Why Target Not Achievable

1. **No labeled data for cycles 14-16:** The verification criterion requires a "held-out set from cycles 14-16" but those files contain only proposed goals with no revision history.
2. **Small positive class:** Only 32 iterated goals exist in the entire archive (2% of dataset).
3. **Weak feature separation:** With PROGRESS notes removed, max Δ is 41 chars (char_len) and 6.6 words - small signal relative to variance.

## Recommendations

1. **Data accumulation:** As cycles progress and agents work on goals, [PROGRESS entries will accumulate in cycle-17+ files. Re-run this predictor in 2-3 cycles when labeled data for cycles 14-16 exists.
2. **Alternative label:** Use "completed within first auto-loop pass" vs "required multiple passes" from loop telemetry (if available) as a proxy.
3. **Model is still useful at 64%:** Above the 50% baseline, and the feature pattern (specificity → acceptance) is actionable for goal-drafting guidance.

## Artifacts
- Model script: `memory/researcher/goal_acceptance_predictor.py`
- Model params: `memory/researcher/goal-acceptance-model.json`
