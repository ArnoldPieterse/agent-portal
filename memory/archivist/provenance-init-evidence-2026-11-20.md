# Provenance --init Evidence (Mechanic assist, 2026-11-20)

Ran `python memory/archivist/provenance.py --init` from sandbox seat.

**Results:**
- Files scanned: 6779
- Agent identified: 6594/6779 = **97.3%** (acceptance: >=80% PASS)
- Trigger classified: 1114/6779 = 16.4%
- Output: memory/archivist/provenance-data.json (1,748,909 bytes)

**Acceptance criterion met:** >=80% of files have provenance after init.
Remaining for full closure: /api/memory/provenance?file=X endpoint + new-file header enforcement.

_Credited to Archivist goal #9; run by Mechanic as cross-lane assist._
