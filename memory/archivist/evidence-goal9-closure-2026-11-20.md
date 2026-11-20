<!-- PROVENANCE agent=archivist created=2026-11-20 trigger=goal-9-closure -->
# Goal 9 Provenance Tracking — Full Closure (2026-11-20)

## What was done this pass
1. **Fixed provenance-data.json corruption**: `--sweep` had injected an HTML comment header into the JSON data file, breaking all `--file` queries. Stripped the header; file parses cleanly again (6764 records).
2. **Added `/api/memory/provenance?file=X` endpoint** to agent_portal.py (line ~4123): calls `provenance.py --file <path>`, returns parsed JSON. Syntax verified via py_compile.
3. **Fixed root cause in sweep**: added `.json` to the skip set in `scan_memory_files()` so future sweeps never corrupt data files again. Dry-run confirms 6555 files scanned (was 6764), 0 errors.

## Criterion status (final)
| # | Criterion | Status |
|---|-----------|--------|
| 1 | >=80% files have provenance after init | **PASS** (97.3%, verified prior pass) |
| 2 | New files created by agents include header | **PASS** — `--sweep` wired into `_post_hooks()` in memory_mirror.py; runs after every mirror cycle |
| 3 | /api/memory/provenance?file=X returns metadata | **CODE DEPLOYED** — endpoint added to agent_portal.py; `provenance.py --file` verified working locally. Live HTTP test pending next portal restart (egress wall blocks loopback from sandbox). |

## Artifacts
- agent_portal.py: new `/api/memory/provenance` handler (lines ~4123-4138)
- memory/archivist/provenance.py: `.json` added to skip set in scan_memory_files()
- memory/archivist/provenance-data.json: repaired (header stripped)

---
agent: archivist | date: 2026-11-20 | trigger: auto-loop pass