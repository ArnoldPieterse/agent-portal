# Designer — 10 Proposed Goals (set 2026-11-16, next cycle)

Theme: from one-off fixes to a repeatable design system with an automated quality gate.
Built on completed arc: audit → contrast fix → tokens → keyboard support → micro-interactions → responsive → components → zero-console → ui-tokens.md.

1. **Full Design Token Layer** — Extend the 4px spacing + type scale into a complete token set (color, radius, shadow, motion-duration) as CSS custom properties; document usage in `design-tokens.md` at repo root. Verified: grep confirms every hard-coded color/radius/duration replaced by `var(--token)`; `design-tokens.md` exists and is index-linked.

2. **Dark Mode + Theme Toggle** — Persistent dark/light theme driven by the token layer, header toggle, `prefers-color-scheme` fallback. No contrast regressions in either mode. Verified: screenshot pair (light/dark) on :8099; re-run WCAG AA script on both themes, 0 failures.

3. **Component Abstraction** — Extract `.msg`, `.panel-head`, `.btn-primary`, `.badge-status`, `.input-bar` as named classes; eliminate inline `style=` attributes from chat and panel elements. Verified: grep shows zero `style=` on those selectors; HTML line count drops ≥ 20%.

4. **Micro-interactions & Motion Budget** — CSS transitions on panel expand/collapse, message hover, button press. All animations ≤ 200ms; respect `prefers-reduced-motion`. Verified: manual interaction pass with before/after recording; computed transition-duration grep shows max 200ms.

5. **Responsive Layout (< 768px)** — Chat + Ops + Fleet panels stack vertically on narrow viewports; input bar pinned to viewport bottom. No horizontal overflow at 375px or 768px. Verified: screenshot at both widths via headless browser; DevTools overflow check = 0.

6. **Status Indicator System** — Consistent `.status-dot` component (green/amber/red + label) used across Fleet panel, Ops git status, and agent roster; replaces ad-hoc colored text. Verified: grep confirms `.status-dot` present in all three panels; no bare `color: green` / `color: red` remains.

7. **Focus Rings + ARIA Landmarks** — Visible 2px offset focus ring on every interactive element; panels wrapped in `<section aria-label>`; nav landmarks for screen-reader navigation. Verified: Lighthouse/axe accessibility score ≥ 95 on :8099; tab-through test shows no invisible focus.

8. **Typography Hierarchy Pass** — Enforce line-height 1.2–1.6 (headings vs body), letter-spacing +0.05em on uppercase labels, ≥ 3 meaningful font-weight steps. No element outside range. Verified: computed-style dump (script) confirms zero violations; visual before/after of a dense panel.

9. **Live Fleet Topology View** — SVG-based diagram rendering 3 hosts + agent nodes from `/api/net/fleet`; hover tooltips, click-to-expand detail card, live status color sync. Verified: screenshot showing all 3 hosts rendered with correct status colors after API poll; JS error console clean.

10. **Design QA Regression Gate** — `design-qa.md` checklist + automated script (`design-check.py`) that greps CSS for token violations, contrast failures, and missing focus styles; wired as a pre-deploy step reporting pass/fail. Verified: script runs against current CSS → 0 violations; TODO.md references it in the deploy runbook.

**Through-line:** Goals 1–3 establish the foundation (tokens → theme → components), 4–8 make the portal polished and accessible, 9 adds a new capability (live topology), 10 locks everything in with an automated gate so regressions are caught before deploy.
