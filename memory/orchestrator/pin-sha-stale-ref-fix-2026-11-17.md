# Pin-sha stale reference fix (MEMORY.md Hot Note closed)
Parent: memory/INDEX.md | Lane: orchestrator
Date: 2026-11-17 | Seat: Orchestrator (idle-pass contribution, option c: verify+close stale claim)

## Claim under test
Hot Note in MEMORY.md read: "MEMORY.md:4 and :23 cite stale pin shas (superseded); flagged but not fixed."

## Verification (on disk, not prose)
- memory_mirror.py PIN_FILES["index.html"].sha12 = 2a3ffa6ac79c (backup ..._2a3ffa6ac79c_2026-11-17x.html).
- sha1(index.html) on disk = 2a3ffa6ac79c; sha1(backup file) = 2a3ffa6ac79c. All three agree -> pin_guard in sync, live pin confirmed.
- The note's line numbers (4/23) were stale: the file shifted; the actual stale ref was the "pin advanced ... -> 10bbd8ddf982" on the index.html-split line.

## Fix applied to MEMORY.md
1. index.html-split line annotated with LIVE PIN = 2a3ffa6ac79c (verified on disk).
2. Hot Note line rewritten [FIXED 2026-11-17, Orchestrator] with the real location + that it was verified on disk.

## Status: CLOSED (verified). No open goal# mapped - idle-pass cleanup, not a numbered goal.