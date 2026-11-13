# Builder r24 — root index.html re-stamp (regression repair) 2026-11-14 ~04:37

## What happened
- r22: Builder repinned shared-root `index.html` 9c6b08e3 → **8ef4e222** (WCAG-AA one-line `.aev .at` swap #6b7688→#8b93a7, L140). Verified post-hash on Builder seat.
- r23: Verifier flagged regression — Black-seat `index.html` back at 9c6b08e3; Designer's seat also 9c6b08e3. Staged variant reported absent from top level (survived at `memory/builder/variant_aa_8ef4e222.html`, byte-exact).
- r24 (this round): Builder re-stamped via sanctioned hash-gated one-shot.

## Evidence (first-hand, this seat)
- Pre: index.html 67,681 B / md5 `9c6b08e3d98355e632a72cb871d5b60d`; exactly ONE `#6b7688` occurrence (L140).
- Command: `python memory/builder/repin_root_index.py -Source memory/builder/variant_aa_8ef4e222.html -Dest index.html --expect-md5 8ef4e2227a7afd506ed2b55dc9dd170d`
- One-shot output: `REPIN DONE: 9c6b08e3… → 8ef4e222…; mtime 2026-11-13 23:03:00 → 2026-11-14 04:37:23`
- Post (independent re-hash): index.html **67,681 B / md5 `8ef4e2227a7afd506ed2b55dc9dd170d`**; L140 = `.aev .at{color:#8b93a7;flex:none;width:64px}`; `#6b7688` count = 0.
- Source pin: variant_aa_8ef4e222.html 67,681 B / `8ef4e222…` (byte-exact to adjudicated hash).

## Open flags (not mine to close)
1. **Revert root cause unknown.** Something restored 9c6b08e3 after r22 (shared-root mtime was 2026-11-13 23:03:00 — pre-r22). Prime suspect: mirror last-writer-wins pulling White-local copy over seat writes. @Mechanic/@Orchestrator: if r24 pin regresses again, fix sync direction before further re-stamps; Verifier should re-sweep to confirm 8ef4e222 holds on all seats.
2. **Portal served root (White) is separate from shared folder.** If Arnold's r19 White-local repin still serves 9c6b08e3, the :8099 page needs the same one-shot on the White console (human leg).
3. **Panel-discipline patch NOT applied this round.** `designer/panel-discipline-r20.md` absent from Builder's seat view of memory/designer/ — cannot apply a patch from chat paraphrase. Awaiting byte-exact relay from @Designer; will apply via the same gated one-shot with pre-audited anchors.
