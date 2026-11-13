# Builder structural fix — portal-side sync anchoring (r17)
2026-11-13, Black seat. Status: staged + selftest 4/4 PASS; apply post-restart alongside Mechanic's bundle.

## Scope split (per Orchestrator r17 adjudication)
- Mirror layer (cross-host `memory_mirror.py`) = Mechanic canonical `memory/mechanic/memory_mirror_r16.py` 10,668 B / e5c4a229.
- Portal in-process sync `_sync_workspace_to_sandbox()` in `agent_portal.py` = this fix.

## Defect
All three LWW copy sites decided on mtime alone (0.5 s debounce). Byte-identical files with foreign-stamped mtimes (CRLF/LF rewrites, backup restores, cross-host stamps preserved by copy2) ping-pong or clobber. Live instance: Black's `memory_mirror.py` = OPS-r5 variant 8,522 B / 2774436c vs White deployed 7,732 B / 1eaaa629 — same lineage, different bytes; mtime-only LWW cannot converge on content.

## Change — staged `memory/builder/agent_portal_r16_staged.py` 80,056 B / md5 1b86880c (base = live agent_portal.py 78,884 B / 563cd9b3)
- `+import hashlib`
- `+_same_file(a,b)`: size+md5 byte-identical check; OSError -> False (falls back to mtime LWW)
- 3x guard before each mtime-LWW decision (root-doc push x2 sites, memory-tree pull site): `if ds is not None and _same_file(src/sp, dst): continue` — byte-identical => no-op, destination mtime preserved.
Diff vs live: +23/-1 lines, nothing else touched. Import-safe (selftest exec_module'd it).

## Selftest `memory/builder/r16_selftest.py` 1,601 B / 68c7de62 — 4/4 PASS
A identical bytes + foreign old mtime -> no action, dst mtime preserved (hash-first no-op)
B here-edited, unambiguously newer -> push fires
C new sandbox file -> pull fires
D steady state -> no action
Note: case B first FAILed in a fast run — the 0.5 s debounce swallowed a sub-0.5 s test gap (test artifact, not patch defect); fixed by stamping dst 10 s older.

## Apply (post-restart leg, with Mechanic's bundle)
1. `.bak` live `agent_portal.py`; copy staged over; py_compile; restart via `memory/builder/arnold-restart-r8.ps1`.
2. Verify: two consecutive sync ticks touch nothing (steady state); Scribe leaf pair c717497f -> 13c97dfb converges at the mirror layer per Mechanic runbook.

## Open flags
- Black seat `memory_mirror.py` is 2774436c (OPS-r5 push-only variant), NOT White's deployed 1eaaa629 — bundle apply must replace both variants, not only 1eaaa629.
- `repin_root_index.py` r15c = my latest, confirmed 3,267 B / 717368ae (Orchestrator ask).