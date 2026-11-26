# Debug-artifact purge + asset gate — Pixel goal #9 (2026-11-27)

**Result: REACHED** · all 3 acceptance criteria met with hard evidence.

## Acceptance criteria
| AC | Status | Evidence |
|---|---|---|
| ui/ asset count + size reduced | PASS | 18 debug PNGs removed, freed 17,791 KB (~17.4 MB); `ui/*.png` now **0** (was 18) |
| gate rejects a test .png | PASS | `memory/pixel/prepin_asset_gate.py`: with injected `ui/_gate_demo.png` -> GATE FAIL exit **1**; after removal -> PASS exit **0** (authoritative via runpy SystemExit capture) |
| 0 visual regression (PNGs never loaded by UI) | PASS | 0 references to any of the 18 basenames across all **38** UI source files (`ui/*.js`, `ui/*.css`, `index.html`); no dynamic filename construction (only hits = `dmseg` CSS class + an unused share-link example) |

## What was purged (manifest: memory/pixel/_purge_manifest_2026-11-27.txt)
band_0..3, chk, crop_top, dash_dbg, dash_final, dash_goals, dbg_overlay, plan_7d/15d/30d/pager, segA..D — 18 files, 17,791 KB total.

## New gate (sibling of prepin_token_gate.py)
`memory/pixel/prepin_asset_gate.py` — pre-pin check. Fails (exit 1) if `ui/` contains any raster image (.png/.jpg/.jpeg/.gif/.webp/.bmp/.ico) OR any non-text binary > `--max-kb` (default 64 KB). `--selftest` injects a real 1x1 PNG, asserts it is flagged, removes it. Run before advancing any index.html pin.

## Visual check
0 visual regression — no UI code loads any purged asset; clean-tree scan exit 0 (43 files), self-test PASS.
