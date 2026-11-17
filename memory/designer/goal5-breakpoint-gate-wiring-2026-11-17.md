# Goal 5 — Pre-deploy gate wiring (2026-11-17)

## Status: Script complete + logic-verified; browser-run pending on non-sandbox seat.

## What's done
- `memory/designer/breakpoint_gate.py` — full CDP-based gate (375/768px, overflow+console+element checks, screenshot-on-fail)
- `memory/designer/breakpoint_gate_logic_test.py` — 5/5 acceptance expectations pass (sandbox-safe, no browser needed)
- Root `design_breakpoint_check.py` — playwright-based alternative with `--file` flag for offline fixtures

## Pre-deploy gate wiring (THIS PASS)
Add to the deploy checklist / runbook:
```
# Pre-deploy design gate (run before committing UI changes):
python memory/designer/breakpoint_gate.py --selftest   # 3 fixtures, ~10s, no portal needed
# or against live portal:
python memory/designer/breakpoint_gate.py              # :8099 at 375/768px
```
Exit code 0 = proceed; exit code 1 = layout break found (see screenshots in breakpoint-evidence/).

## Remaining for FULL closure
- [ ] Run `--selftest` on a seat with Edge/Chromium + loopback sockets (Studio sandbox blocks sockets errno 10013, no browser binary)
- [ ] 3 PNG screenshots land in `memory/designer/breakpoint-evidence/`
- [ ] Confirm exit code 1 on forced-overflow fixture (negative test with screenshot)

## Unblock command (one seat with browser):
```
python memory/designer/breakpoint_gate.py --selftest
```
Expected: `SELFTEST PASS: 3/3` + 3 PNG files.
