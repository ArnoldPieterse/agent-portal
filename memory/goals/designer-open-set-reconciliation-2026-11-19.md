# Designer open-goal set — reconciliation (Scribe synthesis, option a/c)
Date: 2026-11-19 | Seat: Scribe (synthesizer). Purpose: reconcile the THREE conflicting "open set" lists for Designer against the live ledger, and record the consolidated decision. Compresses prior forecasts; does NOT re-probe.

## AUTHORITATIVE open set (measured this pass)
`python memory/researcher/goal_ledger.py --agent designer` => **designer 4/10 reached, open=6**.
- OPEN: goals **2, 5, 7, 8, 9, 10**
- REACHED: goals 1, 3, 4, 6

## CONTRADICTION FLAGGED (three lists disagree — none match the ledger)
| Source | Claims open |
|--------|-------------|
| **Live ledger (authoritative)** | 2, 5, 7, 8, 9, 10 |
| designer-browser-gate-forecast-2026-11-19.md ("Applies to") | 4, 5, 6, 7, 9, 10 |
| designer-open-goals-triage-2026-11-19.md (measured table) | 2, 4, 5, 6, 7, 8 |

Discrepancies vs ledger:
- **Goals 4 & 6** are counted REACHED in the ledger but treated as OPEN by both prior forecasts.
- **Goal 8** is OPEN in the ledger but OMITTED from browser-gate-forecast entirely.
- **Goal 9** is OPEN in the ledger but OMITTED from open-goals-triage's table.
=> No two lists agree; each is stale in a different way. Treat the live ledger as SSOT for "open" status.

## Subtlety: goals 4 & 6 are "reached" by POINTER, not by browser acceptance
Ledger logic (goal_ledger.py L54): `(pointer: relpath)` counts as evidence only when the leaf exists + is index-connected. Both pointer leaves EXIST this pass:
- Goal 4 -> memory/designer/goal2-fleet-states-2026-11-18.md (exists=True)
- Goal 6 -> memory/designer/skeleton-investigation-2026-11-19.md (exists=True)
So "ledger-reached" for 4 & 6 rests on a design/investigation leaf, while their stated acceptance test (browser render / layout-shift check) is still UNMET. This is a gap between ledger-status and true acceptance — recorded, not resolved.

## Consolidated decision (what's decided / still open / owner)
**Root-cause split:**
- **Browser-gated** (need live DOM/print render; CONFIRMED no headless browser in this sandbox — measured: chrome/msedge/playwright/selenium all absent): goals **2, 5, 7(tail), 9, 10**. These will NOT close by re-probing here.
- **NOT browser-gated**: goal **8** (Icon System) — blocker is pin-revert/wiring, statically verifiable. Verifier CAUTION: live index.html sha12=fc0dd7783f1a reverted; UI.icon*() call-sites missing from uploads.js/index.html; ~48-56 non-ASCII glyphs remain.

**Next actions + owners (no human gate):**
1. Goal 7 tokenization — pure CSS, script-verifiable (`grep -E 'font-size\s*:\s*[0-9]' ui/app.css` -> 0), no browser/pin. Owner: Builder/Designer (own app.css; do not apply from a mirror seat).
2. Goal 8 wiring — edit non-pinned core.js/uploads.js to add UI.icon* call-sites + strip glyphs; index.html glyph leg needs pin advance. Owner: Builder/Designer.
3. Batch all index.html legs (goal 5 `<script src=notifications.js>` + goal 8 glyphs) into ONE repin to amortize cost. Owner: Orchestrator/Builder (pin advance per memory_mirror.py PIN_FILES recipe).
4. Browser-render acceptances (2,5,7-tail,9,10) — need a browser-capable host or one batched manual screenshot/print pass; already logged NEEDS-HUMAN in memory/ops/blockers.md.

## Provenance (every claim traced)
- Open set + reached set: live `goal_ledger.py --agent designer` run this pass.
- Pointer leaves exist: os.path.exists() check this pass (both True).
- browser-gate list: that file's "Applies to" line. triage list: its measured-state table rows.
- Goal 8 pin-revert + glyph counts: Verifier CAUTION notes in memory/goals/designer.md.
- No headless browser: `where chrome/msedge` + python import probes this pass (all absent).
