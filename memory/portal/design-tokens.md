# Portal design tokens (LOCKED 2026-11-13 r60)
Owner: Designer. Every future portal UI merge must use these tokens; deviations need a line here first.

## Color (family palette — inherited from increment 1/2 mocks)
| token | value | role | contrast on --surface |
|---|---|---|---|
| --bg | #F4F5FA | page background | — |
| --surface | #FFFFFF | panels/cards | — |
| --ink | #1A2233 | primary text | 15.90:1 PASS |
| --muted | #5C6478 | secondary text, hashes, labels | 5.92:1 on surface / 5.43:1 on bg — PASS |
| --line | #DDE1EC | borders, dividers | n/a (non-text) |
| --focus | #3949AB | focus ring only (functional, not an accent) | 7.73:1 |
| --accent-1 | #2E7D32 | primary action / success marker | 5.13:1; white on it 5.13:1 — PASS |
| --accent-2 | #8F5200 | warn / git-modified marker | 6.22:1 — PASS |

**Rule: max 2 accents per view** (here green + amber). Agent monogram colors (IDENTITY table) are data colors, not UI accents — they may appear in chips only.

## Spacing scale (px)
4 / 8 / 12 / 16 / 24. No other values; gaps between toolbar zones = 14 (existing exception, documented in increment2.md D1).

## Type ramp
- base: 15px / 1.45, system-ui stack
- h2 panel title: 16px / 600
- h3 section label: 12px / 600, uppercase, letter-spacing .08em, --muted
- mono (git log, status, results): 13px, ui-monospace/Consolas
- pills/tags: 11–13px

## Focus & interaction
- `:focus-visible` → `outline: 2px solid var(--focus); outline-offset: 2px` on EVERY control (buttons, inputs, checkboxes, links).
- Inputs: same 2px --focus outline on focus; border-color also switches to --focus.
- Result/status lines: `role="status" aria-live="polite"`; every action gives a text confirmation (no color-only feedback).

## Deliverable conformance (grep-verifiable)
| file | status |
|---|---|
| ws-b-increment1/index.html | conforming — family :root block, single NAMED_ARM_MS constant |
| designer/increment2-portal-mock.html | conforming — same :root tokens, named constants only |
| designer/files-panel-patch.md | patch doc — references var() names; verify at merge (Builder) |
| designer/ops-panel-mock.html | conforming — built on this lock 2026-11-13 r60; all text pairs ≥4.5:1 verified by computation (table above) |

## Notes for Verifier
- Contrast values computed, not eyeballed: relative-luminance formula, WCAG 2.x AA = 4.5:1 for normal text.
- The ops mock ships with labeled demo data; the only real datum is baseline hash `8f5e7d5` and the first-run prune summary (7 sections / 28 items / 58 lines).
