"""Goal 9 verification: Steady-State Calm Mode (static analysis)"""
import re, pathlib, sys
src = pathlib.Path("ui/cockpit-calm-mode.js").read_text(encoding="utf-8")
checks = []
m = re.search(r"classList\.(add|remove)\(CALM_CLASS\)", src)
checks.append(("mode toggle changes CSS class", bool(m)))
has_catch = "catch" in src
checks.append(("error handling present (try/catch)", has_catch))
m = re.search(r"TRANSITION_MS\s*=\s*(\d+)", src)
dur = int(m.group(1)) if m else 9999
checks.append((f"transition {dur}ms (< 1000ms)", dur < 1000))
m = re.search(r"--acc:#6b9e8a|--ok:#5a8a72", src)
checks.append(("muted color palette override", bool(m)))
m = re.search(r"animation-duration:.*!important|animation:none!important", src)
checks.append(("reduced/disabled animations", bool(m)))
m = re.search(r"classList\.remove\(CALM_CLASS\)", src)
checks.append(("restore full UI on exit (class removed)", bool(m)))
all_pass = all(ok for _, ok in checks)
for name, ok in checks:
    print(f"  {'PASS' if ok else 'FAIL'}: {name}")
print(f"ALL {len(checks)} CHECKS PASSED" if all_pass else "FAILED")
sys.exit(0 if all_pass else 1)
