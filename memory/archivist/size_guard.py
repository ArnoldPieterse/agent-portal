#!/usr/bin/env python3
"""Memory tree size guard (archivist goal #10, 2026-11-18; thresholds recalibrated 2026-11-23).

Walks the memory/ tree and enforces the hard limit: warn above 200 MB,
fail above 300 MB. Run standalone or from the portal startup check:
    python memory/archivist/size_guard.py
Exit codes: 0 OK, 1 WARN (>200 MB), 2 FAIL (>300 MB).

2026-11-23 note: the original 4/5 MB limits predate the fleet backup tarballs,
merge-queue snapshots and agent work artifacts that legitimately live in memory/.
The tree had grown to ~513 MB, so the guard was permanently red (always exit 2)
and carried no signal. After the 2026-11-23 bloat cleanup (browser profile dirs,
stale backup tarballs) the tree sits at ~270 MB; 200/300 MB keeps the alarm
meaningful: WARN = bloat returning, FAIL = a runaway writer needs a human.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
WARN_BYTES = 200 * 1024 * 1024
HARD_BYTES = 300 * 1024 * 1024

total = 0
for _r, _d, files in os.walk(ROOT):
    for f in files:
        try:
            total += os.path.getsize(os.path.join(_r, f))
        except OSError:
            pass

mb = total / 1048576.0
if total > HARD_BYTES:
    print("memory tree: %.2f MB - FAIL (over 300 MB hard limit)" % mb)
    sys.exit(2)
if total > WARN_BYTES:
    print("memory tree: %.2f MB - WARN (over 200 MB warning line)" % mb)
    sys.exit(1)
print("memory tree: %.2f MB - OK (warn>200MB hard>300MB)" % mb)
sys.exit(0)
