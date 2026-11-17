#!/usr/bin/env python3
"""Unit tests for slo_enforce.py logic (mocked network). Validates output format
and breach detection before first production run. Run: python memory/verifier/test_slo_enforce.py"""
import json, io, sys, os, datetime
from unittest.mock import patch, MagicMock

# We test the core logic by importing and monkeypatching urllib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS_COUNT = 0
FAIL_COUNT = 0

def check(name, cond, detail=""):
    global PASS_COUNT, FAIL_COUNT
    if cond:
        PASS_COUNT += 1
        print(f"  PASS: {name}")
    else:
        FAIL_COUNT += 1
        print(f"  FAIL: {name} {detail}")

def make_perf(endpoints):
    return {"endpoints": endpoints}

def run_slo_logic(perf_data, tmp_dir):
    """Run slo_enforce.main() with mocked urlopen + file paths redirected to tmp_dir."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(perf_data).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    
    # Redirect output files
    orig_open = open
    def fake_open(path, mode='r', **kw):
        if path.startswith('memory/verifier/slo-'):
            path = os.path.join(tmp_dir, os.path.basename(path))
        return orig_open(path, mode, **kw)
    
    with patch('urllib.request.urlopen', return_value=mock_resp), \
         patch('builtins.open', side_effect=fake_open):
        import slo_enforce
        import importlib
        importlib.reload(slo_enforce)
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            slo_enforce.main()
        finally:
            sys.stdout = old_stdout
    return buf.getvalue().strip()

def test_all_ok():
    """All endpoints within SLO -> PASS."""
    perf = make_perf([
        {"path": "/api/health", "n": 100, "p95_ms": 45, "p99_ms": 120},
        {"path": "/api/goals", "n": 50, "p95_ms": 80, "p99_ms": 300},
    ])
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        out = run_slo_logic(perf, td)
    check("all-ok: output says PASS", "PASS" in out, f"got: {out}")
    check("all-ok: no BREACH", "BREACH" not in out, f"got: {out}")
    # stdout one-line format (what gets posted to group chat)
    check("all-ok: one-line format 'slo_enforce: PASS'", out == "slo_enforce: PASS", f"got: {repr(out)}")

def test_breach():
    """One endpoint breaches p95 -> BREACH."""
    perf = make_perf([
        {"path": "/api/health", "n": 100, "p95_ms": 45, "p99_ms": 120},
        {"path": "/api/slow-endpoint", "n": 10, "p95_ms": 3500, "p99_ms": 7000},
    ])
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        out = run_slo_logic(perf, td)
    check("breach: output says BREACH", "BREACH" in out, f"got: {out}")
    check("breach: names offending endpoint", "/api/slow-endpoint" in out, f"got: {out}")
    check("breach: one-line format starts 'slo_enforce:'", out.startswith("slo_enforce:"), f"got: {repr(out)}")

def test_empty():
    """No endpoints -> PASS (vacuously true)."""
    perf = make_perf([])
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        out = run_slo_logic(perf, td)
    check("empty: output says PASS", "PASS" in out, f"got: {out}")

def test_none_percentiles():
    """p95/p99 are None (insufficient data) -> treated as OK."""
    perf = make_perf([
        {"path": "/api/new", "n": 1, "p95_ms": None, "p99_ms": None},
    ])
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        out = run_slo_logic(perf, td)
    check("none-pct: output says PASS", "PASS" in out, f"got: {out}")

if __name__ == "__main__":
    print("slo_enforce.py unit tests (mocked network):")
    test_all_ok()
    test_breach()
    test_empty()
    test_none_percentiles()
    print(f"\nResult: {PASS_COUNT} PASS, {FAIL_COUNT} FAIL")
    sys.exit(0 if FAIL_COUNT == 0 else 1)
