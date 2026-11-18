# Builder r44 — A6+B anchor bug confirmed first-party; ec095107 adopted as canonical re-run target

**Seat:** Black. **Date:** 2026-11-14. **Trigger:** Verifier r44 flag that `apply_a6_b_r42.py` fails on its own declared base.

## Bug confirmed (first-party, my seat)
- `apply_a6_b_r42.py` uses single-line anchors for the two confirm handlers:
  - `old_del` (L81) — **0 occurrences** in the pinned base `45323d09`. Real handler is multi-line:
    `x.onclick=async e=>{e.stopPropagation();\n      if(!confirm(`Delete ${a.name}?`))return;\n      await fetch("/api/agents/"+a.id,{method:"DELETE"}); refresh();};` (~L328-330)
  - `old_rst` (L88) — same class: base has `...then reset."); return; }\n  if(!confirm("Reset conversation?...") )return;\n  try{` (~L922-925); my anchor assumed a single space, not newline+indent.
- Net effect: `sub1()` asserts `count==1`, gets 0 → script **aborts before writing** (write is last, L109). Nothing was ever persisted by the r42 script — matches Verifier's "script exists but never run".

## Fixed transform re-verified byte-exact
- Ran `memory/verifier/apply_a6_b_r44_fixed.py` (multi-line anchors; **my replacement payloads verbatim**) on pinned base 45323d09:
  - 9/9 post-checks PASS (no alert/, no confirm/, two @media, toast fn, A4 panelDock absolute intact, A5 --acc-strong intact, div balance 61/61, delete arm, reset arm).
  - Output **`ec095107236a9bdcf514baaf4e9b4abd` / 69,707 B** (base 68,633 B).
- Idempotency: re-run reproduces identical md5; builder/ and verifier/ candidate copies **byte-identical**.

## Lane decision
- `apply_a6_b_r42.py` is **superseded** by `memory/verifier/apply_a6_b_r44_fixed.py` for the A6+B item (content unchanged, anchors corrected).
- **AC-A2 re-run target = `ec095107`, not 45323d09** — concurs with Verifier r44. Functional acceptance (live leg + stamp) remains Arnold's White-console pass; Designer's a11y note (`.aev .at` 3.80:1, pre-8ef4e222 lineage) is disjoint from all A6+B anchors and stacks cleanly if ec095107 gets re-pinned canonical.

## Pins (this seat)
- base `memory/builder/index_html_a4a5_candidate_45323d09.html` = 45323d09… / 68,633 B
- cand `memory/builder/index_html_a6_b_candidate_ec095107236a9bdc.html` = ec095107… / 69,707 B
- pin `memory/verifier/index_html_a6_b_candidate_ec095107236a9bdc.html` = ec095107… (byte-identical)

Builder A6+B lane CLOSED — reproducible + pinned; nothing further agent-executable from this seat.
