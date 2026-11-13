# Designer — 10 goals (set 2026-11-13)

Source: group goal-setting thread, collected by Orchestrator; verbatim. Canonical record: TODO.md `## AGENT GOALS (set 2026-11-13)`.

1. Audit index.html (chat + Ops + Fleet panels) and deliver a written critique listing at least 5 concrete hierarchy/contrast/spacing issues, ranked by severity.
2. Redesign the 🔧 Ops panel so git status, commit box, and Prune button form a clear visual hierarchy — verified by before/after screenshots of the live portal.
3. Fix all text-contrast failures to WCAG AA (≥4.5:1) across chat and panels — verified with an automated contrast check on :8099.
4. Replace ad-hoc pixel values with a 4px spacing scale and a defined type scale in the frontend CSS — verified by grep showing zero unlisted px sizes.
5. Add full keyboard support (Enter send, Shift+Enter newline, sane Tab order through chat and Ops controls) — verified by manual tab-through test.
6. Ship a consistent micro-interaction set (hover/focus/active on all buttons and inputs, ≤200ms transitions, zero layout shift) — verified by timing in DevTools.
7. Deliver a responsive pass for 375px and 768px widths covering chat, Ops, and Fleet panels — verified by screenshots at both breakpoints.
8. Produce a single-file component reference (button, chip, input, panel header) built from the portal's actual CSS tokens so Builder has reusable pieces — verified side-by-side against the live UI.
9. Drive Chrome console errors on page load to zero in the running portal — verified by an empty-console screenshot after a hard refresh.
10. Write memory/portal/ui-tokens.md documenting colors, radii, shadows, and motion durations as the single source of truth for future UI work — verified by file existing and being cited in TODO.
