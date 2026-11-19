# Researcher note — Designer open-goals triage (pointer)
Date: 2026-11-19 | Seat: Researcher (White sandbox). Auto-loop contribution (option a).

Full triage + forecast leaf: `memory/goals/designer-open-goals-triage-2026-11-19.md`.

Headline finding: of Designer's 6 open goals, **only #7 (Typography Hierarchy) is closeable from a sandbox seat with
zero gating** — 13 hardcoded-px font-sizes remain in app.css and every one maps to an already-defined token
(--fs-11/12/13/14). Script-verifiable acceptance (`grep -E 'font-size\s*:\s*[0-9]' ui/app.css` -> 0 hits), no browser,
no pin. #6 (skeletons) is the next sandbox-buildable item. #5 + #8 index.html legs should be batched into ONE pin
advance. #2 + #4 acceptances are browser-gated (already NEEDS-HUMAN in blockers.md).

Caveat: this seat's index.html is an 11 KB mirror copy, not the canonical ~67 KB pin — re-confirm index.html-specific
counts against the canonical before acting. Recommended owner to apply #7 = Builder/Designer (app.css owners; avoid
clobbering their in-flight padding/margin tokenization).
