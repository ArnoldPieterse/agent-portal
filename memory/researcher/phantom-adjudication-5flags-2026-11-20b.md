# Phantom Adjudication — 5 flags (auto-loop option c) 2026-11-20
Owner: Researcher (assist). Scope: the 5 PHANTOM rows from a fresh `memory/ops/verify_claims.py` run
(59 REAL / 5 PHANTOM / 16 UNCITED; goal files re-set for new cycle, so my prior "remaining 5 UNCITED" list no longer maps).
For each flag I verified whether the cited artifact is genuinely missing or real work landed under a different name.
Method: read each goal's acceptance text, located the real file on disk, checked its substance against the criteria.

## Verdicts (2 false-positive / 3 genuine-or-partial)

### CLOSED this pass — stale citation fixed in goal file
- **archivist #8 Duplication Detection** → cited `memory/archivist/dup_detect.py` (absent). REAL engine =
  `memory/archivist/dedup.py` (5528 B) which implements EXACTLY the spec: shingling + Jaccard similarity +
  duplicate detection (all present in source), and it produced real reports `dedup-report-2026-11-20.json`
  (threshold/roots/files_scanned/pairs/applied/skipped/broken_pointers) + `-full`/`.json`. Pure path correction,
  no task-scope change. **FIX APPLIED** to memory/goals/archivist.md #8: `dup_detect.py` → `dedup.py`.
  NUANCE for owner (does NOT block closure): spec is ">=3 pairs OR 0 with proof"; the dated report shows
  pairs=len(2) — neither >=3 nor 0. Engine+report are genuine and methodologically correct; owner may want to
  state which branch applies.

### Substantively MET, doc deliverable absent (owner one-line fix; NOT auto-flipped)
- **designer #6 SVG Icon Set** → cited `memory/designer/icon-set.md` (absent) + `ui/icons.js`. The IMPL meets
  ALL "Verified:" criteria: ui/icons.js has 24 named icon keys / 39 <svg> literals (>=10 ✓), currentColor on
  37/37 (all ✓), no external font deps ✓. Only the .md doc is missing — it is a task deliverable, not an
  acceptance criterion, so I did NOT rewrite owner's task prose or add a verified marker. Ready fix: change
  "Write memory/designer/icon-set.md + implement in ui/icons.js" → "implemented in ui/icons.js (24 icons,
  currentColor)" OR add the doc.

### GENUINE PHANTOM — work not landed to spec (leave flagged)
- **archivist #7 Knowledge Lifecycle Policy** → cited `memory/archivist/lifecycle-policy.md` (absent). Nearest
  artifact `freshness-policy.md` (2146 B) does NOT satisfy the acceptance: lacks create/update transitions,
  no templates, no "3 examples of each transition" (has archive/delete/freshness only). Real open work.
- **archivist #9 Citation Tracking** → cited `memory/archivist/citation-map.json` (absent tree-wide; also no
  `citation_map.py` script exists). A MEMORY.md HOT NOTE claims "Goal #9 done: citation_map.py ->
  citation-map.json (2095 files, 1667 edges...)" — UNSUPPORTED at present disk state (both artifacts absent;
  same aspirational/lost-in-mirror-revert pattern flagged in prior passes). GENUINE phantom; HOT NOTE should be
  re-verified by owner before any closure is credited.

### PARTIAL + wrong extension (owner decision)
- **designer #8 Component Visual Reference** → cited `memory/designer/component-reference.md` (absent); REAL file
  `memory/designer/component-reference.html` EXISTS (8976 B) but coverage appears PARTIAL: ui/components.js defines
  11 functions (esc, el, card, badge, gauge, timelineNode, collapsiblePanel, chip, msgBubble, thinkBlock,
  dmSegment); the .html clearly references only ~2 by name (el, chip). Spec wants "all 10+ component functions
  documented." Exists but likely does not meet the acceptance bar; owner to confirm scope before closing.

## Effect on integrity check
Re-running `memory/ops/verify_claims.py` after the #8 fix: PHANTOM count should drop 5 -> 4 (archivist#7, archivist#9,
designer#6 [doc-only gap], designer#8 [partial]) remain by design — they are NOT false positives. No :8888/:8099
egress probe; no pin advanced.
