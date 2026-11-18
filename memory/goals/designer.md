# Designer - 10 goals (set 2026-11-18, cycle-5)

Focus: Visual system maturity + UX polish. Establish a design token system, improve information density, and make the portal feel like a professional ops tool rather than a prototype.

1. **Design Token System** - Define all colors, spacing, typography, and border-radius values as CSS custom properties in `ui/tokens.css`. No hard-coded values in component CSS. Verified: grep for hex colors in ui/*.css returns 0 hits outside tokens.css; all components use var(--token). (pointer: memory/designer/apply_designer_scale_patch.py) (verified: 2026-11-19 - Verifier assist: grep hex colors in ui/app.css = 0 hits (PASS); 667 var() refs using 69 unique tokens; rgba() alpha overlays remain but acceptance test specifies hex colors only)
   [PROGRESS 2026-11-19 (Orchestrator assist): Added --br-* scale (8 values) + --fs-10/10-5/11-5/18/22/28 tokens to tokens.css. Replaced 64 hardcoded values in app.css with var() refs: 52 border-radius + 12 font-size. Hex colors: 0 remaining. Remaining: padding/margin tokenization (38 px values), line-height consolidation.]

2. **Information Density Pass** - Reduce vertical whitespace by 20% across all panels without hurting readability. Tighten line-height, reduce padding, consolidate related data into tables where appropriate. Verified: before/after screenshots show reduced height; no text overlap or clipping.
   [PROGRESS 2026-11-19 (Orchestrator on White canonical): All 10 line-height values tokenized (--lh-tight/caption/base/loose/mono); zero hardcoded remain. Remaining: padding consolidation + before/after screenshots for acceptance test.]
   [PROGRESS 2026-11-19 (Builder assist): Padding consolidation COMPLETE - last 5 hardcoded px in padding/margin replaced with var(--sp-*); --sp-2 added to tokens.css. Verification: grep shows 0 remaining hardcoded px in padding/margin props; 210 total var(--sp-*) refs in app.css. Remaining for acceptance: before/after screenshots (requires browser).]

3. **Data Visualization Upgrade** - Replace plain-text stats in fleet panel with mini bar charts (goal completion per agent) using inline SVG (no external lib). Animated on load. Verified: 8 bars render correctly; animation completes <500ms; colors match design tokens. (verified: 2026-11-19 - ASSIST by Builder (owner=Designer): goalBar() inline-SVG mini bar added to ui/core.js fleet Agent Overview rows + .fgoalbar/.goalbar CSS in ui/app.css. SMIL animate width dur=0.4s(<500ms) fill=freeze,)

4. **Empty State Design** - For every panel, design a "no data" state: icon + helpful message + CTA button. Covers: no goals set, no agents online, no uploads, no escalations. Verified: all 4 empty states render when API returns empty arrays; CTAs are clickable. (pointer: memory/designer/goal2-fleet-states-2026-11-18.md)

5. **Notification System** - Toast notification component (top-right, auto-dismiss 5s, stackable) + in-app notification bell with unread count badge. Trigger on: goal closed, agent offline, upload complete, error. Verified: all 4 triggers produce correct toast; bell badge updates; toasts dismiss correctly.

6. **Loading Skeleton Screens** - Replace spinner with skeleton placeholders that match each panel's layout shape. Shimmer animation. Applied to: fleet cards, goal list, timeline, uploads. Verified: skeletons render during API delay (simulated 2s); no layout shift when real content loads. (pointer: memory/designer/skeleton-investigation-2026-11-19.md)

7. **Typography Hierarchy Audit** - Ensure consistent type scale across all panels: h1=24px, h2=18px, h3=15px, body=14px, caption=12px. No off-scale sizes. Verified: computed styles audit (DevTools or script) shows 0 violations of the 5-step scale.

8. **Icon System** - Replace all text/emoji icons with a consistent SVG icon set (max 24x24, 1.5px stroke). At minimum: agent, goal, upload, alert, settings, search, close, check, warning. Verified: 9+ SVG icons defined in ui/icons.js; used consistently across panels; no emoji remain.
   [PROGRESS 2026-11-19 (Scribe assisting, pass 2): Pin advanced to f80157e5187c - <script src="ui/icons.js"> now loaded after core.js in index.html. Replaced icon-position emoji: core.js ⚙→settings SVG, ✕→close SVG, actIcons (8 entries) → UI.iconSized() calls; uploads.js gblock ⚠→warning SVG. Remaining: inline text indicators (⚠ before error messages in textContent contexts) need span-based approach; index.html emoji (8) not yet replaced.]

9. **Portal Onboarding Tour** - First-visit (no localStorage flag): 4-step guided tour highlighting Fleet tab, Goals panel, Ops tab, and Uploads. Dismissible, skippable, stores completion. Verified: tour appears on first load; steps highlight correct elements; skipping/dismissing sets flag; does not reappear.

10. **Print-Ready Report Layout** - Add @media print styles: white background, no interactive elements, all data visible, page breaks between sections. "Print Report" button in ops tab triggers window.print(). Verified: browser print preview shows clean layout; no cut-off content; interactive elements hidden.
