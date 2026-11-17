# Evidence: design_breakpoint_check.py enhancement (2026-11-17)

Goal #5 - Breakpoint regression automation.

## What was done this turn
- Added `--file` flag: script can load a local HTML file instead of :8099 (enables offline testing without the live portal).
- Added screenshot-on-fail: on any check failure, saves full-page PNG to `breakpoint_screenshots/fail_<width>px.png`.
- Created `breakpoint_overflow_fixture.html`: 1200px-wide div that forces horizontal overflow at all three breakpoints (375/768/1024).
- Script compiles clean (`python -m py_compile` OK).

## Remaining to close
- Run on Studio: `python design_breakpoint_check.py --file breakpoint_overflow_fixture.html` -> expect FAIL with screenshot evidence.
- Run against live portal: `python design_breakpoint_check.py` -> expect PASS.
- Wire as pre-deploy step in TODO.md runbook.

## Files
- design_breakpoint_check.py (enhanced, 4 edits)
- breakpoint_overflow_fixture.html (new test fixture)
