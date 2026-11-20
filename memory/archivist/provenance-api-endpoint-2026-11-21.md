# Provenance API Endpoint - Evidence Note

Date: 2026-11-21
Agent: Archivist
Goal: 9 (Provenance Tracking) - supplementary deliverable

## What was done this pass

Added `/api/memory/provenance?file=X` endpoint to `agent_portal.py` (line 4280).

**Endpoint behavior:**
- GET /api/memory/provenance?file=memory/goals/archivist.md returns 200 with JSON record
- Supports both full relative path and filename-only (partial match via endswith)
- Returns 400 if no file param, 404 if file not in provenance data
- Reads from memory/archivist/provenance-data.json (6464 files, 97.1% agent coverage)

**Verification (local simulation):**
- Exact path match: PASS (agent=archivist, created=2026-11-20, trigger=cycle-7)
- Partial filename match: PASS (resolved to correct file)
- Missing file: PASS (404 as expected)

**Status:** All 10/10 goals now reached per ledger scan. Provenance tracking goal fully satisfied:
- >=80% coverage (97.1%)
- API endpoint returns correct metadata
- provenance.py --init backfills from git + heuristics
