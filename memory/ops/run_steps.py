# Provenance: created 2026-11-23 (assistant) for scheduler consolidation - one schedule
# slot per logical pipeline instead of one per script.
"""run_steps.py - run workspace scripts sequentially in one process chain.

Usage: python memory/ops/run_steps.py "script.py [args...]" ["script2.py ..." ...]
Each argument is a command line (script path relative to the workspace root + any args),
split on whitespace. Exits with the first non-zero rc, else 0.
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))   # <ws>/memory/ops
WS   = os.path.dirname(os.path.dirname(HERE))       # workspace root
PY   = sys.executable

def main():
    rc = 0
    for step in sys.argv[1:]:
        parts = step.split()
        if not parts:
            continue
        script = parts[0]
        path = script if os.path.isabs(script) else os.path.join(WS, script)
        r = subprocess.run([PY, path] + parts[1:], cwd=WS,
                           stdout=subprocess.DEVNULL, stderr=sys.stderr)
        print("run_steps: rc=%d %s" % (r.returncode, step))
        if r.returncode != 0 and rc == 0:
            rc = r.returncode
    return rc

if __name__ == "__main__":
    sys.exit(main())
