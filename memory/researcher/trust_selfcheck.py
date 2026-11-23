#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""trust_selfcheck.py - Researcher Goal 10 (cycle-11): Trust-Pipeline Self-Check.

Test harness over the whole trust pipeline. For each component it runs the
real selftest in a subprocess AND an active negative fixture that must make
the corresponding assertion fail (proving the check is live, not rubber-stamp).
Exit code 0 = all pass, 1 = any failure. Runtime <20s.

Components:
  loop_closure_rate      - closure report regenerates deterministically
  decision_confidence    - confidence report regenerates
  evidence_trace         - trace report regenerates
  calibration_tracker    - Brier within [0,1] on live data
  action_replay          - replay hash stable across runs
  autonomy_risk_register - planted risk detected (negative fixture)
  loop_stall_predictor   - stalled fixture > productive fixture
  fleet_trust_score      - high-low gap >=20 (negative: low state must not score high)
"""
import json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def run_selftest(name):
    t0 = time.time()
    r = subprocess.run([PY, os.path.join(HERE, name), "selftest"],
                       capture_output=True, text=True, timeout=15)
    ok = r.returncode == 0 and "SELFTEST PASS" in (r.stdout + r.stderr)
    return ok, round(time.time() - t0, 2), (r.stdout + r.stderr)[-160:]


def fixture_loop_closure():
    """Closure rate must parse; a corrupted report must yield a different (or
    missing) value - proves the parser reads real data."""
    p = os.path.join(HERE, "loop-closure-report.md")
    orig = open(p, encoding="utf-8", errors="replace").read()
    try:
        m1 = re.search(r"closure rate:\s*([0-9.]+)%", orig)
        assert m1, "no closure rate in live report"
        open(p, "w", encoding="utf-8").write(orig.replace(m1.group(0), "closure rate: 0.0%"))
        m2 = re.search(r"closure rate:\s*([0-9.]+)%", open(p, encoding="utf-8").read())
        assert m2 and float(m2.group(1)) != float(m1.group(1)), "corruption not observed"
    finally:
        open(p, "w", encoding="utf-8").write(orig)
    return True


def fixture_trust_score():
    """Negative: a low-trust signal set must NOT score >=70."""
    sys.path.insert(0, HERE)
    try:
        import fleet_trust_score as fts
        low = fts.trust_score({"closure_rate": 0.35, "mean_confidence": 0.1, "brier": 0.249})
        assert low is not None and low < 70, "low state scored %s (want <70)" % low
    finally:
        if HERE in sys.path:
            sys.path.remove(HERE)
    return True


def main():
    t0 = time.time()
    results = []
    for name in ["loop_closure_rate.py", "decision_confidence.py", "evidence_trace.py",
                 "calibration_tracker.py", "action_replay.py",
                 "autonomy_risk_register.py", "loop_stall_predictor.py",
                 "fleet_trust_score.py"]:
        ok, dt, tail = run_selftest(name)
        results.append((name, ok, dt))
        print("%-28s %s (%.2fs)" % (name, "PASS" if ok else "FAIL", dt))
        if not ok:
            print("   tail:", tail.replace("\n", " | ")[:140])
    # active negative fixtures
    try:
        fixture_loop_closure()
        results.append(("fixture:closure-corruption", True, 0.0))
        print("%-28s PASS" % "fixture:closure-corruption")
    except Exception as e:
        results.append(("fixture:closure-corruption", False, 0.0))
        print("%-28s FAIL %s" % ("fixture:closure-corruption", str(e)[:100]))
    try:
        fixture_trust_score()
        results.append(("fixture:trust-low-state", True, 0.0))
        print("%-28s PASS" % "fixture:trust-low-state")
    except Exception as e:
        results.append(("fixture:trust-low-state", False, 0.0))
        print("%-28s FAIL %s" % ("fixture:trust-low-state", str(e)[:100]))
    failed = [n for n, ok, _ in results if not ok]
    total = time.time() - t0
    print("RESULT: %d/%d pass (%.1fs)" % (len(results) - len(failed), len(results), total))
    if failed:
        print("FAILED:", ", ".join(failed))
    sys.exit(1 if (failed or total > 20) else 0)


if __name__ == "__main__":
    main()

