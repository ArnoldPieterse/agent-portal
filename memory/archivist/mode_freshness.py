#!/usr/bin/env python3
"""mode_freshness.py - Knowledge freshness (TTL) for fleet-mode data (Archivist cycle-15 G10).

Watches the two live mode-data sources and flags staleness:
  * memory/ops/fleet-mode.json          (fleet mode controller output)
  * memory/ops/productivity-baseline.json  (productivity baseline snapshot)

A file is STALE when its mtime is older than TTL_HOURS (default 2h). Stale files are
marked in the KB index (memory/archivist/knowledge-index.json, key "mode_freshness")
and the flag propagates to /api/fleet/cockpit via check() -> memory/ops/mode-freshness.json.

CLI:
  python mode_freshness.py            # check + write flags, print JSON
  python mode_freshness.py selftest   # fresh vs stale scenarios in a sandbox dir
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent            # memory/archivist
BASE = HERE.parent.parent                         # project root
OPS = HERE.parent / "ops"
KB_INDEX = HERE / "knowledge-index.json"
OUT = OPS / "mode-freshness.json"
TTL_HOURS = 2.0
WATCHED = {
    "fleet-mode": OPS / "fleet-mode.json",
    "productivity-baseline": OPS / "productivity-baseline.json",
}


def _age_hours(p: Path, now=None) -> float | None:
    if not p.exists():
        return None
    now = now or time.time()
    return round((now - p.stat().st_mtime) / 3600.0, 2)


def check(now=None, watched: dict | None = None, out_path: Path | str = OUT,
          kb_index: Path | str = KB_INDEX, ttl_hours: float = TTL_HOURS) -> dict:
    """Compute freshness for each watched file; write mode-freshness.json and mark
    stale entries in the KB index. Returns the report dict."""
    now = now or time.time()
    watched = watched or WATCHED
    files = []
    n_stale = 0
    for name, p in watched.items():
        age = _age_hours(p, now)
        if age is None:
            status, age_out = "missing", None
        else:
            stale = age > ttl_hours
            status = "stale" if stale else "current"
            if stale:
                n_stale += 1
            age_out = age
        files.append({"file": name, "path": str(p.relative_to(BASE)) if p.is_relative_to(BASE) else str(p),
                      "status": status, "age_h": age_out,
                      "mtime": datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat() if p.exists() else None})
    report = {"ts": datetime.now(tz=timezone.utc).isoformat(), "ttl_h": ttl_hours,
              "files": files, "stale_count": n_stale,
              "any_stale": n_stale > 0}
    # 1) machine-readable flag file (read by /api/fleet/cockpit)
    try:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = str(out_path) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        os.replace(tmp, str(out_path))
    except OSError:
        pass
    # 2) mark stale in the KB index (create a minimal index if none exists yet)
    try:
        kb_index = Path(kb_index)
        idx = {}
        if kb_index.exists():
            try:
                idx = json.loads(kb_index.read_text(encoding="utf-8"))
            except Exception:
                idx = {}
        idx["mode_freshness"] = {f["file"]: f for f in files}
        tmp = str(kb_index) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(idx, f, indent=2)
        os.replace(tmp, str(kb_index))
    except OSError:
        pass
    return report


def selftest() -> int:
    import shutil
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="fresh_"))
    try:
        ops = tmp / "ops"
        ops.mkdir(parents=True)
        fm = ops / "fleet-mode.json"
        pb = ops / "productivity-baseline.json"
        fm.write_text(json.dumps({"mode": "WORK"}), encoding="utf-8")
        pb.write_text(json.dumps({"baseline": 0.5}), encoding="utf-8")
        out = tmp / "ops" / "mode-freshness.json"
        kb = tmp / "kb-index.json"

        # Scenario 1: fresh files (<2h) -> current
        r = check(watched={"fleet-mode": fm, "productivity-baseline": pb},
                  out_path=out, kb_index=kb)
        assert all(f["status"] == "current" for f in r["files"]), r
        assert r["any_stale"] is False and r["stale_count"] == 0, r
        assert out.exists() and json.loads(out.read_text(encoding="utf-8"))["any_stale"] is False
        kbdata = json.loads(kb.read_text(encoding="utf-8"))
        assert kbdata["mode_freshness"]["fleet-mode"]["status"] == "current", kbdata

        # Scenario 2: make one file stale (>2h) -> marked stale with age, KB index updated
        old = time.time() - 3 * 3600
        os.utime(pb, (old, old))
        r = check(watched={"fleet-mode": fm, "productivity-baseline": pb},
                  out_path=out, kb_index=kb)
        st = {f["file"]: f for f in r["files"]}
        assert st["fleet-mode"]["status"] == "current", st
        assert st["productivity-baseline"]["status"] == "stale", st
        assert st["productivity-baseline"]["age_h"] > 2.0, st
        assert r["any_stale"] is True and r["stale_count"] == 1, r
        kbdata = json.loads(kb.read_text(encoding="utf-8"))
        assert kbdata["mode_freshness"]["productivity-baseline"]["status"] == "stale", kbdata

        # Scenario 3: missing file -> status missing (not a crash)
        pb.unlink()
        r = check(watched={"fleet-mode": fm, "productivity-baseline": pb},
                  out_path=out, kb_index=kb)
        st = {f["file"]: f for f in r["files"]}
        assert st["productivity-baseline"]["status"] == "missing", st

        print("SELFTEST OK (fresh->current, stale>2h->stale w/ age, missing handled; KB index marked)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        sys.exit(selftest())
    print(json.dumps(check(), indent=2))
