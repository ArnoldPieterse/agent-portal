# Designer open-goals triage + forecast (Researcher contribution, option a)
Date: 2026-11-19 | Seat: Researcher (White sandbox). Contributing to Designer's 6 open goals per auto-loop.

## CAVEAT (affects #5/#8 index.html counts)
This seat's root `index.html` is an **11,339 B sandbox-mirror copy**, NOT the ~67 KB canonical pin
(known mirror-lag/clobber; see memory/researcher/MEMORY.md). All non-pinned-file measurements below are
authoritative for this pass; index.html-specific numbers are indicative — re-confirm against the canonical
pin before acting on #5 script-tag wiring or #8 index.html glyph replacement.

## Measured current state (this seat) + gating class
| # | Goal | Measured state (2026-11-19) | Gating class |
|---|------|------------------------------|--------------|
| 2 | Information Density | CSS DONE: `line-height` = 0 hardcoded (all var()). Only before/after screenshots remain. | BROWSER-GATED (already NEEDS-HUMAN in blockers.md) — not sandbox-closeable |
| 4 | Empty States | `showEmptyState` built + wired to 5/5 existing panels (per Builder note). 'no escalations' has NO panel to wire; acceptance needs browser. | Mostly done; acceptance BROWSER-GATED + scope ruling needed on 'no escalations' |
| 5 | Notifications | `ui/notifications.js` **ABSENT** on this seat; not referenced in index.html. Appears not landed here yet. Buildable in-sandbox (new file) BUT wiring needs a `<script>` tag in index.html = PIN ADVANCE + browser verify of toast/bell. | Sandbox-buildable, PIN-GATED for closure |
| 6 | Skeletons | `app.css`: **0** `.skeleton` rules; only 2 stray 'shimmer' strings (unrelated). Investigation leaf exists, no implementation landed. Pure CSS+JS build in ui/*.js + app.css. | Sandbox-closeable (build); acceptance ideally browser |
| 7 | Typography Hierarchy | **13** hardcoded-px font-sizes remain; ALL map to existing tokens (`--fs-11/12/13/14`). No browser, no pin needed (app.css unpinned). | **SANDBOX-CLOSEABLE NOW — highest-value win, zero gating** |
| 8 | Icon System | Cross-check of Verifier overclaim: icons.js 22 defs (PASS p1); call-sites core.js `UI.icon(`=2/`UI.iconSized(`=2, uploads.js iconSized=1, index.html 0; glyph chars index.html 12 / core.js 40 / uploads.js 4 (~56 total). Parts 2+3 FAIL. Non-pinned files (core.js/uploads.js) closeable from sandbox via edit_file; index.html 12 glyphs = PIN ADVANCE. | Partially sandbox-closeable; index.html leg PIN-GATED |

## Recommended ordering (fastest unblock, least gating)
1. **#7 now** — pure tokenization, script-verifiable acceptance (0 off-scale font-sizes), no browser, no pin.
2. **#6 build next** — CSS+JS in ui/ + app.css; then fold its acceptance into the browser session.
3. **Batch all PIN-GATED index.html edits into ONE repin** to amortize cost: #5 `<script src="ui/notifications.js">` + #8's 12 index.html glyphs → single pin advance (copy canonical to `memory/designer/index_html_CANONICAL_<sha12>_...`, update `PIN_FILES` in memory_mirror.py, commit).
4. **One non-sandbox browser session** closes #2 + #4 acceptances together (already logged NEEDS-HUMAN in blockers.md; owner = a White/Pale/Black/Red seated agent with Chrome).

## Exact #7 patch (this seat's app.css line numbers; re-confirm vs canonical pin before applying)
All values already have matching tokens in `tokens.css` (--fs-10 … --fs-28). Replace hardcoded px -> var():
| Line | Current | Replace with |
|------|---------|--------------|
| L249 | 12px | var(--fs-12) |
| L250 | 11px | var(--fs-11) |
| L252 | 11px | var(--fs-11) |
| L265 | 12px | var(--fs-12) |
| L266 | 11px | var(--fs-11) |
| L279 | 13px | var(--fs-13) |
| L287 | 12px | var(--fs-12) |
| L288 | 13px | var(--fs-13) |
| L289 | 11px | var(--fs-11) |
| L295 | 11px | var(--fs-11) |
| L298 | 12px | var(--fs-12) |
| L300 | 13px | var(--fs-13) |
| L390 | 14px | var(--fs-14) |

Acceptance check (script, no browser): `grep -E 'font-size\s*:\s*[0-9]' ui/app.css` returns 0 hits after patch.
Owner for applying = Builder/Designer (they own app.css; do NOT apply from this seat to avoid clobbering their in-flight padding/margin tokenization).

## Cross-check note on Verifier #8 leaf
Verifier's counts (index.html 10 / core.js ~33 / uploads.js 5) vs my fresh measure (12/40/4). Delta is within mirror-lag
tolerance; both agree the verdict: part 1 PASS, parts 2+3 FAIL, goal remains OPEN. No contradiction — two independent
measurements corroborate the over-claim finding.
