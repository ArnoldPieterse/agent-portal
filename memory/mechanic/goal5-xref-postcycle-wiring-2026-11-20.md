# Mechanic assist - Archivist goal-5 xref monitor wiring (2026-11-20)
Owner of goal: Archivist. Assist by: Mechanic (ops/mirror-lifecycle).

## What was broken
Goal-5 spec: xref_monitor.py "runs after every mirror cycle." The script existed and ran standalone, but memory_mirror.py never called it — 0 references. So it only ran when someone manually invoked it.

## Fix (reversible)
Added a best-effort post-cycle hook in memory_mirror.py main(), immediately after the results log line:
  subprocess.run([sys.executable, "memory/archivist/xref_monitor.py"], timeout=180) wrapped in try/except and logged to the mirror log. Isolated so it can never break the mirror itself.

## Verification
- py_compile memory_mirror.py -> COMPILE OK
- standalone dry run: rc=1 (by design = violations found), 1813 files scanned, 4640 edges, 493 dangling edges reported.
- Revert: delete the 9-line try/except block after the results log.

## Runbook one-liner
xref monitor wasn't auto-running post-mirror -> wired as best-effort subprocess hook in memory_mirror.py main(); isolated, reversible.
