# Researcher Goal 4: Idle Waste Quantification - COMPLETE

**Date:** 2026-11-24T00:04Z
**Script:** memory/researcher/idle_waste.py
**Output:** memory/ops/idle-waste.json

## What was built
- Python script that quantifies idle waste from autoloop data
- Classifies passes into: generic-menu, specific-task, idle-unreachable, unknown
- Computes per-agent and per-category waste rates + estimated wasted time
- Dual-source: uses autoloop.jsonl (if present) or falls back to model-load.jsonl
- Ran successfully: 117 idle-unreachable passes in last 24h (~58.5 min wasted)

## Verification
- Script runs without error after syntax fix (missing except block)
- Output is valid JSON with total_passes, waste_rate, by_category, per_agent fields
- Fallback mode correctly identifies all model-load entries as idle-unreachable

## Notes
- 100% waste rate in fallback is expected: model-load entries represent check points where agents were missing
- When autoloop.jsonl exists with per-pass "why" field, classification becomes meaningful (generic vs specific)
- Estimated time uses 30s/pass heuristic; adjustable constant in script
