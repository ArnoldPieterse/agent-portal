#!/usr/bin/env python3
"""fleet_stats_collect.py - per-host resource stats collector (Mechanic goal #7).

Runs locally on each host (via schtask or manual). Appends a JSON line to
memory/ops/fleet-stats.jsonl with: disk usage %, memory usage %, portal uptime.
The mirror syncs this file across hosts; /api/health/fleet reads the latest
entry per host.

Usage:
  python fleet_stats_collect.py           # collect + append
  python fleet_stats_collect.py --last    # print most recent entry for this host
"""
import json, os, sys, time, platform, subprocess, datetime

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATS_FILE = os.path.join(HERE, "memory", "ops", "fleet-stats.jsonl")
HOSTNAME = platform.node().split(".")[0]  # e.g. "White", "Red", etc.
PORTAL_PORT = 8099


def _disk_usage_pct():
    """Return used % of the system drive (C: on Windows)."""
    try:
        import shutil
        total, used, free = shutil.disk_usage("C:\\")
        return round(100 * used / total, 1) if total else None
    except Exception:
        return None


def _memory_usage_pct():
    """Return system memory usage % via tasklist-free heuristic (no psutil dep)."""
    try:
        r = subprocess.run(
            ["wmic", "OS", "get", "TotalVisibleMemorySize,FreePhysicalMemory"],
            capture_output=True, text=True, timeout=10,
            creationflags=0x08000000
        )
        lines = [l.strip() for l in r.stdout.splitlines() if l.strip() and not l[0].isdigit() is False]
        # wmic output: header line then values line
        vals = [l for l in r.stdout.splitlines() if l.strip().replace(" ", "").isdigit()]
        if len(vals) >= 2:
            total_kb = int(vals[0].strip())
            free_kb = int(vals[1].strip())
            return round(100 * (total_kb - free_kb) / total_kb, 1) if total_kb else None
    except Exception:
        pass
    # Fallback: try ctypes GlobalMemoryStatusEx
    try:
        import ctypes
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return int(stat.dwMemoryLoad)
    except Exception:
        return None


def _portal_uptime_s():
    """Check if portal is running locally; return uptime seconds or None."""
    try:
        import urllib.request
        r = urllib.request.urlopen(f"http://127.0.0.1:{PORTAL_PORT}/api/health", timeout=3)
        data = json.loads(r.read())
        return int(data.get("uptime_s", 0))
    except Exception:
        return None


def _model_load_status():
    """Read agents.json and report which models are loaded (from local probe cache)."""
    try:
        cfg = json.load(open(os.path.join(HERE, "agents.json"), encoding="utf-8"))
        agents = cfg.get("agents", [])
        return {a["name"]: a.get("model_id", "unknown") for a in agents}
    except Exception:
        return None


def collect():
    entry = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "host": HOSTNAME,
        "disk_pct": _disk_usage_pct(),
        "mem_pct": _memory_usage_pct(),
        "portal_uptime_s": _portal_uptime_s(),
    }
    os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
    with open(STATS_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def main():
    if "--last" in sys.argv:
        if not os.path.exists(STATS_FILE):
            print("no stats file yet")
            return
        lines = [l for l in open(STATS_FILE) if l.strip()]
        last = None
        for line in lines:
            try:
                d = json.loads(line)
                if d.get("host") == HOSTNAME:
                    last = d
            except Exception:
                continue
        print(json.dumps(last, indent=2) if last else "no entry for this host")
    else:
        e = collect()
        print(f"collected: {json.dumps(e)}")


if __name__ == "__main__":
    main()