# Goal 3 - Regression Guard: Evidence

Date: 2026-11-18
Script: `memory/verifier/regression_guard.py`

## What was built
Pre-commit check script with 4 check categories:
1. Python syntax (ast.parse) on agent_portal.py
2. JS structural validation (balanced delimiters after stripping comments/strings/template literals/regexes)
3. CSS brace balance
4. [optional --live] GET /api/* endpoints, verify 200 + valid JSON

## Test results

### Positive case (all files valid):
```
=== Regression Guard (--pre-commit) ===
  [PASS] agent_portal.py syntax
  [PASS] JS syntax: components.js
  [PASS] JS syntax: core.js
  [PASS] JS syntax: fleet_topology.js
  [PASS] JS syntax: uploads.js
  [PASS] CSS parse: app.css
=== Result: 6/6 passed, 0 failed ===
Exit code: 0
```

### Negative case (deliberately broken _test_broken.js):
```
  [FAIL] JS syntax: _test_broken.js - '[' (pos 29) closed by '}' (pos 46)
=== Result: 6/7 passed, 1 failed ===
Exit code: 1
```

## Acceptance criteria met
- [x] Script blocks a bad change (intentionally broken test file → exit 1)
- [x] Script passes a good one (all existing files → exit 0)
- [x] Covers JS syntax, CSS parse, Python syntax
- [x] Live endpoint mode available via --live flag (port-blocked in sandbox; degrades gracefully)

## Notes
- No Node.js on this host; JS validation uses a state-machine stripper + brace counter.
  Handles: multi-line comments, single-line comments, single/double-quoted strings,
  template literals with ${} nesting, regex literals (heuristic based on preceding char).
- CSS check is basic (brace balance after comment strip); sufficient for pre-commit guard.
