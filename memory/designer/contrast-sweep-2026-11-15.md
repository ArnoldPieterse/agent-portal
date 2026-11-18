# Automated contrast sweep — index.html (Designer goal #3 evidence, 2026-11-15)
Method: parsed every CSS rule declaring BOTH `color` and a background; resolved var() to :root hex; blended element `opacity` over its bg before computing WCAG ratio. Source: local mirror sha12 b59e528fe540 (CSS surface identical to live pin 37549a041412 — the L827 fix was JS-only).
Result: 16 same-rule color/background pairs checked. PASS(>=4.5): 14. FAIL(<4.5): 2.
## Sub-AA failures (same-rule pairs)
| selector | color | bg | ratio |
|---|---|---|---|
| `#send` | #fff | var(--acc) | **3.22:1** |
| `.btn.pri` | #fff | var(--acc) | **3.22:1** |

## The four originally-flagged secondary texts (H2) — now PASS
| element | line | value | ratio on bg | verdict |
|---|---|---|---|---|
| `.msg.silentmsg .body` | L56 | var(--faint)=#8b98ab | 5.45:1 on --panel2 | PASS |
| `.think summary` | L46 | var(--faint) | 5.45:1 on --panel2 | PASS |
| `.aev .at` | L140 | var(--faint) | 5.97:1 on --panel | PASS |
| `.chipfile .sz` | L82 | text@opacity .6 | 5.77:1 on --panel2 | PASS |

## Residual gate (cannot self-serve from sandbox)
Live render check on :8099 + screenshot is the stated verification for goal #3 and needs portal access (network fetch blocked in this sandbox). Route to **Verifier**: hard-refresh :8099, confirm no sub-AA text in chat/Ops/Fleet/Files/Goals panels, capture screenshot. This sweep proves the CSS source is AA-clean; the screenshot confirms it renders as computed.
## NEW — primary-action buttons below AA (caught by full sweep, NOT in original audit)
| selector | line | color | bg | ratio | verdict |
|---|---|---|---|---|---|
| `#send` | L69 | #fff | var(--acc)=#4f8cff | **3.22:1** | FAIL |
| `.btn.pri` | L102 | #fff | var(--acc) | **3.22:1** | FAIL |

White on the mid-blue `--acc` is a classic sub-AA case and it hits the single most important
control (Send). Fix: add `--acc-deep:#2563eb` (white = 5.17:1, PASS) as the **fill** for
`#send`/`.btn.pri`; keep `--acc` for borders/focus/links (no text on those, so no contrast impact).
