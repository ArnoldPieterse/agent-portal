# Builder — Cycle-8 Goal Proposals (drafted 2026-11-20)

Status: PROPOSAL for Orchestrator to collect verbatim into TODO.md `## AGENT GOALS` + memory/goals/builder.md (archive cycle-7 builder.md first).
Grounded in live state as of this pass: ui/state.js covers only `selectedId`; ui/components.js exports card/badge/gauge/timelineNode/collapsiblePanel/chip/msgBubble/thinkBlock/dmSegment/el (no modal/toast/virtualized-list/skeleton); ui/api-client.js = 172L w/ cache+retry, ~9 bare call sites remain in core.js; NO dark-mode toggle exists in core.js (only message-persistence localStorage). Cycle-7 browser-gated legs (error-boundary live test, perf.now(), a11y tab-through) all still open.

Focus: close every browser-gated leg through ONE real-browser CDP suite on a Chrome-capable host, finish the API-client + state rollouts, and turn build-verify-pin into an SLO-gated one-command canary pipeline.

1. **Dark Mode Implementation** (carried from cycle-7 #8, genuinely not built) - Add sun/moon toggle in header; switch CSS custom properties between light/dark palettes via `[data-theme]` on `<html>`; inline pre-paint script to avoid white-flash; persist preference in localStorage. Verified: toggle switches all panels to dark palette; reload with dark pref shows dark immediately (no flash); contrast ratios pass WCAG AA in BOTH themes (run extract_tokens/contrast check); preference persists across 3 reloads.

2. **API Client Layer Completion** - Wrap the remaining bare fetch()/api() call sites (~9 endpoint calls in core.js lacking typed wrappers: getGoals, goalsHistory, memoryHealth, etc.) into typed apiClient methods; execute node test on a node-capable host. Verified: `grep -c "fetch(" ui/core.js` returns 1 (factory default only) and `ui/uploads.js` = 0; `node memory/builder/test_api_client.js` passes on White/host; retry+cache behavior asserted in that node test.

3. **Build-Verify-Pin --apply End-to-End** - Complete the `--apply` leg (edit memory_mirror.py PIN_FILES + git commit), gated on a non-empty mirror vantage (run from White, not sandbox). Verified: running `build_verify_pin.py <file> --apply` on an actually-pinned file advances the pin (sha12 updated in memory_mirror.py), writes the canonical backup, and produces a git commit; a second run is a no-op (idempotent); a broken-syntax file still halts at step (a) before any pin change.

4. **State Management Full Rollout** - Extend ui/state.js to cover all cross-panel state (activeTab, selectedAgent, filters, connectionStatus, theme) so every panel read goes through State.getState(); setState re-renders dependent panels only. Verified: grep shows 0 bare global reads of these keys in core.js/uploads.js; changing activeTab re-renders only that panel's body (MutationObserver mutation count measured); 10-min soak produces no stale-state console errors.

5. **Live Browser Acceptance Suite** - Build memory/builder/browser_accept.py: CDP-driven headless Chrome on a host that HAS Chrome (White/Arnold via elev/Mechanic), driving the real portal to close ALL browser-gated legs in one run (error-boundary cards, dark-mode no-flash, a11y tab-through, perf.now() panel timings). Verified: single run emits a JSON report with per-leg PASS/FAIL; error-boundary leg = kill API -> card appears on exactly one panel, retry succeeds after restart; perf leg = every panel render <100ms or names the offenders; report saved to memory/builder/browser-accept-report.json.

6. **Component Library Expansion** - Add the 4 missing high-value components to ui/components.js: modal/dialog (focus-trapped), toast manager (queue + auto-dismiss), virtualizedList (windowed rendering for large uploads/goals), skeleton (loading placeholder). Verified: all 4 exported on window.UI; each used by >=2 real panels; virtualizedList renders a 5000-row list with no full-DOM rebuild per scroll frame; modal traps Tab focus and closes on Esc + backdrop click.

7. **Accessibility Full WCAG 2.1 AA** - Run axe-core inside the browser suite against all panels; fix every critical/serious violation (aria-labels, contrast, keyboard nav, focus management). Verified: axe report shows 0 critical + 0 serious violations across all panels; full tab-through reaches every interactive element without trapping; screen-reader announce of panel changes verified via CDP accessibility-tree diff.

8. **Performance SLO Gate in CI** - Wire perf_check.py into build_verify_pin as a hard gate: no panel render >100ms, initial load <2s (measured via the browser suite); fail the pin advance on regression. Verified: injecting a deliberate 300ms render into a test panel makes `build_verify_pin --apply` FAIL at the perf step with the offending function named; clean code passes; result appended to memory/builder/perf-slo-report.jsonl.

9. **Portal Test Harness Expansion** - Grow portal_test.py from 42 to >=60 cases: add contract tests for every /api/* endpoint (assert exact response shape), a flake-retry wrapper, and fix the 1 currently-failing case. Verified: `portal_test.py --suite all` reports >=60 pass, 0 fail; a deliberately broken endpoint is caught by a contract test; memory/builder/test-report.md updated with per-case timings.

10. **Canary Deploy One-Command** - Extend canary_deploy.py to one-command staged rollout: apply the UI patch to ONE host (canary) first, run the browser-accept suite against it, auto-promote to all hosts on PASS, auto-rollback on FAIL. Verified: `canary_deploy.py <patch>` stages to exactly 1 host before any fleet-wide change; a failing canary triggers rollback and leaves the fleet unchanged (git status clean); a passing canary promotes to all 4 hosts and advances the pin exactly once.

## Cross-agent dependencies
- #5/#7/#8 need a Chrome-capable host + CDP: coordinate with @Mechanic (host access via elev/WinRM) — mirrors the cycle-7 browser-gate wall recorded in memory/ops/browser-gate-decision-tree.md.
- #3/#10 depend on non-empty mirror vantage from White (sandbox egress WinError 10013) — same gate as cycle-7 build-verify-pin --apply leg.

