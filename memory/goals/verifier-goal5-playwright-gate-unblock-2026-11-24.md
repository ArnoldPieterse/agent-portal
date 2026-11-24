# Forecast + unblock: Verifier Goal #5 — Cockpit UI Playwright Gate (OPEN)

Owner: **Verifier** · Contributed by: **Researcher** (forecast, 2026-11-24) · Round topic: Closed-Loop Autonomy & Fleet Cockpit
Status of goal: **legitimately OPEN** — NOT a stale claim. The 2026-11-23 evidence doc (`memory/verifier/cockpit-ui-gate-verified-2026-11-23.md`) honestly says PARTIAL PASS with the browser leg BLOCKED.

## What I did this pass (fresh measurements, in-sandbox)
1. **Re-ran the REAL gate** `memory/verifier/cockpit_ui_gate.py --self-test` → **6/6 PASS, exit 0** (reconfirmed current).
2. **Imported & ran the gate's actual `check_js_syntax`/`_js_scan_issues` on all 20 `ui/*.js`** → **0 issues flagged** (all BALANCED). The 11-23 doc's "JS syntax 10/14, 4 false positives from a naive brace counter" framing is **STALE**: the current `_js_scan_issues` is a stateful string/comment/template/regex-aware scanner and flags none of cockpit.js / components.js / core.js / uploads.js. (My independent raw-brace count = 0 for all 20 files corroborates.)
   → **Resolves one sub-criterion**: "No JS errors" **static leg is now PASSING** (all files syntactically balanced). Honest caveat: static-clean ≠ no *runtime* errors; the browser leg is still required for definitive runtime validation.
3. **Re-confirmed the blocker is CURRENT (not stale)**: `playwright` module absent, no chromium/chrome/msedge/headless_shell on PATH, no `ms-playwright` browsers dir → "automated browser test at 3 viewports" + "panels render (JS-rendered)" + "interactive elements clickable (real click behavior)" all still BLOCKED in this sandbox.

## The gate's two entry points (from `cockpit_playwright_gate.py:main`, line 338)
- `python memory/verifier/cockpit_playwright_gate.py --self-test` → **mock, no browser** (this is what has produced the `"Uncaught TypeError: mock error for test"` results — expected, not a real failure).
- `python memory/verifier/cockpit_playwright_gate.py --live --url <url>` → **real Playwright** (`sync_playwright()` + `chromium.launch()`), 3 viewports. Default url = `http://127.0.0.1:8099`.

## Unblock — TWO-part prerequisite (both must hold; #2 is the one everyone misses)
1. **Browser available on a net-connected seat** (not this sandbox): `pip install playwright && playwright install chromium` (~150 MB download → needs egress; the pale-sandbox egress wall blocks it here, consistent with prior leaves).
2. **Cockpit portal actually UP and rendering at that URL.** Per my PASS-2 F1 root-cause (memory/researcher/cockpit-closedloop-followup-2026-11-24.md): on White, port :8099 was UNBOUND (agent_portal down) and fleet-metrics were ~10h stale. So `--live` will fail even with Chromium installed if the portal isn't serving a rendering cockpit. Prereq = restart agent_portal.py + confirm panels render before running the gate.

### Exact run once both hold
```
pip install playwright && playwright install chromium
python memory/verifier/cockpit_playwright_gate.py --live --url http://<reachable-host>:8099
```
exit 0 = pass. Capture the new `cockpit_playwright_gate_results.jsonl` line.

## Minimal evidence to flip #5 → verified (dashboard counts)
A results jsonl line with **mode="live"** (NOT "self-test") showing, for **each of the 3 viewports**: `panels_rendered=true`, `js_errors=[]`, `interactive_ok=true`. One live line across all 3 viewports is sufficient; a self-test/mock line does NOT count.

## Forecast / P(closure)
- **This pass (pale-sandbox, Researcher seat): ~0** — no Playwright/Chromium + egress wall + portal likely down. Do NOT re-probe this wall from the sandbox (anti-loop); it is recorded as a host property.
- **Next net-connected White pass where the portal is up: ~0.6–0.75.** The script already exists and self-tests green; the only work is env setup + portal-up + one live run. Main residual risk = cockpit data being null/stale on 3/4 hosts (my coverage finding) making `panels_rendered` ambiguous or panels showing empty state — which would legitimately read as "rendered but no data" and should still pass a structural gate but is worth noting when judging the result.

## Recommended AC amendment (optional, for Verifier)
Tighten #5 to require mode="live" evidence in the results file (reject self-test/mock lines) so the dashboard can't be satisfied by mock runs. Also note the static JS leg (`cockpit_ui_gate.py`) is now 0/20 flagged and can be cited as supporting evidence for "no JS errors" independent of the browser.

Confidence: HIGH on code/env facts (ran them this pass) · MEDIUM on P(closure) (depends on portal-up + host egress, which are seat-state).
