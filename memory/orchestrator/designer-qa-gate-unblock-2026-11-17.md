# Designer QA-gate unblock + stale-claim findings (Orchestrator assist)
Parent: memory/INDEX.md | Lane: orchestrator (assisting designer)
Date: 2026-11-17 | Seat: Orchestrator (auto-loop option d: concrete step on Designer's open goals; human: "everyone help out designer")

## A. FIXED — design_check.py crash (Goal #10 gate could not run at all)
File: memory/designer/design_check.py line 27.
Bug: motion-budget regex `(?:transition|animation)[^;]*?([\d.]+)s` captured a bare `.`
(no digit) -> `float('.')` raised ValueError and aborted the whole gate before any report.
Reproduced in-sandbox: old capture set = ['.2','1.3','.','.9']; the '.' was the crash.
Fix (minimal, preserves lazy-quantifier detection semantics): number pattern now requires >=1 digit:
  re.findall(r'(?:transition|animation)[^;]*?(\d+(?:\.\d+)?|\.\d+)s', css)
Verified after fix (ran in-sandbox): gate runs to completion. Motion budget = OK
(1.3s pulse + 0.9s qspin correctly exempted). focus-visible=4, reduced-motion guard present,
status-dot 3 states, theme-toggle JS present. Credit: Designer authored the gate; Orchestrator fixed only the crash.

## B. TWO REMAINING design_check.py FLAGS ARE GATE-LOGIC FALSE POSITIVES (Designer to decide)
Gate still exits FAIL on 2 items that are not real design violations (Goal #2 dark mode is already verified):
1. "[data-theme="light"] token override block missing" -> app.css line 21 uses `[data-theme="dark"]`
   as the override with `:root` as the light DEFAULT (no explicit light block by design).
   Suggested one-line fix: check for `[data-theme="dark"]` (the real override) OR treat `:root` as the light baseline.
2. "NO @media(prefers-color-scheme) fallback" -> that fallback lives in core.js (themeToggle IIFE reads
   prefers-color-scheme), NOT in app.css, so a CSS-only check is wrong.
   Suggested fix: also grep ui/core.js for `prefers-color-scheme`, or downgrade the CSS-only miss to [info].

## C. GOAL #8 — HOT NOTE "fixed" IS STALE vs disk (sole blocker to closing #8)
Ran memory/designer/goal8_typography_check.py in-sandbox -> FAIL (1 violation):
   #actBody: line-height 1.7 outside [1.2,1.6]   (ui/app.css line 166, confirmed on disk)
All other #8 criteria PASS: uppercase letter-spacing 0.06em (x2 ok); font-weight steps {400,600,700}=3 ok.
HOT NOTE "Goal #8 typography done: fixed line-heights (#attach, #actBody)" does NOT match disk — #actBody is still 1.7.
Designer decision (ui/app.css is his pinned file; Orchestrator did NOT edit it): lower #actBody to <=1.6,
OR add #actBody to the script's documented text-exception list if 1.7 is intentional for the monospace log panel.

## D. RECURRING BLOCKER logged as NEEDS-HUMAN (memory/ops/blockers.md)
The *computed-style dump / axe-Lighthouse / CDP-screenshot* verification legs of Designer #5 and #7
cannot run from a White sandbox seat (no browser binary; sockets blocked, WinError 10013). Logged once.

## Net effect for Designer
- #10 gate: un-crashed + 2 false-positive checks flagged -> one small logic tweak gets it to "0 violations on current CSS".
- #8: single remaining violation identified with exact line + two fix options -> closable in one edit + re-run of goal8_typography_check.py.
