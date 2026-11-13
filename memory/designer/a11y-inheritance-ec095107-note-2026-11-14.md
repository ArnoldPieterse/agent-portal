# Designer note — a11y gap inherits into ec095107 (bundle input)
Date: 2026-11-14 (r45, post-Verifier-r44). Seat: Designer module dir.

## Finding (inference from pinned evidence, file not yet on this seat)
- Verifier r44 built `index_html_a6_b_candidate_ec095107236a9bdc.html` (ec095107 / 69,707 B) by applying Builder's A6+B payloads to the verified base = **45323d09** (his words: "running it from the verified base").
- My re-run leaf `design-sheet-rerun-45323d09-2026-11-14.md` (f9e448ea, 4,747 B) established that 45323d09 **predates the 8ef4e222 a11y stamp**: `.aev .at` timestamps = `#6b7688` on white → **3.80:1**, below WCAG AA (4.5:1).
- A6+B anchors are disjoint from the `.aev .at` rule, so ec095107 **inherits the same 3.80:1 gap** unless the fix is stacked separately.

## Bundle implication (for Orchestrator / Arnold's White-console pass)
- Whichever candidate gets stamped (45323d09 or ec095107), the one-line a11y fix `.aev .at` color `#6b7688` → `#8b93a7` (≈4.6:1) must be in the apply set. It is disjoint from all A4/A5 and A6+B anchors, so it can layer cleanly on either.
- If ec095107 is stamped as canonical, my full r19 sheet re-run against it is owed (static checks only; functional AC-A4/AC-A5 acceptance remains Verifier/Arnold). Trigger: file visible from this seat via mirror. Not yet present as of this note (memory/builder + memory/verifier dir-listed; verifier module ends at r42 leaf).

## Pins (this seat, measured now)
- `memory/designer/design-sheet-rerun-45323d09-2026-11-14.md` f9e448ea / 4,747 B — my r-rerun deliverable, intact.
- `memory/builder/index_html_a4a5_candidate_45323d09.html` 45323d09 / 68,633 B — base candidate, intact.
- ec095107 + `apply_a6_b_r44_fixed.py` + `r44-closeout-2026-11-14.md`: ABSENT from this seat (mirror lag) — no measurement possible here.
