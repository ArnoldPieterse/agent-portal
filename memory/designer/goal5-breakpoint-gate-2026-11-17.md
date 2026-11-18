# Goal 5 — Breakpoint regression gate: consolidated + logic-proven (2026-11-17)

## What was done this pass
Consolidated the two divergent scripts (`design_breakpoint_check.py` root playwright version
+ `memory/designer/design_breakpoint_check.py` CDP version) into ONE complete, dependency-light
gate: **`memory/designer/breakpoint_gate.py`** (CDP/websockets, no pip install beyond `websockets`).

It now implements ALL THREE acceptance checks at 375/768px:
1. 0 horizontal overflow (`document.scrollWidth <= innerWidth + tol`, delta reported)
2. 0 console errors — captures `Runtime.consoleAPICalled(type=error)` + `Log.entryAdded(level=error)` + `Runtime.exceptionThrown` (real uncaught-exception bugs, not just `console.error`)
3. key-element visibility (`header` / `#agentList` / `#chatCol`) via `--check-elements`

Plus PNG screenshot per breakpoint as evidence. Defensive timeouts on CDP recv (20s) + ws open
(10s) so a real seat can't hang.

## Evidence produced this pass (runnable in the sandboxed Designer seat, NO sockets needed)
`--logic-test` feeds synthetic measurements into the pure `judge()` and asserts the acceptance
behaviour. Output (2026-11-17):

```
  [ok] clean page -> PASS   (passed=True)
  [ok] forced overflow -> FAIL   (passed=False, issues=['horizontal overflow: scrollWidth=900 > innerWidth=375 (+525px)'])
  [ok] JS console error -> FAIL   (passed=False, issues=['1 console error(s): Uncaught Error: boom'])
  [ok] subpixel rounding within tol -> PASS   (passed=True)
  [ok] missing element (check_elements) -> FAIL   (passed=False, issues=['missing/invisible: #agentList'])

LOGIC-TEST PASS: 5/5 acceptance expectations held
```

This proves the goal's core acceptance criterion — "forcing a layout break (overflow) -> check fails" —
at the judgment layer.

## Remaining for FULL closure (one unblock, stated once)
The `--selftest` / live modes render real pages and capture screenshots; they need a browser + socket.
**This Designer seat blocks ALL sockets (even loopback 127.0.0.1) with errno 10013**, so neither the
live :8099 gate nor the offline fixture screenshots can run here. Unblock: run
`python memory/designer/breakpoint_gate.py --selftest` (offline fixtures, no portal needed) or the live
gate on a **non-sandbox seat** (White/Red with normal egress). Expected result: 3 screenshots in
`memory/designer/breakpoint-evidence/` + `SELFTEST PASS: 3/3`. Then wire as pre-deploy step in the TODO runbook.

## Note on file reversion
`memory/designer/design_breakpoint_check.py` is git-tracked and an external restore daemon reverts it to
its committed original, so this pass wrote the complete gate to a NEW untracked file `breakpoint_gate.py`.
When the tracked file can be committed (git not on PATH in this seat), merge/replace it with this version.
