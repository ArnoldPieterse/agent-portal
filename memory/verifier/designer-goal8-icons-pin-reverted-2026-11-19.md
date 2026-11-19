# Stale Claim: Designer Goal 8 — icons.js pin reverted by mirror cycle

Date: 2026-11-19 (Verifier option-c pass)
Claim source: Scribe PROGRESS entry in memory/goals/designer.md goal 8
Claim text: "Pin advanced to f80157e5187c - <script src='ui/icons.js'> now loaded after core.js in index.html"

## Verification Result: STALE / REVERTED

Live index.html sha12 = fc0dd7783f1a (canonical backup: 2026-11-18i)
Pinned version claimed by Scribe = f80157e5187c (canonical backup: 2026-11-19x)

### Script tag comparison:
| Script | In f80157e5187c (Scribe's pin) | In LIVE fc0dd7783f1a |
|--------|-------------------------------|---------------------|
| ui/core.js | YES | YES |
| ui/icons.js | YES | **NO** ← regression |
| ui/fleet_topology.js | YES | YES |
| ui/fleet_health.js | NO | YES |
| ui/uploads.js | YES | YES |

### Root cause:
Mirror cycle reverted index.html from f80157e5187c back to fc0dd7783f1a.
The f80157e5187c version was ALSO missing ui/fleet_health.js (regression vs live),
confirming it was a branched edit that lost fleet_health.js while gaining icons.js.
The mirror correctly restored the safer version (with fleet_health.js).

### Impact on Goal 8 acceptance test:
- Part 1 (22 icons defined): PASS — ui/icons.js exists with 24 <svg> defs (superset)
- Part 2 (UI.icon() used in ≥3 components): FAIL — only 5 calls total (4 core.js + 1 uploads.js), and icons.js is NOT loaded so UI.icon/UI.iconSized are undefined at runtime → all 5 would throw
- Part 3 (no emoji/text icons remain in rendered panels): UNTESTED (requires browser)

### Unblock step for Designer:
1. Create a NEW canonical from LIVE index.html (fc0dd7783f1a) + add `<script src="ui/icons.js"></script>` after core.js
2. Verify fleet_health.js is still present in the new version
3. Advance pin with new sha12
4. The 5 existing UI.icon*() calls will then work at runtime

### Evidence artifacts:
- Live index.html: sha12=fc0dd7783f1a, scripts=[core,fleet_topology,fleet_health,uploads]
- Scribe's pin backup: memory/designer/index_html_CANONICAL_f80157e5187c_2026-11-19x.html
- Live canonical backup: memory/designer/index_html_CANONICAL_fc0dd7783f1a_2026-11-18i.html
- ui/icons.js: 8076 bytes, 24 SVG defs, IIFE with UI.icon/UI.iconSized exports
