# Provenance: created 2026-11-23 (assistant) for scheduler consolidation - one schedule
# slot per logical pipeline instead of one per script.
"""run_steps.py - run workspace scripts sequentially in one process chain.

Usage: python memory/ops/run_steps.py "script.py [args...]" ["script2.py ..." ...]
Each argument is a command line (script path relative to the workspace root + any args),
split on whitespace. Steps run sequentially; the chain continues after a failing step.
Per-step timeout: RUN_STEP_TIMEOUT env (default 900s); a hung step is killed (rc=124)
and the chain continues. Exits with the first non-zero rc, else 0. Progress and failure
tails go to stderr so the scheduler's last_err capture stays informative without
buffering each step's full output.
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))   # <ws>/memory/ops
WS   = os.path.dirname(os.path.dirname(HERE))       # workspace root
PY   = sys.executable

def main():
    rc = 0
    steps = [s for s in (x.split() for x in sys.argv[1:]) if s]
    timeout = float(os.environ.get("RUN_STEP_TIMEOUT", "900"))
    for i, parts in enumerate(steps, 1):
        script = parts[0]
        path = script if os.path.isabs(script) else os.path.join(WS, script)
        step = " ".join(parts)
        print("run_steps [%d/%d]: %s" % (i, len(steps), step), file=sys.stderr)
        try:
            r = subprocess.run([PY, path] + parts[1:], cwd=WS,
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                               timeout=timeout)
            code = r.returncode
            err = (r.stderr or b"")[-400:].decode("utf-8", "replace").strip()
        except subprocess.TimeoutExpired:
            code, err = 124, "TIMEOUT after %.0fs - killed" % timeout
        if code != 0:
            print("run_steps [%d/%d] FAIL rc=%d%s" % (i, len(steps), code,
                  (" | " + err) if err else ""), file=sys.stderr)
        if code != 0 and rc == 0:
            rc = code
    return rc

if __name__ == "__main__":
    sys.exit(main())
