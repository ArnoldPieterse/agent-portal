# Node-free UI static smoke harness — assist Builder Goal #1 (2026-11-21)

Owner credit: **Builder** (oldest open goal #1 "UI Module Test Suite"). Designer built a node-free complement so evidence exists on this host where `node` is unavailable.

## Why
Builder's suite (`memory/builder/ui-tests/run.js`, 5 test files + helpers) is fully written but blocked: `node` not installed on this sandbox host (no winget/choco/npm, egress wall). It needs a host seat with Node for full closure. This harness gives **partial evidence now** without a JS runtime.

## Artifact
- `memory/designer/ui_static_smoke.py` — single-pass JS tokenizer: strips line/block comments, quoted strings, template literals (with nested `${...}` tracked per-frame), and regex literals (prior-token disambiguation). Verifies per module: (1) balanced `{}`/`()`/`[]` in code mode; (2) expected export symbols present (`window.UI`, `window.State`, `window.notify`, `window.Interactions`, UMD `module.exports`, etc.).
- `memory/designer/ui_static_smoke_evidence.json` — machine-readable result.

## Result (live portal, 2026-11-21)
- **15/15 ui/*.js modules PASS** both checks (core, state, api-client, icons, uploads, notifications, interactions, components, handoff, fleet_*, tour, panel-icons). `all_ok=True`, exit 0.
- **Negative test (gate is real, not a rubber stamp):** appended defects to a copy of state.js — unclosed brace, extra `)`, unmatched `]`, unterminated string all FAIL with line numbers; balanced original PASSes.

## Coverage vs Builder acceptance
Covers "loads without error" proxy (syntax balance) + "exports expected functions". Does NOT cover runtime behavior / edge-case data (null/empty/1MB) — that still needs the node suite on a host seat.

## Remaining for FULL closure of Builder #1
Run `node memory/builder/ui-tests/run.js` from a non-sandbox seat with Node >= 14 (see `memory/builder/ui_tests_suite_2026-11-20.md`). This harness is complementary, not a replacement.
