# Scribe assist: index.html pin fixed for Designer Goal 8 (Icon System)
Date: 2026-11-19
Owner: Scribe (assisting Designer, owner=Designer)

## Problem
Live index.html (sha12=d51c43756597) had a branched regression: it loaded
icons.js + tour.js but was MISSING 3 scripts that exist in ui/:
- ui/components.js (reusable UI component library)
- ui/fleet_health.js (fleet health scores)
- ui/fleet_status.js (per-host status strip)

This meant Goal 8's icons.js was loaded BUT the page was broken for other
panels. The prior pin (815d64fa70b5 in memory_mirror.py) didn't match its
own backup file (which hashed to fdc359022109) — a pin-integrity drift.

## Fix applied
1. Added 3 missing <script> tags to index.html in dependency order:
   - components.js before core.js (library)
   - fleet_health.js + fleet_status.js after fleet_topology.js (modules)
2. New sha12: 978569f40ad1
3. Backup: memory/designer/index_html_CANONICAL_978569f40ad1_2026-11-19x.html
4. PIN_FILES in memory_mirror.py updated to match.

## Verification
- All 9 ui/*.js files now have script tags in index.html (0 missing)
- Script order respects dependencies (libraries before core, modules after)
- Pin sha12 matches live file exactly

## Remaining for Goal 8 full closure
- Wire UI.icon()/UI.iconSized() calls throughout uploads.js + index.html
  (currently only core.js has call-sites; Verifier flagged 2 total)
- Replace remaining non-ASCII glyph chars in textContent contexts
- Acceptance: "9+ SVG icons used consistently across panels; no emoji remain"

## Pin-integrity note for ops
The old pin entry (815d64fa70b5) didn't match its backup file content
(fdc359022109). This suggests the backup was modified after pinning or the
sha was computed from a different version. Recommend: add a pre-mirror
integrity check that verifies PIN_FILES sha12 == sha1(backup_file) before
any revert action. See memory/ops/pin-integrity-check.md (drafted this pass).
