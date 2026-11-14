# Designer finding — LIVE root index.html is NOT the v2 canonical (r62, 2026-11-14)

NEW file (propagates under skew). Supersedes the "Design lane: CLOSED" bottom-line of
`stamp-verify-r61-107cbd93-2026-11-14.md`: that verdict verified the v2 STAMP artifact, but the
served/root page was never re-pinned to it and has since drifted. Concrete byte evidence below.

## What is on disk right now (this seat, certutil + python md5)
| file | size | md5 (raw) | md5 (LF-norm) |
|---|---:|---|---|
| index.html  (workspace ROOT = served) | 68,549 B | 8fc29f19ac6f1a79e00ace5087542600 | 437b738739358532129980cf2d82e613 (67,576 B) |
| memory/designer/index_html_stamp_final_107cbd93.html (v2 canonical) | 69,888 B | 107cbd9357c85d209c76590bc4101d58 | same (file is LF-native) |
| memory/designer/index_html_black_5.html (old r19 canonical) | 67,681 B | 9c6b08e3d98355e632a72cb871d5b60d | 07ac2961e366f89780a08bb48a64e9d6 (66,716 B) |

The live root is a THIRD state: it matches NEITHER pin in raw or LF-normalized form. It is the OLD
r19 canonical (9c6b08e3) plus ~23 extra agent-editor lines (+868 B), and it contains NONE of the v2
design fixes. The root has also drifted away from its own r19 pin (9c6b08e3) since 22:0x.

## Marker grep — LIVE root vs v2 stamp (decisive)
| marker | LIVE root | v2 stamp |
|---|--:|--:|
| alert(     | 4 | 0 |
| confirm(   | 2 | 0 |
| @media     | 0 | 2 |
| --acc-strong | 0 | 5 |
| #panelDock | 0 | 1 |
| one-open-at-a-time | 0 | 1 |
| .toast     | 0 | 3 |

diff (unified, LF-normalized): 68 lines only-in-v2, 23 lines only-in-LIVE. Every LIVE-only line is an
OLD-version line that v2 replaced: `#send{background:var(--acc)}` (the 3.22:1 contrast defect),
`.seg button.on`/`.btn.pri` on --acc, `.aev .at{color:#6b7688}`, and the six alert()/confirm() calls
(agent-editor delete/name/model validation, Reset busy-guard banner, Reset confirm, counter-reset
fail alert). v2 swaps all of these for the .toast system + --acc-strong + #panelDock + 2 @media blocks.

## Consequence (why this matters to the open gate)
All six r19 defects are STILL LIVE on the served page: (1) token family = old dark, not v2;
(2) alert()/confirm() in flow x6; (3) no one-open-at-a-time / outside-click-close; (4) layout shift
on panel toggle (no #panelDock); (5) Send button 3.22:1 < 4.5 AA; (6) zero @media, 360px squeeze.
If Arnold runs his White-console pass now he is judging a page that does NOT reflect the v2 fixes,
and will re-report all six as open.

## Ask (not my call to make unilaterally — I do not write index.html)
1. Orchestrator/Builder: the v2 stamp (107cbd93 / 69,888 B) must actually be re-pinned to root via
   the sanctioned hash-gated one-shot BEFORE Arnold's console pass — otherwise that pass is invalid.
2. Or, if the live drift (the +23 agent-editor lines) is intended and newer than v2, Builder must
   RE-MERGE those onto the v2 base and I re-run the r19/r61 defect sheet against the new stamp.
3. Verifier: do NOT close AC-A2 on PID 23704 as "v2 verified" — the served page is not v2.

Bottom line: my r61 "lane CLOSED" was scoped to the artifact and I undersold it; the live page was
never updated. Design leg RE-OPENED pending one of the two re-pin/merge paths above. Re-run this sheet
whenever root index.html changes.

Owner: Designer. Basis: certutil + python md5 on all three files, marker grep, unified diff (LF-normalized).