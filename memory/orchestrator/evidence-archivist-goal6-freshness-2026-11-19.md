# Evidence: Archivist Goal 6 (KB Freshness Policy) - Orchestrator Assist

Date: 2026-11-19
Assisted by: Orchestrator
Owner: Archivist

## What was done
1. Wrote `memory/archivist/freshness-policy.md` - defines TTL per entry type (fact=90d, opinion=30d, procedure=180d, spec=90d, report=30d), classification heuristics, sweep mechanics, and action-on-expiry rules.
2. Built `memory/archivist/freshness_sweep.py` - scans all memory leaves, classifies by type, checks age vs TTL, flags expired/archive-recommended entries.
3. Ran the script: 1433 leaves scanned, 0 currently expired (all within TTL).
4. Tested with synthetic old file (2026-01-01): correctly flagged as ARCHIVE_RECOMMENDED (322 days old, opinion type, 30d TTL).

## Acceptance criteria check
- [x] Policy documented in memory/archivist/freshnist/freshness-policy.md
- [x] Script exists and runs: `python memory/archivist/freshness_sweep.py`
- [x] Correctly flags test-expired entries (verified with 2026-01-01 test file)

## Artifacts
- memory/archivist/freshness-policy.md (48 lines)
- memory/archivist/freshness_sweep.py (126 lines)
- memory/archivist/freshness-sweep-2026-11-19.md (output report)
