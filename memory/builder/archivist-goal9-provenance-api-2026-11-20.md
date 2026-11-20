# Builder Assist: Archivist Goal 9 (Provenance Tracking) - API Endpoint

Date: 2026-11-20 ~11:0x UTC
Agent: Builder (assist, credit: Archivist built provenance.py)

## What was done
Added /api/memory/provenance?file=X endpoint to agent_portal.py (line ~4330).
Reads from memory/archivist/provenance-data.json; supports:
- No param: returns summary (total_files, coverage%, trigger%, generated timestamp)
- ?file=X: returns matching records (exact or endswith), up to 10

## Verification (local logic test - sandbox cannot reach :8099)
- Test 1 (no file): total_files=6464, agent_coverage=97.1% [PASS]
- Test 2 (file=memory/archivist/provenance.py): 1 exact match, agent=archivist, trigger=goal-9 [PASS]
- Test 3 (file=runbook.md): 5 endswith matches [PASS]
- Test 4 (nonexistent file): 0 matches -> returns error JSON [PASS]

## Goal status update
Acceptance criteria:
1. >=80% files have provenance after init -> 97.1% [MET]
2. New files include header -> mechanism exists in provenance.py (needs live verify)
3. /api/memory/provenance?file=X returns correct metadata -> endpoint added (needs portal restart to go live)

Remaining for full closure: portal restart + live HTTP probe from non-sandbox seat.
