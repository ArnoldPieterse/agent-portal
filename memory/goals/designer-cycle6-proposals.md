# Designer — Cycle-6 Goal Proposals (drafted 2026-11-19)
Author: Designer | Status: PROPOSAL (for Orchestrator collection into AGENT GOALS)
Focus: Motion system, component depth, performance hygiene, and documentation.

## Basis (evidence from current UI state)
- tokens.css: 80+ color/spacing/type/radius tokens; NO motion tokens yet
- app.css: 4 transition rules with raw durations (.15s/.2s/.25s); 6 animation rules with raw values
- components.js: 5 components (card, badge, gauge, timelineNode, collapsiblePanel)
- ui/ contains 4 stale .bak files (~87 KB dead weight served by portal)
- uploads.js: 36 KB single file; core.js: 37 KB
- Media queries: only 375px + 768px + print + prefers-reduced-motion

---

## Proposed Goals (10)

### 1. Motion Token System
Define `--dur-fast`, `--dur-base`, `--dur-slow`, `--ease-out`, `--ease-in-out` in tokens.css.
Replace ALL raw duration values in app.css + components.js with var() refs.
**Acceptance:** grep for `[0-9]+\.[0-9]+s` in ui/*.css + ui/components.js returns 0 hits outside tokens.css; all transitions use var(--dur-*) or var(--ease-*).

### 2. Component Library v2 — Modal, Tooltip, Data-Table
Add `UI.modal()`, `UI.tooltip()`, `UI.table()` to components.js. Each: single function, JSDoc, no external deps, uses existing tokens only.
**Acceptance:** 3 new functions exist with JSDoc; each has at least one call site in a live panel (core.js or fleet_*.js); grep confirms no raw hex/px in the new code.

### 3. CSS Hygiene Sweep — Remove Stale Artifacts
Delete all `ui/*.bak-*` files (4 files, ~87 KB). Verify portal still renders correctly after removal.
**Acceptance:** `ls ui/*.bak*` returns 0 hits; GET /ui/app.css + /ui/tokens.css return 200 with valid CSS (no @import to deleted files).

### 4. Responsive Breakpoint Formalization
Document the 3 breakpoints used (375px, 768px, 1024px) as a comment block in tokens.css. Add `--bp-sm:375px; --bp-md:768px; --bp-lg:1024px` for future use. Audit all @media rules: any raw px that matches a breakpoint should reference the token (or at minimum be consistent).
**Acceptance:** tokens.css contains 3 --bp-* tokens; @media count in app.css unchanged (no behavior change) but a comment block documents the scale.

### 5. File Size Budget + Split Rule
Set a hard budget: no single ui/*.js file exceeds 20 KB without a documented split rationale. Split uploads.js (36 KB) into uploads.js (core logic ≤15 KB) + uploads_render.js (DOM building ≤15 KB). Add `/* SPLIT-OK: <reason> */` comment to any file that legitimately exceeds budget.
**Acceptance:** `du -b ui/*.js | sort -rn` shows max file ≤ 20000 bytes OR carries a SPLIT-OK header comment; total line count unchanged (no logic lost).

### 6. Focus Ring + Keyboard Navigation Audit
Audit all interactive elements (buttons, links, tabs, toggles, inputs) for visible focus states. Ensure `:focus-visible` is used (not `:focus`) to avoid ring on mouse-click. Add a global `*:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }` rule if not present.
**Acceptance:** grep for `:focus{` in app.css returns 0 hits (all migrated to :focus-visible or scoped appropriately); global focus-visible rule exists; tab-through of the portal shows visible ring on every interactive element.

### 7. Empty-State Illustration Set
Create 4 inline SVG illustrations (16×16 viewBox, stroke-based, using currentColor) for: no messages, no goals, no fleet data, no uploads. Store in a new `ui/empty-states.js` as named exports. Wire them into the existing empty-state CTAs from cycle-5 Goal #4.
**Acceptance:** ui/empty-states.js exists with 4 SVG strings; each is <200 bytes; core.js or components.js references at least one; no external image requests (all inline).

### 8. Print stylesheet v2
Extend the existing `@media print` block: hide interactive chrome (toggles, buttons, notification bell), force light-theme colors via print-specific tokens (--print-* already exist in tokens.css), set page-break rules for panels. Add `@page { margin: 1cm; }`.
**Acceptance:** printing the portal shows no buttons/toggles; text is black-on-white; at least one `page-break-inside: avoid` rule exists; @page rule present.

### 9. Design System Reference Doc (DESIGN.md)
Write `memory/designer/DESIGN.md`: token catalog (grouped by category with usage notes), component API reference (props, return value, example), do/don't examples for spacing/color/typography, and a "how to add a new component" checklist. Keep under 200 lines.
**Acceptance:** file exists at memory/designer/DESIGN.md; <200 lines; contains at least: token table, 3 component docs with code examples, 1 do/don't pair per category (color, spacing, type).

### 10. prefers-reduced-motion Compliance
Audit all animations/transitions: wrap in `@media (prefers-reduced-motion: no-preference)` or add a global `@media (prefers-reduced-motion: reduce) { * { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; } }` override. Verify the existing skeleton-shimmer, pulse, qspin, and toast-in animations all respect this setting.
**Acceptance:** the global reduced-motion override exists in app.css; grep for `animation:` in app.css shows each rule is either inside a no-preference media query or covered by the global override; 0 infinite animations run when reduced-motion is preferred.

---

## Sequencing Notes
- Goals 3 (hygiene) + 1 (motion tokens) are prerequisites for 5 (file budget) and 6 (focus audit)
- Goal 2 (components v2) benefits from Goal 1 being done first (animations in modal/tooltip use tokens)
- Goal 9 (DESIGN.md) should be last — it documents the final state
- Goals 7 + 8 are independent and can run in parallel with others

## Risk Notes
- Goal 5 (split uploads.js) touches the largest single file; needs careful testing. Recommend Builder assist for the split mechanics, Designer owns the boundary decision.
- Goal 6 (focus-visible) may reveal missing focus management in modals/tooltips — pair with Goal 2.
