#!/usr/bin/env python3
"""host_state.py (2026-11-17, Mechanic goal 7): per-host resource + model state collector.
Writes one JSON line to memory/ops/host-state.jsonl on each run. Designed to be called
by a scheduled task or the fleet probe cycle on each host. All-local, no network calls.

Fields collected:
- ts: ISO timestamp
- host: platform.node()
- disk: {total_gb, used_gb, free_gb, pct_used} for C:\
- mem: {total_mb, used_mb, free_mb, pct_used}
- model_loaded: bool (Studio :8888 /api/health responds with model info)
- portal_up: bool (local :8099 responds)

Usage: python memory/ops/host_state.py [--quiet]
"""
import json, os, sys, time, datetime, platform, shutil, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(HERE, "host-state.jsonl")
HOSTNAME = platform.node()

def _disk():
    for path in ("C:\\", os.path.expanduser("~"), "."):
        try:
            u = shutil.disk_usage(path)
            gb = 1024**3
            return {"total_gb": round(u.total/gb, 1), "used_gb": round(u.used/gb, 1),
                    "free_gb": round(u.free/gb, 1), "pct_used": round(100*u.used/u.total, 1)}
        except Exception:
            continue
    return {"error": "all disk probes failed"}

def _mem():
    try:
        import ctypes
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        mb = 1024**2
        total, avail = int(stat.ullTotalPhys/mb), int(stat.ullAvailPhys/mb)
        return {"total_mb": total, "used_mb": total - avail, "free_mb": avail,
                "pct_used": int(stat.dwMemoryLoad)}
    except Exception as e:
        return {"error": str(e)[:80]}

def _model_loaded():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8888/api/health", timeout=3) as r:
            d = json.loads(r.read())
            return {"loaded": True, "detail": d.get("model", d.get("status", "ok"))[:60]}
    except Exception:
        return {"loaded": False}

def _portal_up():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8099/api/goals", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False

def main(quiet=False):
    entry = {
        "ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "host": HOSTNAME,
        "disk": _disk(),
        "mem": _mem(),
        "model": _model_loaded(),
        "portal_up": _portal_up(),
    }
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    if not quiet:
        print(json.dumps(entry, indent=2))

if __name__ == "__main__":
    main(quiet="--quiet" in sys.argv)
