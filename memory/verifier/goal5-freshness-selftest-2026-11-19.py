#!/usr/bin/env python3
"""Self-test for freshness_audit.py (goal 5). Proves both detection branches:
(stale) an old-dated marker whose evidence file exists but is >7 days old,
and (missing) a marker pointing at a nonexistent file. Runs against an isolated
fixture tree by temporarily repointing the module's GOALS_DIR, then cleans up.
"""
import os, sys, tempfile, shutil, importlib.util
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("freshness_audit", os.path.join(HERE, "freshness_audit.py"))
fa = importlib.util.module_from_spec(spec); spec.loader.exec_module(fa)

tmp = os.path.join(HERE, "_fx_fresh")  # same drive as cwd so relpath works
if os.path.isdir(tmp): shutil.rmtree(tmp)
gdir = os.path.join(tmp, "goals"); edir = os.path.join(tmp, "evidence")
os.makedirs(gdir); os.makedirs(edir)

# 1) STALE: evidence exists but mtime is 30 days old + marker dated 2026-10-01
ef = os.path.join(edir, "stale_ev.md"); open(ef, "w").write("old evidence\n")
old = datetime.now() - timedelta(days=30); os.utime(ef, (old.timestamp(), old.timestamp()))
open(os.path.join(gdir, "fxgoal.md"), "w").write(
    "1. Test goal (verified: 2026-10-01 - ran thing; evidence at %s)\n" % ef.replace("\\", "/"))

# 2) MISSING: marker points at a nonexistent file
open(os.path.join(gdir, "fxgoal2.md"), "w").write(
    "2. Missing ev (verified: 2026-11-01 - did x; evidence at %s)\n"
    % os.path.join("memory", "verifier", "_does_not_exist_xyz.md").replace("\\", "/"))

fa.GOALS_DIR = gdir
rc = fa.audit(stale_days=7, verbose=True)
os._exit(shutil.rmtree(tmp, ignore_errors=True) or rc if rc in (0,1) else 3)
