# Builder r45 closeout — ffa77423 lineage verification (Builder seat, first-party)

Date: 2026-11-14. Seat: Builder sandbox. All hashes md5.

## Verified facts (re-measured on this seat)
- `memory/builder/index_html_a6_b_a11y_candidate_ffa774230d8f354cbcdab640bd080b02.html` = **ffa774230d8f354cbcdab640bd080b02 / 69,707 B**; pinned copy `memory/verifier/index_html_a6_b_a11y_candidate_ffa77423...html` byte-identical on this seat.
- Line-diff vs `ec095107` base: **exactly one line, L141** — `.aev .at{color:#6b7688;flex:none;width:64px}` → `.aev .at{color:#8b93a7;flex:none;width:64px}`. Line counts 1015=1015, zero other changes.
- Independent re-derivation (base.replace `#6b7688`→`#8b93a7`) = ffa77423 byte-exact MATCH. Transform is exactly Designer's one-line a11y fix, nothing else.
- 9/9 surface post-checks PASS on ffa77423: filesBtn refs ==7; `alert(` ==0; `confirm(` ==0; panelToggles present; panelClose present; `#6b7688` absent (zero occurrences); `.aev .at{color:#8b93a7` rule present; `--acc-strong:#2f6fe0` def present; acc-strong mentions ==5 (1 def + 4 `var(--acc-strong)` refs). A4 `#panelDock` absolute intact.

## Endorsement
Builder endorses **ffa77423** as the single stamp-ready file for AC-A2 re-run + a11y in one pass. Lineage: 45323d09 (A4+A5) → ec095107 (A6+B, fixed anchors per `apply_a6_b_r44_fixed.py`) → **ffa77423 (+a11y L141)**. Each step byte-verified; earlier two candidates superseded for stamping purposes.

## Cross-seat flag for Orchestrator (bundle de-dup)
Two files named `index-pointer-addendum-r43.md` exist with different hashes: `memory/synthesis/` (ca4f6e45 / 2,291 B, Scribe) and `memory/archivist/` (8a69f329 / 2,031 B, Archivist). Both carry the SAME two pointer paths (`2026-11-14-r42-round-record.md` 9ebab4c4/2,380 B; `2026-11-14-r41-closeout.md` 614f1d9c/3,051 B) with different description text. Apply exactly ONE to `memory/synthesis/INDEX.md` or the batch double-applies (4 lines instead of 2). Suggestion: Scribe's (owns synthesis lane); delete/archive the other post-apply.

Builder executable lane: closed. Remaining = Arnold's human White-console leg + Orchestrator apply bundle.
