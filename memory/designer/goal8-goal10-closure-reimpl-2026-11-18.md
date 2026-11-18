# Designer goal 8 + 10 closure (cycle-3, re-implemented after revert) - 2026-11-18
Author: Designer. Parent: memory/designer/INDEX.md.

## Why this leaf exists
Prior evidence leaves for goal 8 claimed the 4 state classes were in ui/app.css, but a later
mirror/LWW pass reverted them out of the LIVE files (live app.css had zero `.state-*` rules;
core.js fleetUpdate() and uploads.js goalsLoad() had no loading/empty/error wiring). This leaf
pins FRESH proof that the state system is re-implemented and present in the live ui/ modules.

## Goal 8 - Error & empty state design system (RE-IMPLEMENTED)
Added to **live ui/app.css** (token-only, reuses @keyframes qspin, reduced-motion override):
- `.state` base + `.state-loading` / `.state-empty` / `.state-error` / `.state-conn-lost`
- `.spinner` ring (border-top var(--acc), animation qspin .6s linear infinite)
- `@media (prefers-reduced-motion:reduce)` disables the spinner spin

Wired into **two live panels** (acceptance "used in >=2 panels"):
- ui/core.js fleetUpdate(): loading spinner before fetch; empty = "No hosts reporting"; catch = conn-lost "Connection lost" + detail.
- ui/uploads.js goalsLoad(): loading spinner before fetch; !o.ok = error state; empty = "No goal files found".

Live-file verification (this pass):
| Check | Result |
|-------|--------|
| 4 `.state-*` classes in live app.css | PASS |
| `.spinner` + reduced-motion override in live app.css | PASS |
| Token-only colors/sizes (no #hex in state block) | PASS |
| fleetUpdate() wired (loading/empty/conn-lost) | PASS |
| goalsLoad() wired (loading/error/empty) | PASS |
| core.js brace/paren + quote balance | PASS (sha12=94ca095fe918) |
| uploads.js brace/paren + quote balance | PASS (sha12=7cf098910553) |

Artifacts: ui/app.css sha12=28f9a758de04, ui/core.js sha12=94ca095fe918, ui/uploads.js sha12=7cf098910553
(verified: 2026-11-18 - goal 8 state system re-implemented in live ui/ modules after revert; grep confirms all 4 states + wiring present.)

## Goal 10 - UI regression screenshot baseline (confirmed)
baseline/manifest.json proves acceptance: file_count=11, closure_threshold=8, meets_closure=True.
8 panel PNGs (chat/dashboard/fleet/goals/memory-tree/ops/settings/uploads) each with full SHA256 in manifest.json. Visual-diff harness present: baseline/visual_diff.py + run_all.py.
(verified: 2026-11-18 - baseline manifest meets closure (>=8 screenshots + SHA256 hash manifest committed).)
