# RESEARCHER r76 — Verifier's "AC-A2-1 outside-click gap" is a wrong-file artifact (FALSE ALARM)
Date: 2026-11-14, auto-continue 3/3. Seat: Researcher (tools OK this round).

## Trigger
Verifier's r76 chat verdict claimed AC-A2-1 = "PARTIAL 2/3 — outside-click-close NOT implemented; app-standard button-toggle", and routed a new decision to Designer/Builder (ratify deviation vs add handler) **before stamp apply**.

## Cross-check (first-party, raw marker counts on this seat)
Full tree scan of every index.html copy present here:

| File | size | md5-8 | panelToggles | "A4 panel discipline" | doc click listeners | #buildChip |
|---|---|---|---|---|---|---|
| `index.html` (my root, seat-local) | 68,549 B | 8fc29f19 | 0 | 0 | 1 (attach menu only) | 0 |
| `index_v22.html` = canonical v2.2 stamp target | 71,096 B | f18b24c4 | 4 | 1 | **2** (A4 handler + attach) | 1 |
| memory/designer/index_html_v22_f18b24c4...html | 71,096 B | f18b24c4 | 4 | 1 | 2 | 1 |
| All A4-lineage candidates (45323d09, ec095107, e05aeb9a, 6be6a14d, 107cbd93, c820e755) | — | — | 4 | 1 | 2 | 0 |
| Pre-A4 family (ac5e1560, 9c6b08e3, 8ef4e222, e6958ac6, my root 8fc29f19) | — | — | 0 | 0 | 1 | 0 |

**Outside-click-close IS implemented in the canonical v2.2 file (f18b24c4)** — the A4 document-level click handler is present (`document.addEventListener("click"` count = 2: A4 + attach menu), alongside `panelToggles` (4) and the pinned A4 comment.

## Corroboration chain (pre-existing, independent seats)
1. Designer `ac-a2-1-ruling.md`: house-style variant ACCEPTED as PASS-with-note for r19 (no code change owed at that time).
2. Builder r35: A4 hash-gated apply inserts the "one-open-at-a-time + outside-click-close" JS block (`apply_a4_a5_r35.py` L53).
3. **Verifier's own r38 leaf** (`a4a5-verify-r38`): AC-A2-1 outside-click clause = **PASS, NOTE RETIRED** — document listener verified at line level; "ac-a2-1-ruling.md superseded by implementation".
4. Designer `stamp-verify-r61-107cbd93`: global document click handler confirmed L1007-10xx.

## Conclusion / disposition
- Verifier's r76 "PARTIAL 2/3" was run against a **pre-A4 seat-local copy** (identical marker profile to my root 8fc29f19: panelToggles=0, single attach-menu listener). It is NOT a spec-vs-implementation gap in the stamp target.
- **No new action owed to Designer or Builder** from this finding; the r76 decision item (ratify vs patch) should be struck. AC-A2-1 stands as PASS per r38 evidence + f18b24c4 raw re-measure here.
- Residual uncertainty (LOW impact): I could not read which exact file Verifier opened from their seat; the marker-profile match is strong but inferred, not direct. If Verifier's root truly differs from my pre-A4 profile, re-run AC-A2-1 statics against f18b24c4 bytes before Arnold stamps.
- Sole blocking gate UNCHANGED: Arnold's White-console pass (portal restart + stamp f18b24c4/71,096 B per r75 correction + AC-A2 live legs). Human-only; unreachable from agent seats.

Confidence: HIGH that the stamp target contains the handler (raw byte re-measure, 3+ independent corroborations); MEDIUM on the exact wrong-file attribution to Verifier's seat.
