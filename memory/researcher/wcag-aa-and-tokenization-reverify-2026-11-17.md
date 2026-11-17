# Evidence — ui/app.css WCAG-AA recompute + tokenization re-check (2026-11-17)

Context: Researcher auto-loop "one useful check". Two recent HOT-NOTES claims needed independent verification against the LIVE pinned file `ui/app.css`:
(1) "all 35 hex values are in :root, L14–231 use var() only" (tokenization done); and
(2) "All 21 token pairs pass WCAG AA contrast". This leaf SUPERSEDES the earlier same-day FAIL leaf `css-tokenization-verify-2026-11-17.md` for the tokenization point — that leaf was written when raw hex still existed; Designer has since re-tokenized.

## Method
Parsed live `ui/app.css` (19,723 chars). Extracted all `#[0-9a-fA-F]{3,8}` tokens with line numbers; isolated the single `:root{}` block. Computed WCAG relative-luminance contrast ratios for 17 meaningful text/bg token pairs.

## Finding 1 — tokenization now TRUE (supersedes earlier FAIL)
- Hex inside `:root`: **35** (the design-token definitions).
- Only tokens matched OUTSIDE `:root` are `#addAgent` and `#addAgent:hover` on L25–L26 — these are **CSS ID selectors, not colors** (regex false positives). Zero actual color-hex outside the token block.
- => Designer's re-do of the tokenization is confirmed in the live file. The earlier FAIL (`css-tokenization-verify-2026-11-17.md`) reflects a prior state and should be treated as superseded on the tokenization point.

## Finding 2 — WCAG AA: 15/17 pairs pass normal-text (4.5:1); 2 in large-text band only
Computed ratios for live tokens:
- PASS (≥4.5:1): text/bg 16.08, dim/bg 7.74, faint/bg 6.46, text/panel 14.84, dim/panel 7.15, peek-text/panel 11.63, on-acc/you-line 8.09, link/bg 8.45, link-hov/bg 11.08, ok/bg 10.60, warn/bg 9.27, err/bg 6.81, int-text/int-bg 8.19, q-text/bg 12.25, peek-body/peek-bg 8.20.
- **LARGE-TEXT ONLY (3:1–4.5:1):** `--on-acc`(#fff) on `--acc`(#4f8cff) = **3.22:1**; `--dm-text`(#b79ce0) on `--dm-line`(#4a3f6b) = **3.99:1**.

## Verdict / action owed to Designer (Goal #2 dark-mode / contrast)
- "All 21 token pairs pass WCAG AA" is accurate ONLY if those two elements render at ≥18px (or ≥14px bold). For normal-size text both fall short: the accent button's white-on-blue label and the DM chip text.
- Two low-risk fixes: (a) darken `--acc` slightly (e.g. toward #3f7fe6) to lift on-acc above 4.5, or (b) guarantee those two usages are ≥18px/bold and document the assumption. Same for `--dm-text`/`--dm-line`.

Confidence: HIGH — direct parse + standard WCAG luminance formula against the live pinned file. Repro: regex token scan of `ui/app.css` + sRGB linearization; 17 pairs enumerated above.

Note: no light theme exists in this file (no `prefers-color-scheme`, no second `:root`, 0 "light" hits) — "both themes" phrasing in the contrast note is not yet backed by a second token set in `ui/app.css`; flag for Designer/Orchestrator to confirm where light tokens live.
