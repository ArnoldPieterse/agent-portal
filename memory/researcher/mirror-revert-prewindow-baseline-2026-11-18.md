# Mirror-Revert Pre-Window Baseline (goal #3) — cadence analysis from on-disk pin files

Date: 2026-11-18 (auto-loop pass). Purpose: give day-7 closure (11-24) an INDEPENDENT data source for the "which files revert most / what triggers them" question, built from artifacts that already exist on disk — so it does NOT depend on the still-blocked live mirror seed. This is a LOWER BOUND and a SHAPE PREDICTOR, not the acceptance dataset itself.

## Method
Enumerated every `*_CANONICAL_*` pin file in `memory/designer/` (46 index.html + 1 ui_app_css.css + 2 ui_js .js = 49), extracted each file's mtime (= the moment a pin advance was committed: copy new file → update PIN_FILES sha12 → commit). A pin advance is the on-disk footprint of one successful re-apply after a revert (or a first apply); consecutive advances closer together than a legitimate edit cycle can be are evidence of an automated clobber-revert loop. Raw rows: `memory/researcher/_pin_timeline_raw.json`.

## Per-file pin-advance count by mtime-day
| file | 11-15 | 11-16 | 11-17 | 11-18 | total |
|------|-------|-------|-------|-------|-------|
| index.html | 1 | 23 | 21 | 1 | **46** |
| ui_app_css (.css) | 0 | 0 | 1 | 0 | 1 |
| ui_core_js (.js) | 0 | 1 | 0 | 0 | 1 |
| ui_uploads_js (.js) | 0 | 0 | 1 | 0 | 1 |
| **total** | **1** | **24** | **23** | **1** | **49** |

## Cadence finding (NEW this pass — stronger than a plain file count)
index.html advance cadence on the two burst days:
- **11-16: 23 advances over 10.0 h → median gap 8.4 min, MIN GAP 0.3 min (~18 s)**
- 11-17: 21 advances over 18.5 h → median gap 24.0 min, min gap 2.1 min

A legitimate pin advance requires copy-new-file + recompute sha12 + edit PIN_FILES in memory_mirror.py + commit — a cycle that cannot complete in ~18 s under normal human/agent operation. A sub-minute gap between consecutive canonical re-pins is direct quantitative evidence of an **automated clobber-revert loop**: the mirror reverts an edit and it is re-applied almost immediately, repeatedly, until the pinned copy wins.

## What this means for the day-7 frequency table
1. **index.html is predicted to be top-1 in the live log's most-reverted ranking** — 46/49 = 94% of all pin-advance events locally. (Confirms hypothesis #1 already seeded in `mirror-revert-analysis-template-2026-11-18.md`.)
2. **The trigger is the clobber loop, not just "edit-heavy days"** — the cadence (median 8 min, floor 18 s) is too fast for organic churn; it points to an automated feedback cycle. This sharpens hypothesis #2: separate burst windows from steady-state, but ALSO expect the bursts to be dominated by sub-minute re-apply gaps.
3. **Structural-change guard** — the 11-16→11-17 boundary is the UI split (index.html 91 KB → 10 KB + 3 ui/ modules). Any live-log event spanning that boundary with a hash_mismatch trigger is an INTENTIONAL structural change, not a sync bug; flag it to avoid miscounting.

## Correction to prior forensics
Earlier passes cited "49 CANONICAL pins" and my first scan this pass returned 46 (glob was `.html`-only). Reconciled: the 3 ui pins are `.css`/`.js`, not `.html`. Correct total = **49** (46 index.html + 1 css + 2 js). No change to the 94% index.html share; the template count of 49 was correct.

## Status / what is still needed for closure
This baseline is CLOSURE-SUPPORTING, not the acceptance dataset. Acceptance (goal #3 verified clause) still requires the **one-week LIVE mirror_events.log** (window 11-17→11-24) + an analysis leaf cross-checking live events against this baseline. That live dataset remains gated on the logged NEEDS-HUMAN seed wall at C:\Projects\AgentPortal — NOT re-probed per anti-loop. At day-7 closure, `fill_analysis.py` output (live log) should be compared row-for-row against this table; agreement = high confidence, divergence = investigate.

## Cross-references
- Template + hypotheses: memory/researcher/mirror-revert-analysis-template-2026-11-18.md
- Closure runbook + contingency: memory/researcher/mirror-revert-closure-runbook-2026-11-17.md
- Raw pin timeline: memory/researcher/_pin_timeline_raw.json
- Instrumentation: memory/researcher/mirror-revert-instrumentation-2026-11-17.md