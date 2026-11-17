#!/usr/bin/env python3
"""Memory tree size guard (archivist goal #10, 2026-11-18).

Walks the memory/ tree and enforces the hard limit: warn above 4 MB,
fail above 5 MB. Run standalone or from the portal startup check:
    python memory/archivist/size_guard.py
Exit codes: 0 OK, 1 WARN (>4 MB), 2 FAIL (>5 MB).
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
WARN_BYTES = 4 * 1024 * 1024
HARD_BYTES = 5 * 1024 * 1024

total = 0
for _r, _d, files in os.walk(ROOT):
    for f in files:
        try:
            total += os.path.getsize(os.path.join(_r, f))
        except OSError:
            pass

mb = total / 1048576.0
if total > HARD_BYTES:
    print("memory tree: %.2f MB - FAIL (over 5 MB hard limit)" % mb)
    sys.exit(2)
if total > WARN_BYTES:
    print("memory tree: %.2f MB - WARN (over 4 MB warning line)" % mb)
    sys.exit(1)
print("memory tree: %.2f MB - OK (warn>4MB hard>5MB)" % mb)
sys.exit(0)
