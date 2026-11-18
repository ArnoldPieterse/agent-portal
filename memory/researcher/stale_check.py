"""STALE-KNOWLEDGE DETECTOR (Goal #4).

Scans dictionary_*.json for entries with last_verified > N days old.
Writes a re-verification queue file for flagged terms.

Usage: python memory/researcher/stale_check.py [--days 90] [--queue-file PATH]
"""
import json, os, sys, argparse
from datetime import date, timedelta

_HERE = os.path.dirname(os.path.abspath(__file__))
DICT_FILES = [os.path.join(_HERE, "dictionary_core.json"),
              os.path.join(_HERE, "dictionary_project.json")]
DEFAULT_QUEUE = os.path.join(_HERE, "stale_queue.json")

def parse_date(s):
    try:
        return date.fromisoformat(s.strip())
    except Exception:
        return None

def scan(days=90):
    cutoff = date.today() - timedelta(days=days)
    stale = []
    total = 0
    for f in DICT_FILES:
        if not os.path.exists(f):
            continue
        raw = json.load(open(f, encoding="utf-8"))
        fname = os.path.basename(f)
        for k, v in raw.items():
            if k.startswith("_"):
                continue
            total += 1
            lv = None
            if isinstance(v, dict):
                lv = v.get("last_verified")
            # new format only has last_verified; old list format doesn't -> treat as unknown
            if lv is None:
                stale.append({"term": k, "file": fname, "reason": "no last_verified field (pre-migration)", "last_verified": None})
                continue
            d = parse_date(lv)
            if d is None:
                stale.append({"term": k, "file": fname, "reason": f"unparseable date: {lv!r}", "last_verified": lv})
            elif d < cutoff:
                age = (date.today() - d).days
                stale.append({"term": k, "file": fname, "reason": f"{age} days old (>{days})", "last_verified": lv})
    return total, stale

def main():
    ap = argparse.ArgumentParser(description="Flag stale dictionary entries")
    ap.add_argument("--days", type=int, default=90, help="stale threshold in days (default 90)")
    ap.add_argument("--queue-file", default=DEFAULT_QUEUE, help="output queue file path")
    args = ap.parse_args()

    total, stale = scan(args.days)
    print(f"Scanned {total} entries across {len(DICT_FILES)} files.")
    print(f"Stale (>{args.days} days or missing last_verified): {len(stale)}")

    if stale:
        for s in sorted(stale, key=lambda x: x["term"]):
            print(f"  - {s['term']} ({s['file']}): {s['reason']}")
        queue = {"generated": str(date.today()), "threshold_days": args.days,
                 "count": len(stale), "entries": stale}
        json.dump(queue, open(args.queue_file, "w", encoding="utf-8"), indent=2)
        print(f"\nQueue written to: {os.path.relpath(args.queue_file)}")
    else:
        print("No stale entries found.")
    return 0

if __name__ == "__main__":
    sys.exit(main())