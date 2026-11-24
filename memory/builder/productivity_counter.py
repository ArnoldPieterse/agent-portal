#!/usr/bin/env python3
"""productivity_counter.py - Per-agent pass-productivity over a rolling window.

Builds: builder goal 5 (Productivity Counter + /api/fleet/productivity).
Scans memory/ops/autoloop.jsonl for the last `window_h` hours (default 24),
counts total vs productive passes per agent, and writes the result to
memory/ops/productivity-baseline.json (the file /api/fleet/productivity serves).

Baseline schema:
  {"generated_at": ISO, "window_h": 24,
   "agents": {name: {"total_passes": n, "productive_passes": m, "rate": 0..1}},
   "fleet": {"total_passes": n, "productive_passes": m, "rate": 0..1}}

An entry counts when its timestamp parses and falls inside the window.
Entries with an unparseable timestamp are skipped (and counted in
"skipped_bad_ts") so a corrupt line never breaks the counter.

CLI:
  python productivity_counter.py [--window-h 24]   # recompute + write baseline
  python productivity_counter.py --print           # also print the result
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
OPS = HERE.parent / "ops"
AUTOLOOP = OPS / "autoloop.jsonl"
BASELINE = OPS / "productivity-baseline.json"


def scan(autoloop: Path | str = AUTOLOOP, window_h: float = 24.0,
         now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=window_h)
    per_agent: dict[str, dict] = {}
    fleet_t = fleet_p = skipped = 0
    if Path(autoloop).exists():
        for line in Path(autoloop).read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            ts_raw = e.get("timestamp")
            try:
                ts = datetime.fromisoformat(ts_raw)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            except (TypeError, ValueError):
                skipped += 1
                continue
            if ts < cutoff or ts > now + timedelta(minutes=5):  # small clock skew grace
                continue
            agent = str(e.get("agent") or "unknown")
            prod = bool(e.get("productive", False))
            a = per_agent.setdefault(agent, {"total_passes": 0, "productive_passes": 0})
            a["total_passes"] += 1
            if prod:
                a["productive_passes"] += 1
            fleet_t += 1
            fleet_p += 1
    for a in per_agent.values():
        a["rate"] = round(a["productive_passes"] / a["total_passes"], 4) if a["total_passes"] else 0.0
    return {
        "generated_at": now.isoformat(),
        "window_h": window_h,
        "agents": per_agent,
        "fleet": {
            "total_passes": fleet_t,
            "productive_passes": fleet_p,
            "rate": round(fleet_p / fleet_t, 4) if fleet_t else 0.0,
        },
        "skipped_bad_ts": skipped,
    }


def write_baseline(result: dict, path: Path | str = BASELINE) -> None:
    p = Path(path)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(result, indent=2), encoding="utf-8")
    tmp.replace(p)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--window-h", type=float, default=24.0)
    ap.add_argument("--print", action="store_true")
    args = ap.parse_args()
    res = scan(window_h=args.window_h)
    write_baseline(res)
    if args.print:
        print(json.dumps(res, indent=2))
    else:
        f = res["fleet"]
        print(f"baseline written: {len(res['agents'])} agents, "
              f"{f['productive_passes']}/{f['total_passes']} productive ({f['rate']:.1%})")
