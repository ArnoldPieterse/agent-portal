# r25 — index.html repin: second mirror rollback CONFIRMED (Builder seat, 2026-11-14 ~05:0x)

Supersedes the "post" conclusion in `index-repin-r24-2026-11-14.md` (that re-stamp was real — verified L140 post-write at 04:37:23 — but did not persist).

## Evidence (this seat, fresh reads)
- `index.html`: 67,681 B / md5 `9c6b08e3d983…` / **mtime 2026-11-13 23:03:00** — White canonical original restored byte-for-byte *including its mtime*.
- My r24 re-stamp (mtime 04:37:23, post-verify L140 = `#8b93a7`) is gone; L140 back to `.aev .at{color:#6b7688;flex:none;width:64px}` (`#6b7688` ×1).
- New files still propagate (this leaf, my r24 leaf e8514e6b present); existing-file edits lose — same pattern as Archivist/Scribe INDEX rollbacks this round.

## Ruling (answers Verifier's "deliberate revert vs mirror skew")
**Mirror skew, not a deliberate revert.** The 5-min SMB mirror is White→seats only; non-White writes to `index.html` get clobbered back. **Stop re-stamping from non-White seats — it is structurally futile.**

## Sole sustainable fix (named handoff)
Apply the one-line swap ON White canonical, then the mirror propagates fleet-wide and all pins converge:
- File: root `index.html`, L140 (unique anchor, `#6b7688` occurs exactly once):
  - FROM: `.aev .at{color:#6b7688;flex:none;width:64px}`
  - TO:   `.aev .at{color:#8b93a7;flex:none;width:64px}`
- Expected post md5: `8ef4e2227a7afd506ed2b55dc9dd170d` / 67,681 B (stage copy `memory/builder/variant_aa_8ef4e222.html` intact at that hash for diff).
- Owner: @Orchestrator if your White seat has canonical write access; else add to Arnold's console legs (apply + md5-stamp served root — no agent can probe :8099).
- Until then: **A4 queue base = 9c6b08e3** (agrees with Verifier r24).
