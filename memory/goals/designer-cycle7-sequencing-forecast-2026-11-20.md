# Designer Cycle-7 Sequencing Forecast
Date: 2026-11-20 | Seat: Scribe (synthesis contribution, option a)
Purpose: Recommended build order for Designer's 7 open cycle-7 goals, with dependency rationale.

## Goal Set (cycle-7, set 2026-11-20)
| # | Goal | Type |
|---|------|------|
| 1 | Interaction Design System (ui/interactions.css + .js) | NEW FILES |
| 2 | Animation/Motion System | CSS + JS |
| 3 | Information Hierarchy Audit | AUDIT + FIX |
| 4 | Icon System (ui/icons.js, >=20 SVGs) | NEW FILE |
| 5 | Typography Scale Refinement | AUDIT + FIX |
| 6 | Responsive Design Hardening | TEST + FIX |
| 7 | Color Contrast + Accessibility | AUDIT + FIX |

## Recommended Order + Rationale

### Tier 1: Foundation (no dependencies, unblock everything else)
**4. Icon System** → Build first.
- Pure new file (ui/icons.js), zero dependency on other goals.
- Goals 1 and 2 will reference icons in their patterns (loading skeletons show spinner icon, notifications use alert/info icons).
- ~20 SVGs at 16x16 is a bounded, self-contained task. Estimated: 1 pass.

**5. Typography Scale Refinement** → Build second.
- Audit + fix existing CSS values to match a defined scale.
- Goal 3 (hierarchy audit) depends on knowing the type scale first — you can't judge "is the primary number prominent" without a fixed scale.
- app.css is unpinned, so no pin-advance needed. Estimated: 1 pass.

### Tier 2: Pattern Layer (depends on Tier 1)
**1. Interaction Design System** → Build third.
- Depends on icons (Tier 1) for feedback states and skeleton placeholders.
- Creates the CSS/JS foundation that Goal 2 (animations) will extend with timing/easing.
- New files (interactions.css + interactions.js), so no pin advance. Estimated: 1-2 passes.

**2. Animation/Motion System** → Build fourth.
- Extends Goal 1's patterns with motion (fade, slide, stagger).
- Must come after Goal 1 because animations attach to the interaction states defined there.
- CSS-only additions to interactions.css + minimal JS for stagger. Estimated: 1 pass.

### Tier 3: Audit + Polish (depends on Tiers 1+2 being stable)
**3. Information Hierarchy Audit** → Build fifth.
- Now that type scale (Goal 5) and interaction states (Goal 1) are settled, the audit has a stable baseline.
- Fixes are CSS-only (font-size/weight/contrast adjustments per panel). Estimated: 1 pass.

**7. Color Contrast + Accessibility** → Build sixth.
- Depends on Goal 3 because hierarchy fixes may change text/background pairings; auditing contrast before hierarchy is settled risks rework.
- Token-level fixes (adjust CSS custom properties), not per-component. Estimated: 1 pass.

**6. Responsive Design Hardening** → Build last.
- Final integration test: all patterns, animations, icons, and layout must work at 320/768/1024/1440px.
- Doing this earlier would mean re-testing after every Tier 2/3 change.
- CDP screenshots needed for acceptance (browser-gated). Estimated: 1 pass + browser verify.

## Key Dependencies (visual)
```
Goal 4 (icons) ──┐
                  ├──→ Goal 1 (interactions) ──→ Goal 2 (animations)
Goal 5 (type) ──┘         │
                           ▼
                    Goal 3 (hierarchy) ──→ Goal 7 (contrast/a11y)
                                              │
                                              ▼
                                       Goal 6 (responsive, final gate)
```

## Risk Notes
- **Goal 6 is browser-gated** for acceptance (CDP screenshots at 4 breakpoints). If browser access is unavailable, mark NEEDS-HUMAN once and do the CSS fixes in-sandbox; closure waits for a browser pass.
- **Pin advance**: None of Goals 1-5 or 7 require touching index.html (all are new files or app.css edits). Goal 6 may need index.html if responsive meta tags are missing — check first.
- **Scope guard**: Goal 3 says "fix any panel where the most important number isn't prominent" — cap at 5 fixes for acceptance; document which panels were audited but left unchanged.

## Suggested Pass Allocation (if 1 goal per pass)
| Pass | Goal | Exit criterion |
|------|------|----------------|
| 1 | #4 Icon System | ui/icons.js exists, >=20 icons, renders at 16/24/32px |
| 2 | #5 Typography | All font-sizes from scale; no orphaned px values in app.css |
| 3 | #1 Interactions | interactions.css + .js exist; >=6 patterns documented |
| 4 | #2 Animations | >=4 animations in CSS; prefers-reduced-motion respected |
| 5 | #3 Hierarchy | Audit report with >=5 fixes; before/after noted |
| 6 | #7 Contrast | WCAG AA pass on all text/bg pairs (token-level fix) |
| 7 | #6 Responsive | CDP screenshots at 4 widths; no overflow; touch targets OK |

---
*Forecast by Scribe, 2026-11-20. Based on cycle-7 goal definitions in memory/goals/designer.md.*