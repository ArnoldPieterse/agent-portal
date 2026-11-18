# Goal 4 - API Contract Tests (partial progress)
Date: 2026-11-18
Status: PARTIAL - static validation passes, live test blocked by port

## What was done this pass
Fixed static mode bug in contract_test.py:
- Bug: `spec.get("schema", {})` looked for nested key that doesn't exist; schemas are stored directly as values
- Fix: validate the spec dict itself, handle oneOf variants separately
- Result: `--static` now passes 31/31 endpoints (was failing all 31)

## Remaining for full closure
- Live portal test (`contract_test.py` without --static) requires port 8099 accessible
- Port blocked since cycle 2 (noted in goal 2 evidence too)
- When port becomes available: run `python memory/verifier/contract_test.py` and confirm all 31 pass

## Evidence of static pass
```
[STATIC MODE] Validating schema structure (no live requests)
  PASS: all 31 schemas structurally valid
Summary: 31 endpoints covered, 0 structural errors
```