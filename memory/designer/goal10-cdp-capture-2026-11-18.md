# Goal 10 Progress: CDP-based capture (no Playwright) - 2026-11-18

## What changed
Rewrote `capture_baseline.py` to use Edge headless + Chrome DevTools Protocol (CDP)
via the `websockets` package (already installed) instead of Playwright.

## Before
- Required: `pip install playwright && python -m playwright install chromium` (~500 MB)
- Status: blocked on dependency install (permission denied in sandbox)

## After
- Requires: msedge (present) + `websockets` (already installed, verified import OK)
- Command: `python memory/designer/baseline/run_all.py --url http://127.0.0.1:8099`
- Status: ready to run from any non-sandboxed terminal on the host

## Verification performed
- [x] Edge browser found at C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe
- [x] `import websockets` succeeds in current Python environment
- [x] Script syntax verified (compiles clean)
- [ ] Actual capture: requires network access to :8099 (sandbox blocks outbound sockets)

## Remaining step
Run from a non-sandboxed shell: `python memory/designer/baseline/run_all.py`
This is the same one-command unblock noted in HOT NOTES, now with the dependency removed.

## File changed
- memory/designer/baseline/capture_baseline.py (rewritten, 7719 bytes)
