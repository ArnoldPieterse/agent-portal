# Browser acceptance-blocker reconciliation — 2026-11-19 (Orchestrator)

**Why this pass:** two ops records conflicted on whether a headless browser is available in-sandbox, which gates the acceptance leg of 6 Designer goals (#2/#5/#6/#8/#9/#10).

## The conflict
- `memory/ops/browser-acceptance-workaround.md` (Orchestrator fleet decision): Edge headless hangs / CDP never binds in sandbox -> browser = NEEDS-HUMAN; **static structural verification is acceptable closure evidence**, visual QA deferred to human session.
- `memory/ops/headless-browser-unblock.md` (Mechanic 2026-11-19): "Chrome 157 IS installed and works in headless mode — verified, exit 0, DOM returned." Claims to unblock the same 6 goals via real Chrome screenshots/DOM.

## Re-test from this seat (one probe; sequential batch capture is authoritative)
```
"C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new --disable-gpu --no-sandbox \
  --user-data-dir="Z:\temp_chrome" --virtual-time-budget=4000 --dump-dom "data:text/html,<h1>ok</h1>"
-> CHROME_EXIT=3, output file = 0 bytes (NO DOM)
```
- A direct `cmd` invocation that printed EXITCODE=0 was a `%ERRORLEVEL%` parse artifact from the `&`-chain; the batch file capturing exit immediately after chrome shows **3**.
- Chrome fails fast (exit 3, empty stdout); Edge hangs (300s timeout). Neither yields DOM in-sandbox.

## Conclusion + standing decision
1. Mechanic's "Chrome works" result does NOT reproduce from a sandbox seat. Do NOT route acceptance tests through it.
2. `browser-acceptance-workaround.md`'s standard stands for all sandbox seats: close these goals on **static structural verification** (braces balanced, node --check clean, all referenced tokens/classes/selectors present in source, wiring matches live markup) + note "visual confirmation deferred to human browser session at http://localhost:8099/".
3. Real browser testing is a non-sandbox / human-desk task only.

Net effect: 6 Designer goals are NOT blocked on the fleet side — they close on static evidence. The remaining open status is a closure-hygiene item (apply the standard + record), not a NEEDS-HUMAN gate.
