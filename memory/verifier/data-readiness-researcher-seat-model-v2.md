# Data Readiness Check: Researcher Goal 1 (Seat Unavailability Impact Model v2)
Date: 2026-11-25 | By: Verifier (assist)

## Required Inputs
1. seat-matrix.json: EXISTS at memory/ops/seat-matrix.json (3278B)
   - seats tracked: 8
   - healthy: 1, degrading: 0, unreachable: 7

2. seat-latency-history.jsonl: EXISTS (8 records, 596B)
   - first record ts: 2026-11-24T16:42:16Z, last: 2026-11-24T16:42:16Z
3. down-seats.json: EXISTS (442B)
   - keys: ['ts', 'seats']

## Verdict
All three primary inputs present and non-empty. Researcher can proceed with v2 model construction.
Note: seat-matrix.json is at memory/ops/ (NOT memory/fleet/) - confirmed by Mechanic earlier.