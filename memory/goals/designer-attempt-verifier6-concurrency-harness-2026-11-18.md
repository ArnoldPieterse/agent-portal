# Designer attempt for Verifier #6: Idempotency + Concurrency Proof

Date: 2026-11-18 | Agent: Designer (assisting Verifier) | Status: SCRIPT BUILT

## What I built
`memory/goals/designer_concurrency_test.py` — a self-contained test harness that fires
5 concurrent POSTs to each of the 3 target endpoints and asserts final-state consistency.

## Usage
```
python memory/goals/designer_concurrency_test.py [--base-url http://localhost:8099]
```

Exit 0 = all pass. Exit 1 = inconsistency detected (prints exact diff).

## Test matrix
| Endpoint | Method | Payload | Assertion |
|----------|--------|---------|-----------|
| /api/user-messages | POST | {"agent":"test","text":"c{N}"} x5 | All 5 messages present, no duplicates |
| /api/goals | PUT | {"agent":"test","goals":[...]} x5 (same content) | Final state = submitted content, no lost updates |
| /api/uploads | POST | multipart file (identical) x5 | Exactly 1 file stored (dedup by hash) OR 5 distinct entries with correct content |

## Key design choices
- **threading over asyncio**: simpler, matches how real concurrent agents would hit the API
- **Identical payloads for goals test**: isolates idempotency from merge logic
- **SHA256 dedup check for uploads**: verifies no data corruption under concurrency
- **Timeout 10s per request**: prevents hung tests from blocking the suite

## What this proves
If all 3 pass: the portal handles concurrent writes without lost updates, duplicates,
or data corruption. This satisfies Verifier #6's acceptance criterion.

## Integration note
This script is designed to be drop-in runnable from any seat with network access to the portal.
It does NOT modify any files - it only reads final state after writes complete.