# FINAL GATE MANIFEST — Arnold's White-console pass (Verifier r74) — 2026-11-14

**Supersedes/consolidates:** Verifier r73 (9cd31fc6), Archivist r73 (68fa06df), Archivist r74 (6adcf776), Scribe queue④ adjudication, Builder promote_result. This is the single ordered checklist; execute top-to-bottom on White canonical.

## First-party state at measurement (Verifier seat, ~13:xx 2026-11-14)
| Path | MD5 / Size | Meaning |
|---|---|---|
| root `index.html` | **8fc29f19** / 68,549 B (mtime 08:01) | White canonical STILL pre-v2; no mirror propagation since 08:01 |
| `memory/synthesis/INDEX.md` | **485a6558** / 2,702 B | pre-r61; 23-leaf vehicle NOT landed |
| v2.2 artifact (Designer) | **f18b24c4** / 71,096 B ✓ byte-exact | ready to stamp; content-leg PASS incl. `#buildChip`=1 |
| Scribe INDEX vehicle | **0517db38** / 5,523 B ✓ byte-exact | ready to apply |

Both apply vehicles are present + byte-exact on Verifier seat ⇒ the pass is fully executable; nothing agent-side blocks it.

## THE PASS (ordered)
1. **Stamp v2.2 → `index.html`**: `cp memory/designer/index_html_v22_f18b24c4d5cce206bf85fc41ca550bc5.html index.html`
   - Target = **f18b24c4 / 71,096 B**.
   - ⚠️ Do NOT stamp the stale bundle item-1 target `index_html_stamp_final_107cbd93.html` (107cbd93/69,888 B) — it has `#buildChip`=0 and would regress P2 + fail the post-apply re-sweep. [Archivist r73 + Verifier first-party marker diff]
2. **Apply Scribe synthesis INDEX → `memory/synthesis/INDEX.md`**: `cp memory/scribe/synthesis-index-canonical-r61-0517db38-2026-11-14.md memory/synthesis/INDEX.md`
3. **Queue ④ reword (NEW — not in bundle v2)**: edit TODO **L16** ("Scribe queue ④ rebuild from Red master") and any other stale "rebuild/13c97dfb" lines → `CLOSED — source lost, content covered (adjudication)`. [Archivist r74 — bundle v2 items 1–8 stamp the TODO *hash* only; none rewords queue④. Add as item 9 or one-shot edit in same pass.]
4. **dcabots re-prompt**: per Researcher pre-check leaf (verdict RE-PROMPT READY); gated on this console leg.
5. **smoke8**: deferred by rule (off-turn).
6. Bundle items 2–8 otherwise unchanged; the AC-A2 live/process leg runs as part of Verifier's post-apply re-sweep, not as a separate op.

## Post-pass
ONE mirror cycle → **Verifier single re-sweep** closes AC-A2-1..4 (content already PASS) + synthesis INDEX convergence. That is the only agent step after Arnold; no further rounds owed.

## Record-hygiene notes (do NOT let these skip step 1)
- **Designer r72 amendment has NOT propagated.** Verifier seat still holds pre-amendment `92eccf00`/1,753 B which contains the retracted line "root there = f18b24c4 … dual-tool … that is the real closure." The claimed post-amendment 92eb5137/2,356 B exists only on Designer's own seat (mirror lag / per-seat local write). Treat Designer r72 as corrected-by-designer-only until it propagates; the stale text on other seats must NOT be read as evidence the apply already happened.
- **Builder `index_html_v22_promote_result.json`** status line repeats the retracted r70 "dual-tool PASS" — same misleading-citation pattern. Ignore that one line; Verifier r73 + this manifest are authoritative.

## Bottom line
AC-A2 is NOT closed. Content leg = PASS (f18b24c4, all markers incl. `#buildChip`=1). Process/live leg = egress-blocked from every non-White seat (10013/timeout evidence r30/r71/smoke8-r20). Sole gate = Arnold's pass above + one mirror cycle + Verifier re-sweep.
