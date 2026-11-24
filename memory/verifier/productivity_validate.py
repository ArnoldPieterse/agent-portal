#!/usr/bin/env python3
"""productivity_validate.py - Verifier G7 (cycle-15): validate the productivity counter.

Runs memory/builder/productivity_counter.scan() over three synthetic workloads with
known ground truth and asserts the reported rate matches within 1%:
  A) all-productive: every pass productive -> rate 1.0
  B) all-wasted:     no pass productive    -> rate 0.0
  C) mixed:          3 of 10 productive    -> rate 0.3 (per agent + fleet)

Usage:
  python productivity_validate.py
"""
import importlib.util, json, sys, tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent.parent
cp = HERE / "memory" / "builder" / "productivity_counter.py"
spec = importlib.util.spec_from_file_location("productivity_counter", str(cp))
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)


def workload(path: Path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def main():
    now = datetime.now(timezone.utc)
    def ts(min_ago): return (now - timedelta(minutes=min_ago)).isoformat()
    tmp = Path(tempfile.mkdtemp(prefix="prodval_"))
    try:
        # A) all-productive: 8 passes, all productive
        pa = tmp / "a.jsonl"
        workload(pa, [{"timestamp": ts(10 * i), "agent": "test_agent", "productive": True} for i in range(8)])
        ra = pc.scan(autoloop=pa, window_h=24)
        a = ra["agents"]["test_agent"]
        assert abs(a["rate"] - 1.0) <= 0.01 and a["total_passes"] == 8 and a["productive_passes"] == 8, a

        # B) all-wasted: 8 passes, none productive
        pb = tmp / "b.jsonl"
        workload(pb, [{"timestamp": ts(10 * i), "agent": "test_agent", "productive": False} for i in range(8)])
        rb = pc.scan(autoloop=pb, window_h=24)
        b = rb["agents"]["test_agent"]
        assert abs(b["rate"] - 0.0) <= 0.01 and b["total_passes"] == 8 and b["productive_passes"] == 0, b

        # C) mixed: agent x -> 3/10 productive (0.3), agent y -> 5/6 productive (~0.8333)
        pc_ = tmp / "c.jsonl"
        rows = []
        for i in range(10):
            rows.append({"timestamp": ts(i + 1), "agent": "x", "productive": i < 3})
        for i in range(6):
            rows.append({"timestamp": ts(i + 1), "agent": "y", "productive": i < 5})
        workload(pc_, rows)
        rc = pc.scan(autoloop=pc_, window_h=24)
        x, y = rc["agents"]["x"], rc["agents"]["y"]
        assert abs(x["rate"] - 0.3) <= 0.01 and x["total_passes"] == 10 and x["productive_passes"] == 3, x
        assert abs(y["rate"] - (5 / 6)) <= 0.01 and y["total_passes"] == 6 and y["productive_passes"] == 5, y
        f = rc["fleet"]
        exp_rate = (3 + 5) / (10 + 6)
        assert abs(f["rate"] - exp_rate) <= 0.01 and f["total_passes"] == 16 and f["productive_passes"] == 8, f

        # D) windowing: passes outside the 24h window are excluded (ground truth unchanged)
        pd = tmp / "d.jsonl"
        rows = [{"timestamp": ts(60 * i), "agent": "w", "productive": True} for i in range(4)]
        rows.append({"timestamp": (now - timedelta(hours=48)).isoformat(), "agent": "w", "productive": False})
        workload(pd, rows)
        rd = pc.scan(autoloop=pd, window_h=24)
        w = rd["agents"]["w"]
        assert w["total_passes"] == 4 and abs(w["rate"] - 1.0) <= 0.01, w

        print("SELFTEST OK (all-productive=1.0, all-wasted=0.0, mixed x=0.3 y=5/6 fleet=8/16 within 1%; windowing excludes stale passes)")
        return 0
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())