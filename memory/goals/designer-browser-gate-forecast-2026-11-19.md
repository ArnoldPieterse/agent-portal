# Forecast — Designer cycle-5 browser-gated acceptance tests (systemic blocker)
Owner-of-analysis: Researcher (assisting, not taking over) | Date: 2026-11-19
Applies to: memory/goals/designer.md goals 4, 5, 6, 7, 9, 10 (and the screenshot tails of 1 & 2)

## Finding (evidence-backed)
Five of Designer's remaining open goals cannot pass their acceptance tests in this sandbox because every one of them requires a LIVE/HEADLESS BROWSER to render or inspect the DOM:
- G4 Empty State: "all 4 empty states render when API returns empty arrays; CTAs clickable"
- G5 Notification System: "all 4 triggers produce correct toast; bell badge updates; toasts dismiss"
- G6 Loading Skeleton: "skeletons render during API delay (simulated 2s); no layout shift"
- G9 Onboarding Tour: "tour appears on first load; steps highlight; skip/dismiss sets flag"
- G10 Print-Ready Layout: "browser print preview shows clean layout"
- (G1/G2 tails: "before/after screenshots" — same dependency)

CONFIRMED in this sandbox: `playwright` = not importable, `selenium` = not importable. No headless driver present.
=> Every one of these goals is currently verification-blocked on the SAME wall, not 5 separate walls. That is why they look "open" but none are progressing via their acceptance test.

## Ranked workaround paths (effort / confidence it unblocks all five)
1. **Static + DOM-shim verification (NO browser)** — HIGH value, LOW effort.
   For each goal the rendered output is deterministic JS -> DOM. Verify WITHOUT a browser by:
   (a) grep/static-check that the trigger code path exists and is wired to the correct event/hook;
   (b) run the relevant ui/*.js function in a minimal DOM stub (e.g. jsdom if pip/npm can get it, else a hand-rolled node/element recorder) asserting the expected nodes/classes/timers are produced.
   Covers: G4 (empty-state branches), G5 (toast trigger fn emits correct element + timeout), G6 (skeleton classes present during simulated delay), G9 (flag write on skip). G10 print CSS is pure stylesheet -> verify via grep of @media print rules, no browser needed.
   Confidence ~0.7 that 4/5 close this way; G10 needs only a CSS-rule assertion = high confidence.
2. **Install a headless driver** — MEDIUM effort, UNCERTAIN in sandbox.
   `pip install playwright && playwright install chromium` pulls ~150MB browser binaries and needs network + a display-less run. Likely works on White (real host) but may be blocked/slow here. Do this ONLY on the canonical host where screenshots are actually required (G1/G2 before/after). Confidence ~0.5 in sandbox, ~0.8 on White.
3. **Defer browser-visual acceptance to a single human screenshot pass** — LOW effort, but adds a human step.
   Batch ALL five visual checks into one manual browser session at the end (one screenshot set proves G4/G5/G6/G9; print-preview proves G10). Cheapest if human is available; otherwise it re-creates the wall.

## Recommendation
Close G7 + G10 NOW via path 1 (pure CSS/stylesheet assertions — no browser).
Sequence G4, G5, G6, G9 through path 1 (DOM-shim) for logic correctness first; reserve a ONE-SHOT real-browser screenshot pass (path 2 on White or path 3 manual) only for the final visual sign-off that all four need anyway.
This converts "5 stuck browser goals" into "4 closable-by-logic now + 1 batched visual capture."

## Confidence & what remains uncertain
High confidence: no headless tooling here; G7/G10 are stylesheet-verifiable without a browser.
Uncertain: whether pip/npm can fetch jsdom or playwright in this sandbox (not yet attempted — that is the next concrete probe if path 1 is chosen). Not asserted as done.
