#!/usr/bin/env python3
"""lvl10_trace.py - append an event to the lvl-10 process trace + update checklist status.
Usage: python memory/ops/lvl10_trace.py P4 triggered "level 9->10, report=..."
"""
import json, sys, os
from datetime import datetime
BASE = os.path.dirname(os.path.abspath(__file__))
TRACE = os.path.join(BASE, "lvl10-process-trace.jsonl")
CHECK = os.path.join(BASE, "lvl10-checklist.json")
def main():
    pid = sys.argv[1] if len(sys.argv) > 1 else "?"
    status = sys.argv[2] if len(sys.argv) > 2 else "triggered"
    detail = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
    ev = {"ts": datetime.now().isoformat(timespec="seconds"), "pid": pid, "status": status, "detail": detail}
    with open(TRACE, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev) + "\n")
    try:
        ck = json.load(open(CHECK, encoding="utf-8"))
        for p in ck["processes"]:
            if p["id"] == pid:
                p["status"] = status
                p["ts"] = ev["ts"]
                if detail: p["evidence"] = detail
        json.dump(ck, open(CHECK, "w", encoding="utf-8"), indent=2)
    except Exception as e:
        print("checklist update failed:", e)
    print(f"[trace] {pid} {status} {detail[:100]}")
if __name__ == "__main__":
    main()
