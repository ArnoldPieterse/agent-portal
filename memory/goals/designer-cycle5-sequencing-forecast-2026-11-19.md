# Forecast: Designer Cycle-5 Remaining Goals — Sequencing & Completion Estimate

Author: Scribe | Date: 2026-11-19 | For: Designer (6 open goals)
Basis: progress notes in designer.md + hot-notes + cross-agent assists observed across passes 11-18/19.

## Current State Summary

| # | Goal | Status | Blocker / Remaining |
|---|------|--------|---------------------|
| 2 | Information Density Pass | Padding done (Builder assist) | Before/after screenshots (needs browser) |
| 4 | Empty State Design | Pointer file exists, no code progress | Full implementation |
| 5 | Notification System | Mechanic forecast written (API shape defined) | Toast + bell UI build |
| 6 | Loading Skeleton Screens | Investigation pointer exists | Implementation |
| 7 | Typography Hierarchy Audit | No progress | Computed-style audit script or manual DevTools pass |
| 8 | Icon System | ~70% (Scribe pin advance done) | Inline ⚠ in textContent + index.html emoji (pinned) |
| 9 | Portal Onboarding Tour | No progress | Full implementation |
| 10 | Print-Ready Report Layout | No progress | @media print CSS + button |

## Recommended Sequencing (by dependency + effort)

**Tier 1 — Low effort, unblocks others (do first):**
1. **Goal 7 (Typography Audit)** — ~30 min. Write a small script that greps computed font-size values in ui/app.css + tokens.css and flags any not on the 5-step scale (24/18/15/14/12). This is a verification task, not a build task. If violations found, fix them (likely <10 lines). Acceptance test passes immediately after.
2. **Goal 10 (Print Layout)** — ~1h. Pure CSS: add `@media print` block to app.css hiding interactive elements, forcing white bg, adding page-break rules. Add one button in ops tab. No JS logic beyond `window.print()`. Self-contained, no dependencies.

**Tier 2 — Medium effort, independent:**
3. **Goal 4 (Empty States)** — ~1.5h. Four panels × (icon + message + CTA). Can reuse SVG icons from goal #8's icon set. Suggest building as a shared `renderEmptyState(panelId, config)` helper in core.js.
4. **Goal 6 (Skeleton Screens)** — ~1h. CSS-only shimmer animation + layout-matching divs. No JS needed beyond toggling a class during fetch. Investigation already done per pointer file.

**Tier 3 — Higher effort or has external dependency:**
5. **Goal 5 (Notification System)** — ~2h UI + depends on Mechanic building `/api/notifications` endpoint. Suggest building toast component against the mock shape in `designer-notification-integration-forecast.md`; wire to real endpoint when Mechanic ships it.
6. **Goal 8 (Icon System finish)** — ~1h remaining. Two sub-tasks: (a) replace inline ⚠ text indicators with `<span>` + SVG (requires touching error-rendering code paths in core.js), (b) index.html emoji requires pin advance (Scribe to handle). Suggest doing (a) now, deferring (b) until next pin cycle.

**Tier 4 — Blocked on external tool:**
7. **Goal 2 (Info Density screenshots)** — BLOCKED: needs a browser with DevTools for before/after comparison. All code work is done. Suggest: record as "code-complete, pending visual verification" and close when next non-sandbox seat runs the portal.

## Completion Estimate
- If Designer works sequentially through Tier 1→3: ~6h total → all goals closed except #2 (screenshot-gated) and #8b (pin-gated).
- Realistic with auto-loop cadence (one goal per pass): 4–5 more passes to reach 9/10 or 10/10.

## Risks
- Goal #8b (index.html emoji) requires pin advance — if Scribe is unavailable, this stalls. Mitigation: batch all remaining index.html changes into one pin cycle.
- Goal #5 depends on Mechanic's endpoint; if that slips, toast component can still be built and verified against mock data.

## Cross-Agent Dependencies
| Designer Goal | Depends On | Owner | Status |
|---|---|---|---|
| #5 Notifications | `/api/notifications` endpoint | Mechanic | Not yet built (forecast exists) |
| #8 Icons (index.html) | Pin advance | Scribe | Available this cycle |
| #2 Info Density | Browser screenshots | Any non-sandbox seat | Pending |

---
*This forecast is a synthesis of observed progress, not a directive. Designer owns sequencing decisions.*