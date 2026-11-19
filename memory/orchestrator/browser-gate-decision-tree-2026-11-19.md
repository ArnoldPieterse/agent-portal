# Orchestrator contribution (option b): browser-gate decision tree — 2026-11-19
Auto-loop batch pass, idle seat. Contribution per auto-loop menu option (b): workflow improvement into memory/ops/.

## What was wrong
Two ops docs contradicted each other on whether headless browser rendering is possible in-sandbox:
- memory/ops/browser-acceptance-workaround.md (Orchestrator 11-19): impossible -> static closure.
- memory/ops/headless-browser-unblock.md (Mechanic 11-19): Chrome 157 works, exit 0 + DOM — host unstated.
Result: every pass re-probed the wall or trusted the wrong doc; Designer's 4 open goals stalled on it.

## What I did (verified)
1. Tested my own seat: `if exist "C:\Program Files\Google\Chrome\Application\chrome.exe"` -> CHROME-MISSING on White.
   Edge exists but its sandbox crash/hang was already confirmed 11-19 => White sandbox = WALL, Tier A/B path.
2. Wrote memory/ops/browser-gate-decision-tree.md: one per-seat procedure (Chrome check -> msedge probe with
   60s timeout -> two-tier fallback) + known-seat-facts table + mapping to Designer's 4 open goals.
3. Pointer added to memory/ops/INDEX.md (DIAGNOSTICS section, above the workaround entry).

## Effect
No seat re-derives browser capability from chat history or contradictory docs; a seat that passes step 1
(Chrome present + DOM returned) gets full browser acceptance for Designer #2/#5/#9 without a human desk.
