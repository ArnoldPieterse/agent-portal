#!/usr/bin/env python3
"""archivist/freshness_heatmap.py - Per-directory freshness heatmap with trend.

Extends freshness_report.py: aggregates file ages by top-level memory/ subdir,
produces a JSON heatmap + appends to a 7-day rolling history for trend lines.

Usage:
  python memory/archivist/freshness_heatmap.py          # scan + write JSON
  python memory/archivist/freshness_heatmap.py --show   # also print table

Outputs:
  memory/archivist/freshness-heatmap.json       (current snapshot, render-ready)
  memory/archivist/freshness-heatmap-history.json (last 7 days of snapshots)
"""
import os, sys, json, argparse
from datetime import datetime, date, timedelta
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(ROOT, "memory")
HEATMAP_JSON = os.path.join(MEM, "archivist", "freshness-heatmap.json")
HISTORY_JSON = os.path.join(MEM, "archivist", "freshness-heatmap-history.json")
TODAY = date.today().isoformat()

EXEMPT_EXTS = {".pyc", ".lock", ".tmp", ".bak"}
EXEMPT_DIRS = {"__pycache__", ".git"}


def tier_for(age_days: int) -> str:
    if age_days < 7:
        return "HOT"
    elif age_days <= 30:
        return "WARM"
    elif age_days <= 90:
        return "COLD"
    return "STALE"


def scan_directories():
    """Aggregate file ages per top-level memory/ subdirectory."""
    dirs = defaultdict(lambda: {"files": 0, "age_sum": 0, "tiers": {"HOT": 0, "WARM": 0, "COLD": 0, "STALE": 0}, "newest_age": 9999, "oldest_age": 0})

    for dirpath, dirnames, filenames in os.walk(MEM):
        dirnames[:] = [d for d in dirnames if d not in EXEMPT_DIRS]
        rel_to_mem = os.path.relpath(dirpath, MEM).replace(os.sep, "/")
        # top-level subdir = first segment (or "_root" for files directly in memory/)
        parts = rel_to_mem.split("/")
        lane = parts[0] if len(parts) > 1 and parts[0] != "." else "_root"

        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext in EXEMPT_EXTS:
                continue
            full = os.path.join(dirpath, fn)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(full)).date()
                age_days = (TODAY and date.today() - mtime).days
            except OSError:
                continue
            d = dirs[lane]
            d["files"] += 1
            d["age_sum"] += age_days
            d["tiers"][tier_for(age_days)] += 1
            d["newest_age"] = min(d["newest_age"], age_days)
            d["oldest_age"] = max(d["oldest_age"], age_days)

    # Compute derived fields
    result = {}
    for lane, d in sorted(dirs.items()):
        n = d["files"] or 1
        avg_age = round(d["age_sum"] / n, 1)
        hot_pct = round(100.0 * d["tiers"]["HOT"] / n, 1)
        stale_pct = round(100.0 * d["tiers"]["STALE"] / n, 1)
        # freshness score: 0-100, higher = fresher
        score = max(0, min(100, round(100 - (avg_age / 90) * 100)))
        result[lane] = {
            "files": d["files"],
            "avg_age_days": avg_age,
            "freshness_score": score,
            "tiers": d["tiers"],
            "hot_pct": hot_pct,
            "stale_pct": stale_pct,
            "newest_file_age": d["newest_age"] if d["files"] else None,
            "oldest_file_age": d["oldest_age"] if d["files"] else None,
        }
    return result


def load_history():
    if os.path.exists(HISTORY_JSON):
        with open(HISTORY_JSON, encoding="utf-8") as f:
            return json.load(f)
    return []


def append_history(history, snapshot):
    history.append({"date": TODAY, "dirs": snapshot})
    # Keep last 7 days (or 7 entries if multiple per day)
    cutoff = (date.today() - timedelta(days=7)).isoformat()
    history = [h for h in history if h["date"] >= cutoff]
    return history


def build_trends(history):
    """For each lane, produce last-N freshness scores as a trend list."""
    lanes = set()
    for h in history:
        lanes.update(h.get("dirs", {}).keys())
    trends = {}
    for lane in sorted(lanes):
        points = []
        for h in history:
            d = h.get("dirs", {}).get(lane)
            if d:
                points.append({"date": h["date"], "score": d["freshness_score"], "avg_age": d["avg_age_days"]})
        trends[lane] = points
    return trends


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true", help="print table to stdout")
    args = ap.parse_args()

    snapshot = scan_directories()
    history = load_history()
    history = append_history(history, snapshot)
    trends = build_trends(history)

    output = {
        "generated": TODAY,
        "total_dirs": len(snapshot),
        "dirs": snapshot,
        "trends": trends,
        "history_days": len(history),
    }

    with open(HEATMAP_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    with open(HISTORY_JSON, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    if args.show:
        print(f"{'Lane':<15} {'Files':>6} {'AvgAge':>8} {'Score':>6} {'HOT%':>6} {'STALE%':>7}")
        print("-" * 55)
        for lane, d in sorted(snapshot.items(), key=lambda x: -x[1]["freshness_score"]):
            print(f"{lane:<15} {d['files']:>6} {d['avg_age_days']:>8} {d['freshness_score']:>6} {d['hot_pct']:>6} {d['stale_pct']:>7}")
        print(f"\nWrote: memory/archivist/freshness-heatmap.json ({os.path.getsize(HEATMAP_JSON)} B)")
        print(f"History: {len(history)} snapshots")
    else:
        print(f"OK: freshness-heatmap.json written ({len(snapshot)} dirs, {len(history)} history points)")


if __name__ == "__main__":
    main()
