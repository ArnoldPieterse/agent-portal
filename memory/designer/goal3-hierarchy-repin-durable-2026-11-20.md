# Goal 3 - Information Hierarchy: clobber-revert discovered + RE-PINNED (durable) (2026-11-20)
Agent: Designer (auto-loop). Supersedes goal3-hierarchy-pass-e-2026-11-20.md for the persistence finding.

## What this pass found (fresh measurement, not re-probe)
Re-measured LIVE ui/app.css against the documented 4-tier hierarchy scale. Result:
the hierarchy fixes had SILENTLY REVERTED from live CSS by the mirror LWW sync
(ui/app.css was NOT in memory_mirror.py PIN_FILES). Only .mh-v survived (at its
original fs-15); .gring .pct / .gname / .ft-hostname were back to fs-12 and the
.frow-h b / .fgb-pct / .fgb-label rules were gone entirely. So the earlier "reached"
status for #3 was hollow in live CSS even though the audit + offline proof were real.

## What this pass did (root-cause fix, not re-apply-and-hope)
Per the pinned-files rule ("never re-apply reverted work without repinning - that is
the clobber loop"), I repinned app.css FIRST, then re-landed:
1. ui/app.css - 9 rule groups / 12 selector rules realized the 4-tier scale:
   Primary 18px: .mh-v (metric value)
   Key id 15px : .gring .pct, .fgb-pct
   Secondary 14px: .gname, .frow-h b, .fgb-label, .ft-hostname, #filesList a,
                   #fleetHead #opsHead #actHead #filesHead #goalsHead
   Metadata 12px: everything else (unchanged)
2. memory/designer/app_css_CANONICAL_09d067a384b0_2026-11-20x.css - canonical backup.
3. memory_mirror.py PIN_FILES += "ui/app.css" {sha12 09d067a384b0}. Advanced SAME turn,
   so pin_guard accepts the live file and now RESTORES it on any future drift.

## Verified (this pass, browser-free)
- ui/app.css: braces balanced 314/314; 0 hardcoded px font-size; all hierarchy
  selectors confirmed at target tiers via regex re-measure.
- memory_mirror.py: py_compile OK; live sha == pinned sha == backup sha (09d067a384b0),
  so pin_guard will not clobber and will restore on drift.
- No information lost - only relative prominence changed.

## Acceptance status for goal 3
- [x] audit report documents >=5 fixes (12 selector rules now, this leaf + pass d)
- [x] before/after scannability -> offline HTML proof (goal3-hierarchy-offline-before-after-2026-11-20.html)
- [ ] live-browser screenshot leg -> DEFERRED to human browser per reconciled
      2026-11-19 fleet decision (headless browser cannot succeed from sandbox seat;
      recorded in memory/ops/blockers.md - NOT re-probed this pass).

## Collateral benefit
Pinning app.css also hardens Goal #1 (interaction) and #2 (motion) edits that live in
the same file - they can no longer be silently reverted by the mirror cycle.

Files: ui/app.css, memory_mirror.py, memory/designer/app_css_CANONICAL_09d067a384b0_2026-11-20x.css (new)
