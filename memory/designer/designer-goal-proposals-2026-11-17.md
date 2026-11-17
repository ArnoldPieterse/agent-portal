# Designer — 10 goals (set 2026-11-17)

Source: goal-setting round post-cycle-2 (2026-11-17). Builds on cycle-2 completions: token layer, dark mode, component abstraction, breakpoint gate, a11y landmarks, typography pass, fleet topology SVG, design QA gate.

Cycle-3 theme: production polish + performance discipline. The portal is structurally sound; now it needs to be fast, resilient, and self-documenting.

---

1. CSS bundle performance budget - measure current ui/app.css + core.js + uploads.js total transfer size; target <80KB total (minified); identify top-5 largest rules/blocks and propose splits or removals. Verified: `python memory/designer/asset_budget_check.py` reports total size per file + grand total; PASS if <80KB, FAIL with named offenders otherwise; script wired into design_check.py as a final gate step.

2. Component documentation & usage guide - for each named component (.msg, .panel-head, .btn-primary, .badge-status, .input-bar, .status-dot): a one-paragraph "how to use" doc + a minimal HTML snippet showing the class + required children; assembled into memory/portal/component-reference.md (index-linked). Verified: file exists, grep confirms all 6 component names present with code blocks; a new agent can read it and correctly compose each component without trial-and-error.

3. Empty states & loading skeletons - design a consistent pattern for every data-driven panel: (a) skeleton shimmer while API is pending, (b) "no data" empty state with icon + message, (c) error state with retry button. Implement in ui/app.css as .skeleton, .empty-state, .error-state classes; apply to Fleet panel and Ops log. Verified: force network failure in DevTools -> panels show error state with retry; clear data -> empty state visible; no white-screen or bare spinner anywhere.

4. Print stylesheet - @media print block that produces a clean single-page report: hide chat input, collapse panels to headers + key stats, monospace for code blocks, 10pt body, page-break rules. Verified: browser print preview (Ctrl+P) shows no overflow, readable text, sensible page breaks; screenshot of print output saved as evidence.

5. Interaction feedback audit & fill - every clickable element must have a perceptible state change within 100ms (active/pressed state via scale, opacity, or background shift). Audit all buttons, links, and interactive divs; add missing :active states. Verified: grep confirms `:active` rule for every selector matching `[role="button"]`, `a.btn-*`, `.panel-head`; manual click-through shows no "dead" feeling on any element.

6. Error state design tokens + toast system - define --toast-duration, --toast-max-height, --error-banner-bg as tokens; implement a single-toast stack (max 3 visible, auto-dismiss 4s) in core.js using the token layer; wire to API error handlers. Verified: trigger 5 rapid API errors -> max 3 toasts visible, oldest dismissed first; each toast has close button and aria-live="polite"; no layout shift on toast appear/disappear.

7. Progressive panel hydration - Fleet topology SVG (40 nodes) and Ops git log are the heaviest DOM sections. Defer their rendering until the panel is scrolled into view (IntersectionObserver); show a lightweight placeholder (panel-head + skeleton) before hydration. Verified: initial DOM node count drops >=30% with panels collapsed; scrolling to Fleet panel triggers render within 200ms; no CLS shift on hydrate.

8. Design QA gate v2: add JS accessibility checks - extend design_check.py beyond CSS grep to also verify via headless run: (a) all interactive elements have accessible names, (b) zero console errors/warnings on load, (c) tab-order matches visual order (first 10 stops), (d) no element has both role="button" and <a> without href. Verified: script reports PASS/FAIL per check; deliberately break one (remove aria-label from a button) -> FAIL with the selector named.

9. Motion design language doc - document all existing transitions/animations in ui/app.css: selector, property, duration, easing, trigger context; define the motion vocabulary (fade-in, slide-up, scale-pulse) and when each is appropriate; set the rule "no new transition without a token reference." Verified: memory/portal/motion-language.md exists with a table of all current transitions + 3 named patterns; design_check.py adds a grep that fails if any transition-duration is not a var(--motion-*) reference.

10. Responsive density mode - at >=1280px, offer a "compact" toggle (persistent, like dark mode) that reduces --sp-* by 30% and --fs-body by 1 step; useful for dense fleet monitoring on large displays. Verified: toggle in header switches data-density="compact" on <html>; computed spacing values drop proportionally; WCAG contrast still passes at reduced sizes (min font >=12px); state persists across reload via localStorage.
