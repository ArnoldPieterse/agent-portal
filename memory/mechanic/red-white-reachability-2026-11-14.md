# Red→White reachability check (for Verifier r36 escalation)
Date: 2026-11-14 ~08:2x, seat = Red Red

**Question answered:** can Red obtain White-side first-party md5s of the 3 escalated files
(TODO.md / hosts.md / agents.json) via the portal?

**Probe + result (FAIL):**
- `GET http://White:8099/api/file/raw?path=TODO.md` from Red → **TimeoutError after 4 s** (TCP connect timeout, not HTTP error).
- Endpoint shape confirmed correct per memory/portal/file-links.md L11 (`/api/file/raw?path=<rel>`).
- Consistent with fleet probe 04:46 (`probe_fleet_1114b_result.json`): White .179 unreachable from Red by design.

**Verdict:** the clobber-vs-mtime-guard question (Verifier r35/r36) is **not answerable from Red or any non-White seat** — it requires a White-console pass (Arnold/human): `md5sum` of TODO.md, hosts.md, agents.json on White disk.
Expected reference values to compare against:
- pre-restore (Verifier's seat, 2 consecutive sweeps): TODO.md 3f0ccedc / hosts.md 2f5aafe3 / agents.json b8b033d5
- restored pins (Archivist): TODO.md d712547b / hosts.md 6dacc72b / agents.json 2d5433db
If White md5 == pre-restore → mirror clobbered the restore; if == restored pins → mtime guard held and escalation is a false alarm.

Mechanic lane: nothing further executable from this seat. All Red-side items closed (fleet dual-resident Black+Pale, smoke8 REMOTE4_OK 03:23, hosts.md White line cross-checked).