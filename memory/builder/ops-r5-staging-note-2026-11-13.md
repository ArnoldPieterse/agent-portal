OPS r5 staging note (Builder, 2026-11-13 ~20:3x local)
=====================================================
Purpose: durable, mirrored-tree copies of the post-r5 sync code, so the fix
is not held in a single seat's sandbox. Lands on all seats via the memory/
mirror (5-min tick / turn boundary).

Staged files (md5 verified at copy time, src == dst):
- memory/builder/agent_portal_ops-r5_staged.py   md5=563cd9b3  (source: seat agent_portal.py)
- memory/builder/memory_mirror_ops-r5_staged.py  md5=2774436c  (source: seat memory_mirror.py)

What they contain (content-verified 2026-11-13):
1. agent_portal section 3: pull back to canonical = memory/ leaves ONLY;
   TODO.md / MEMORY.md are PUSH-ONLY (stale whole-file rewrites with fresh
   mtime can no longer be LWW-pulled into canonical). New-only pull never
   overwrites an existing workspace file.
2. memory_mirror push_tree: strictly src-newer-only (ss.st_mtime > ds.st_mtime + MTOL);
   newer remote copies are skipped and audited via returned skipped list
   (logged as skipped_stale). No functional abs() mtime comparison remains
   (the two 'abs(' string hits in the file are docstring prose only).

Provenance: re-authored by Builder after the original r5 apply was observed
reverted in this seat; behavioral re-test 8/8 PASS incl. exact OPS r3 clobber
repro - see builder-ops-r5-retest-2026-11-13.txt (repo root).

NOTE: md5s differ from the originally recorded b2a299ef / c1f4699c because
this is a re-authored patch, not a byte copy. Verifier AC-A2 should check
behavior/content, not hash equality. The original memory_mirror fix also
persists at memory/mechanic/memory_mirror_fixed.py (md5 c1f4699c).

Apply (Arnold, White-local only): replace canonical agent_portal.py +
memory_mirror.py with these copies (or diff first), then restart portal
PID 1240 so the running process loads the exclusion. Until that restart,
the loaded code is whatever PID 1240 was launched from - seat copies prove
nothing about the live process.
