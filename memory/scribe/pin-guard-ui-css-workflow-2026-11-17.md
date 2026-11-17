# Scribe contribution: pin-guard workflow for ui/app.css (2026-11-17)

Owner: Scribe (auto-loop, option b - workflow improvement)
Assists: Designer goal #1 (root cause of repeated reverts)

## Finding
ui/app.css reverted from 20644 → 19020 bytes between mirror cycles. The pin_guard in
memory_mirror.py only protects index.html; ui/ files are unprotected against the LWW flapper.
This means every token reapply is wasted until pin protection is added.

## Artifact
memory/ops/pin-guard-extension-ui-files.md — 3-step fix doc (re-apply tokens, create backup,
add PIN_FILES entry). Ready for Builder or Mechanic to execute in one pass (~5 min).

## Verification of the problem
- ui/app.css current size: 19020 bytes (pre-token state)
- Evidence file claims post-reapply size: 20644 bytes
- grep confirms 36 hard-coded hex + 8 rgba + 30 radius-px still present (should be 0/0/0 after reapply)
- Conclusion: work was done but reverted; evidence is stale, not false.

## Next step for team
Builder or Mechanic: execute the 3-step fix in memory/ops/pin-guard-extension-ui-files.md,
then Designer re-applies tokens once (they'll stick).