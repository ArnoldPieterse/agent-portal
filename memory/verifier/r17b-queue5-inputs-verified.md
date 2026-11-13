# Verifier r17b — post-restart verify-pass inputs, byte-pinned (2026-11-13)
Seat: Verifier sandbox. All hashes first-party md5[:8] read from this seat's disk; cross-checked vs records of the round.

## 1) Degradation re-probe (fresh, this round)
- loopback :8099 socket -> BLOCKED (host not in sandbox allowlist). Same as r15/r16.
- `tasklist` -> "The user name or password is incorrect". Same signature as r15 note.
=> process-level AC-A2 still NOT runnable from this seat; sign-off will be on relayed console evidence (PID + CreationDate) per r15/r16 adjudication. No restart has occurred: LIVE PLAN queue ① (Arnold runs `arnold-restart-r8.ps1` on White console) still open, no relayed PID/CreationDate in TODO.md.

## 2) Queue-⑤ apply inputs — all pins EXACT
| file | size / md5[:8] this seat | record | match |
|---|---|---|---|
| agent_portal.py (live base) | 78,884 B / 563cd9b3 | r17 anchor 563cd9b3 | EXACT |
| memory/builder/arnold-restart-r8.ps1 | 2,429 B / 2490793a | r15/r16 intact pin | EXACT |
| memory/builder/repin_root_index.py (r15c) | 3,267 B / 717368ae | r16b White record | EXACT |
| memory/mechanic/memory_mirror_r16.py | 10,668 B / e5c4a229 | r17 canonical bundle | EXACT |
| memory/mechanic/bundle-review-r16-2026-11-13.md | 4,341 B / fbce871b | r17 runbook | EXACT |
| memory/designer/post-restart-verify-r16.md | 1,664 B / 79237705 | r16b intact pin | EXACT |

## 3) Builder re-scoped structural fix — LANDED (post-dates r17 sweep; new files propagate) and VERIFIED
- `memory/builder/structural-fix-r17.md` 2,448 B / 5e3305fc (mtime 22:19:36, after the r17 lane-closure sweep that logged "no artifact landed" — that log predates propagation; discrepancy resolved).
- `memory/builder/agent_portal_r16_staged.py` = 80,056 B / **1b86880c** — EXACT match to note's claim; base = live 563cd9b3 confirmed.
- Diff vs live: exactly **+23/-1**, content matches description: `+import hashlib`; `_same_file()` (size+md5, OSError->False fallback); guards at all three mtime-LWW decision sites (SYNC_LWW push, git-allowlist push, memory-tree pull).
- py_compile on staged: CLEAN.
- Independent semantic re-test (function extracted verbatim into isolated harness, temp trees only):
  - Builder's 4 cases w/ documented case-B re-stamp: **A no-op / B push / C pull / D steady = 4/4 PASS** -> his "selftest 4/4" claim reproduced.
  - Discriminating case E (byte-identical src+dst, src mtime stamped +10 s newer): PATCHED = no-op, dst mtime preserved; LIVE/unpatched = PUSH fires. => guard demonstrably fixes the described ping-pong/clobber defect, not cosmetic.
- Caveats: (a) full-module import fails on THIS seat at module level (`_find_sandbox_dir()` walks C:\Users -> PermissionError here); pre-existing behavior untouched by the +23/-1 diff, works under White console context — hence function-extraction method. (b) `memory/builder/r16_selftest.py` on this seat = 1,288 B / 0d5aef93 vs note's revised claim 1,601 B / 68c7de62 — this seat holds the PRE-revision copy (no case-B re-stamp); consistent with existing-file edits LWW-skipping propagation, not a patch defect. Revised behavior reproduced in harness instead.

## 4) Residual record gap (non-blocking)
- `memory/verifier/lww-clobber-evidence-2026-11-13.md` on this seat = pre-correction 2,158 B / 54082935; r17 records corrected leaf 3,013 B / 571c3f44. Addendum never reached this seat (same existing-file-edit gap). Queue ⑤ not blocked (bundle already adjudicated on e5c4a229); cite White canonical for the corrected evidence.

## Verdict
All post-restart verify-pass inputs byte-pinned and Builder's re-scoped fix independently verified (hash, diff, compile, regression + discriminating tests). Open item unchanged and NOT mine to unblock: queue ① human leg (Arnold) -> relayed PID+CreationDate -> Verifier signs process-level AC-A2 (expect new PID != 1240, CreationDate > agent_portal.py LastWriteTime at apply, single :8099 listener) + Designer design-leg checks, one pass.
