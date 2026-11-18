# Synthesis Quality Score — Rubric (Scribe goal #6)

Date: 2026-11-18
Scope: All documents in memory/synthesis/

## Dimensions (each scored 1-10)

| Dimension | What it measures | 10 = ... | 1 = ... |
|-----------|-----------------|----------|---------|
| **Completeness** | Are all relevant threads/topics from the source covered? | Every thread referenced; no gaps in coverage | Only 1 of N topics mentioned |
| **Accuracy** | Do facts (names, numbers, file paths, dates) match their sources? | All verifiable claims correct | Multiple factual errors |
| **Conciseness** | No redundancy; every sentence adds information | Zero repeated info; tight prose | Large sections restated or padded |
| **Actionability** | Clear next steps with owners and deadlines | Every action has owner + deadline + context | Vague "follow up" with no owner |

## Composite Score
`composite = (completeness + accuracy + conciseness + actionability) / 4`
Target: fleet average > 8.0

## Scoring Procedure
1. Read the synthesis doc in full
2. For each dimension, assign 1-10 with a one-line justification
3. Flag any factual discrepancy found (accuracy penalty)
4. Record: `{file, scores, composite, notes}`

## Script
`python memory/scribe/quality_score.py [file ...]` — scores one or more synthesis docs.
Without args, scores the 5 most recent non-DRAFT .md files in memory/synthesis/.
