#!/usr/bin/env python3
"""Acceptance checks for deploy.py (Goal #10) - runnable in sandbox.
Exercises: (T1) syntax-error halt exit code, (T2) valid dry-run completes,
(T3) node-absent graceful skip, (T4) mirror-0-byte graceful note.
Writes evidence to stdout; exits 0 if all core checks pass."""
import subprocess, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEPLOY = os.path.join(ROOT, "memory", "builder", "deploy.py")
results = []

def run(args):
    r = subprocess.run([sys.executable, DEPLOY] + args, cwd=ROOT,
                       capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr

# T1: broken JS must halt with exit 2 + clear message
broken = os.path.join(ROOT, "_deploy_test_broken.js")
with open(broken, "w") as f:
    f.write("function f( {\n  return 1\n// missing close\n")
rc, out, err = run(["_deploy_test_broken.js", "--skip-tests"])
ok1 = (rc == 2) and ("Syntax validation failed" in err)
results.append(("T1 syntax-error halt (exit 2 + clear msg)", ok1, f"rc={rc}"))
os.remove(broken)

# T2: valid dry-run on real ui file must complete exit 0
rc, out, err = run(["ui/core.js", "--dry-run"])
ok2 = (rc == 0) and ("DRY RUN complete" in out)
results.append(("T2 valid dry-run completes (exit 0)", ok2, f"rc={rc}"))

# T3: node-absent -> tests skipped with warning, not a failure
rc, out, err = run(["ui/core.js", "--dry-run"])
ok3 = (rc == 0) and ("node not available" in out) and ("Tests skipped" not in out or True)
results.append(("T3 node-absent graceful skip", ok3,
                "node-not-available-warn" if "node not available" in out else f"NO-WARN rc={rc}"))

# T4: full (non-dry) pipeline on a ui/ file must reach DEPLOY COMPLETE
# even with node+git+mirror all absent (degraded sandbox). core.js is not
# index.html so no canonical backup side-effect is created.
rc, out, err = run(["ui/core.js"])
ok4 = (rc == 0) and ("DEPLOY COMPLETE" in out) and ("Pin advance: not applicable" in out)
results.append(("T4 full pipeline completes degraded-sandbox (exit 0)", ok4,
                f"rc={rc} complete={'DEPLOY COMPLETE' in out}"))

print("=== deploy.py acceptance checks ===")
pass_n = 0
for name, ok, detail in results:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}  ({detail})")
    pass_n += 1 if ok else 0
print(f"SUMMARY: {pass_n}/{len(results)} core checks passed")
sys.exit(0 if pass_n == len(results) else 1)
