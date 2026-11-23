# Mechanic assist: Builder goal #8 (Post-Remediation Auto-Report) - data layer

Date: 2026-11-24
Contributor: Mechanic (ops engineer)
Goal owner: Builder

## What was built
`memory/builder/remediation_extractor.py` - scans decision-log.jsonl for completed
remediation cycles and outputs structured JSON ready for post_mortem.py consumption.

## Verification
- Ran against real memory/ops/decision-log.jsonl (17 entries)
- Extracted 5 remediation cycles: 2 OOM recoveries + 3 chaos drills
- All 5 have complete fields: what_broke, root_cause, fix_applied, time_to_recovery_s, lessons_learned
- Handles both `timestamp` and `ts` field names (schema drift in log)
- Filters to successful completions only (success=true or recovered=true)

## How Builder uses it
```python
from memory.builder.remediation_extractor import extract_cycles
cycles = extract_cycles("memory/ops/decision-log.jsonl")
# Each cycle dict has all 5 sections needed for the post-mortem template
```

Or CLI: `python memory/builder/remediation_extractor.py --output /tmp/cycles.json`

## Remaining work for Builder
- Build post_mortem.py that imports extract_cycles and renders markdown
- Template: ## What Broke / ## Root Cause / ## Fix Applied / ## Time to Recovery / ## Lessons Learned
- Output path: memory/ops/post-mortems/<date>-<agent>.md
