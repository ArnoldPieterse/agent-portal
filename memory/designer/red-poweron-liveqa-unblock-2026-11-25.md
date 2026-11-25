# Red power-on -> Designer deferred live-QA legs unblocked (2026-11-25)

**Trigger:** human: "red is powered on". Red = non-sandbox host with real egress + Chromium.
This clears the standing sandbox limitation that forced my cycle-17 goals **#5 (breakpoint
automation)** and **#7 (focus/ARIA a11y)** to close on STATIC structural verification only.
My lane is already 10/10 verified; this note converts those two static-only closures into
fully-verifiable ones with a single ready-to-run command (serves round topic: Fleet Autonomy
Convergence = closing the last visual-QA caveats so convergence is real, not static-only).

**Sandbox position (re-confirmed this pass, one probe):** this Designer sandbox seat has NO
network egress — `127.0.0.1:8099` and `Red` are both "not a literal the sandbox can check"
(same WinError 10013 / allowlist class as memory/ops/blockers.md). So Red being powered on
does NOT let THIS seat run the legs; it lets a NON-SANDBOX seat (Red itself / White ops /
RDP) do so. Do not re-probe egress from sandbox.

**Deliverable (built + syntax-verified this pass):** `memory/designer/live_qa_runner.py`
(185 lines, `py_compile` OK). One-shot headless Edge/Chrome over CDP that verifies ALL deferred
ACs in a single run and writes one evidence JSON:
  - G5: 0 horizontal overflow at 375px AND 768px + screenshots -> cdp-screenshots/liveqa-{w}px.png
  - G7: axe-core score >= 0.95 on :8099 (loads local axe.min.js, else CDN + caches it) + ARIA landmarks
  - shared: console errors == 0 across every load
  Output: `memory/designer/evidence-live-qa-red-<date>.json` with per-AC verdicts + ALL_PASS.
Reuses the exact CDP reader/cmd pattern from cdp_screenshot.py + d9_d7_verify_20261117.py.

**One-shot unblock (run on Red / White ops terminal / RDP, non-sandbox):**
    python memory/designer/live_qa_runner.py
On `ALL_PASS: true`: append the evidence JSON path as a live-QA supplement to goals #5 and #7
(static closures already stand; this is additive proof). On any leg FAIL: inspect the JSON for
the specific AC + screenshot, fix in ui/app.css / ui/core.js, repin (see PIN_FILES rule), re-run.

**Status:** runner READY. Awaiting a non-sandbox execution (Red now available). No regression to
existing 10/10 — static verification remains valid; this only upgrades two legs to live-verified.
