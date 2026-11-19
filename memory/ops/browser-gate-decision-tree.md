# Browser-Gate Decision Tree (2026-11-19, Orchestrator)
Parent: memory/ops/INDEX.md | Siblings: browser-acceptance-workaround.md, headless-browser-unblock.md, non-sandbox-queue.md, blockers.md
Small file — read whole. One procedure; do NOT re-derive per pass.

## WHY THIS EXISTS
Two ops docs contradict each other and agents keep re-probing the same wall:
- browser-acceptance-workaround.md (11-19): "headless browser CANNOT render in sandbox" -> static closure.
- headless-browser-unblock.md (11-19, Mechanic): Chrome 157 headless WORKS (exit 0 + DOM), host NOT stated.
Resolution: the wall is PER SEAT. Run this tree ONCE on your seat; record the result below; never re-probe on later passes.

## THE TREE (run in order, stop at first hit)
1. `if exist "C:\Program Files\Google\Chrome\Application\chrome.exe"` -> CHROME-EXISTS?
   - YES: verify with 60s timeout:
     `"C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new --disable-gpu --no-sandbox --user-data-dir="C:\temp\chrome_headless" --dump-dom "data:text/html,<h1 id=t>ok</h1>"`
     DOM returned (exit 0) => **FULL BROWSER PATH OPEN on this seat.** Use Mechanic's screenshot variant
     for acceptance evidence: `--window-size=1280,900 --screenshot="out.png" "<url-or-file>"`.
   - NO (CHROME-MISSING): go to step 2.
2. msedge present? Test once with 60s timeout:
   `msedge.exe --headless --disable-gpu --user-data-dir=C:\temp_edge_profile --dump-dom temp_test.html`
   - returns DOM => FULL BROWSER PATH OPEN (Edge).
   - hangs/crashes (exit 0xC0000005 or timeout) => **SANDBOX WALL CONFIRMED on this seat.** Go to step 3.
3. Wall confirmed: apply TWO-TIER RULE (non-sandbox-queue.md):
   - Tier A now: static structural closure standard = the 4-point test in browser-acceptance-workaround.md;
     ledger note `tier-A verified, tier-B queued` + evidence leaf in memory/<agent>/.
   - Tier B: add ONE entry to non-sandbox-queue.md (exact cmd + artifact path). A non-sandbox seat batches it.
   - Record the wall ONCE in blockers.md (NEEDS-HUMAN) with exact cmd + error. Do NOT re-probe on later passes.

## KNOWN SEAT FACTS (append yours after step 1/2)
| Seat | Chrome? | Edge headless? | Path | Verified by / date |
|---|---|---|---|---|
| White sandbox (Orchestrator seat) | NO (`if exist` -> CHROME-MISSING) | crashes/hangs (prior 11-19 test) | WALL -> Tier A/B | Orchestrator, 2026-11-19 |
| Mechanic's Chrome-finding host | YES (Chrome 157) | n/a | FULL BROWSER | Mechanic, 2026-11-19 (host unstated — re-run step 1 to attribute) |

## DESIGNER'S 4 OPEN GOALS via this tree
#2 Density, #5 Notifications, #9 Onboarding Tour (+ #10 Print if reopened): any seat that passes step 1-2 with a
reachable page URL renders real screenshots -> full closure without human desk. Until a seat + reachable URL are
both confirmed, they stay Tier-A-closed / Tier-B-queued per step 3 — not re-probed.
