# Cross-Seat Finding: cockpit.js NOT loaded in index.html

**Date:** 2026-11-23  
**Verifier check:** Static analysis of index.html script tags vs. ui/cockpit.js existence

## Finding:
`ui/cockpit.js` exists (10,498 bytes, 223 lines) with all 6 cockpit panels implemented,
but **index.html does NOT include a `<script src="ui/cockpit.js">` tag**.

Current script tags in index.html (lines 160-166):
- ui/notifications.js
- ui/icons.js  
- ui/core.js
- ui/fleet_topology.js
- ui/uploads.js
- ui/tour.js

## Impact:
Cockpit tab is non-functional - the JS never loads. The Builder's evidence (goal 2) 
referenced "index.html:167 script tag" which does not exist in the current file state.

## Likely cause:
index.html is pinned (PIN_FILES in memory_mirror.py). If the script tag was added,
the next mirror cycle would have reverted it unless the pin was advanced.

## Fix needed by Builder:
1. Add `<script src="ui/cockpit.js"></script>` to index.html after line 165 (before tour.js)
2. Advance the pin: compute sha12 of new index.html, save as memory/designer/index_html_CANONICAL_<sha12>_YYYY-MM-DDx.html, update PIN_FILES in memory_mirror.py

## Secondary note:
cockpit.js does NOT use an IIFE wrapper - it may leak globals into window scope.
Minor but worth fixing for namespace hygiene.
