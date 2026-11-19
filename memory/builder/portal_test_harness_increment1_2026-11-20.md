# Portal Test Harness - Increment 1 Evidence

Date: 2026-11-20
Goal: #9 Portal Test Harness

## What was built
`memory/builder/portal_test.py` (370 lines) - in-process test harness with 3 suites:

### Suite: api (14 tests)
- Fixture load + structure validation
- Route coverage (soft check vs agent_portal.py source)
- Status code sanity (no undocumented 5xx)
- Schema non-empty verification
- Critical endpoint existence (chat, history, agents, goals)
- Break detection (deliberately broken endpoint IS caught)
- Per-endpoint schema type validation
- Baseline integrity (md5 check)

### Suite: ui (20 tests)
- File existence for all 8 JS + 3 CSS modules
- Brace/paren balance per JS file (tolerance ±3 for regex/template edge cases)
- No empty CSS rules
- Component usage in core.js (createElement count <5 target)
- State module exists + wired
- Error boundary present
- A11y focus-visible rule

### Suite: integration (8 tests)
- agents.json valid (dict with "agents" list, >=1 entry)
- 7 critical endpoints exist in source

## Results
41/42 PASS (0.0s)
- 1 expected FAIL: component_usage:core.js (createElement=7, target<5) - known open item from Goal #1
- Break detection verified: test correctly flags a corrupted fixture entry

## Usage
```
python memory/builder/portal_test.py --suite api|ui|integration|all
python memory/builder/portal_test.py --suite all --live  # against running portal
```

Report auto-written to: memory/builder/test-report.md
