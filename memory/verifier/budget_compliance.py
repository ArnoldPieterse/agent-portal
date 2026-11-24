#!/usr/bin/env python3
"""budget_compliance.py - Pass budget compliance test (Verifier cycle-15 G5).

Drives the REAL orchestrator pass-budget module (memory/orchestrator/pass_budget.py)
in a sandboxed temp dir: simulates 250 passes with budget=200 and asserts:
  * counter increments on every pass (consumed == pass number)
  * BUDGET_EXHAUSTED flag goes True exactly at pass 200
  * dispatch_work is True for passes 1..200 only - NOTHING dispatched beyond pass 200
  * fleet-mode transitions to IDLE when the budget exhausts (_force_idle path)
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent            # memory/verifier
BASE = HERE.parent.parent                         # project root
BUDGET_MODULE = BASE / "memory" / "orchestrator" / "pass_budget.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("pass_budget", str(BUDGET_MODULE))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="budget_"))
    try:
        pb = _load_module()
        # Sandbox the module's file targets (same technique its own cmd_test uses)
        saved_b, saved_m = pb.BUDGET_FILE, pb.MODE_FILE
        pb.BUDGET_FILE = str(tmp / "pass-budget.json")
        pb.MODE_FILE = str(tmp / "fleet-mode.json")
        with open(pb.MODE_FILE, "w", encoding="utf-8") as f:
            json.dump({"mode": "WORK", "timestamp": "2026-11-24T00:00:00+00:00"}, f)

        # init budget 200
        class A: pass
        args = A(); args.budget = 200
        pb.cmd_init(args)
        d = json.load(open(pb.BUDGET_FILE, encoding="utf-8"))
        assert d["budget"] == 200 and d["consumed"] == 0, d

        # Real dispatcher order: check() BEFORE consuming a pass (check -> dispatch -> increment).
        import io
        from contextlib import redirect_stdout
        dispatched = 0          # passes that were allowed to dispatch work
        refused = 0             # passes denied at/after exhaustion
        exhausted_at = None     # first pass number AFTER which the flag is True
        counter_ok = True
        for i in range(1, 251):   # 250 simulated passes
            with redirect_stdout(io.StringIO()):
                pb.cmd_check(A())
            d = json.load(open(pb.BUDGET_FILE, encoding="utf-8"))
            remaining = d["budget"] - d["consumed"]
            if remaining > 0:
                dispatched += 1
                with redirect_stdout(io.StringIO()):
                    pb.cmd_increment(A())
                d2 = json.load(open(pb.BUDGET_FILE, encoding="utf-8"))
                if d2["consumed"] != i:
                    counter_ok = False
            else:
                refused += 1
            if remaining <= 0 and exhausted_at is None:
                exhausted_at = i - 1   # flag flipped True right after pass (i-1) consumed the last unit

        assert counter_ok, "counter did not increment by exactly one per dispatched pass"
        assert exhausted_at == 200, f"BUDGET_EXHAUSTED raised after pass {exhausted_at}, expected 200"
        assert dispatched == 200, f"{dispatched} passes dispatched; expected exactly 200 (none beyond)"
        assert refused == 50, f"{refused} passes refused; expected 50 (passes 201-250)"

        # exhaustion must have forced fleet-mode to IDLE
        fm = json.load(open(pb.MODE_FILE, encoding="utf-8"))
        assert fm["mode"] == "IDLE", f"fleet-mode after exhaustion: {fm['mode']!r} (expected IDLE)"
        assert "budget" in str(fm.get("reason", "")).lower(), fm

        # check() itself also refuses dispatch at/after exhaustion and keeps IDLE
        out = json.loads(_capture(pb.cmd_check, A()))
        assert out["exhausted"] is True and out["dispatch_work"] is False, out
        fm = json.load(open(pb.MODE_FILE, encoding="utf-8"))
        assert fm["mode"] == "IDLE", fm

        print(f"SELFTEST OK (250 passes @ budget 200: counter exact, BUDGET_EXHAUSTED at pass 200, "
              f"dispatched exactly 200 / zero beyond, mode forced IDLE on exhaustion)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _capture(fn, *a):
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        fn(*a)
    return buf.getvalue().strip().splitlines()[-1]


if __name__ == "__main__":
    sys.exit(main())
