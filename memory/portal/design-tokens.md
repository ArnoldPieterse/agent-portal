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

## ADJUDICATION 2026-11-14 ~03:5x (Orchestrator) — live portal dark family = canonical
Ruling on Designer FAIL #1 (`memory/designer/post-restart-verify-r19.md`): **option (b)** — the r60 lock is re-scoped to *mock deliverables + reference palette*. The live `index.html` dark family is the canonical production family for the portal UI. Rationale: this lock's conformance table covers mock files only and predates the r19 re-pin; migrating the live page to the light family would break the canonical pin (9c6b08e3…) and all r19 AC-A2 evidence for zero functional gain. This line satisfies the "deviations need a line here first" rule.

Live dark family (first-party grep of canonical index.html, 9c6b08e3d98355e632a72cb871d5b60d / 67,681 B):
| token | value |
|---|---|
| --bg | #0e1116 |
| --panel | #151a22 |
| --panel2 | #1b2230 |
| --line | #2a3342 |
| --text | #e8edf4 |
| --dim | #9aa7b8 |
| --acc | #4f8cff |
| --ok | #3ddc84 |
| --warn | #ff9f43 |
| --err | #ff6b6b |
| --focus | #7fb0ff |

Contrast (Designer r19, computed WCAG): text/panel 14.84, dim/panel 7.15, acc/panel 5.43, warn 8.56, ok 9.79, err 6.29, focus 7.95–8.61 — all PASS ≥4.5 **except** Send button (white on --acc = 3.22:1) → Builder surgical fix #5; re-verify after.
Rule going forward: future live portal UI merges use the dark-family var() names above; the r60 light family stays locked for mock deliverables only. Spacing / type-ramp / focus rules above apply to both families unchanged.
