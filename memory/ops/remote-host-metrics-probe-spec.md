# Remote-Host Disk/Memory Probe — Scoped Spec (2026-11-18, Orchestrator)

**Trigger**: Builder flagged gap — "remote-host disk/memory requires a probe-side addition."
**Owner**: Mechanic (execution), Orchestrator (scope + verification).
**Estimated effort**: ~30 min (one endpoint + probe extension + one test run).

## Architecture

```
fleet_probe_v2.py (runs on White, central)
  ├── TCP latency probe to :8099 (existing)
  └── HTTP GET /api/host-metrics on each remote host  ← NEW
        returns: {disk: {pct_used, free_gb}, mem: {pct_used, free_mb}, model_loaded, portal_up}
```

`host_state.py` already has the collection logic (shutil.disk_usage + GlobalMemoryStatusEx).
The new endpoint reuses that logic inline in agent_portal.py so no import path issues on remotes.

## Step 1: Add `/api/host-metrics` to agent_portal.py

Insert after `_perf_snapshot()` (line ~843):

```python
def _host_metrics():
    """GET /api/host-metrics — local disk + memory + model state for remote probe."""
    import shutil, platform, ctypes
    out = {"host": platform.node(), "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
    # Disk (C:\\)
    try:
        u = shutil.disk_usage("C:\\")
        gb = 1024**3
        out["disk"] = {"total_gb": round(u.total/gb,1), "free_gb": round(u.free/gb,1),
                       "pct_used": round(100*u.used/u.total,1)}
    except Exception as e:
        out["disk"] = {"error": str(e)[:60]}
    # Memory
    try:
        class MSX(ctypes.Structure):
            _fields_ = [("dwLength",ctypes.c_ulong),("dwMemoryLoad",ctypes.c_ulong),
                        ("ullTotalPhys",ctypes.c_ulonglong),("ullAvailPhys",ctypes.c_ulonglong),
                        ("ullTotalPageFile",ctypes.c_ulonglong),("ullAvailPageFile",ctypes.c_ulonglong),
                        ("ullTotalVirtual",ctypes.c_ulonglong),("ullAvailVirtual",ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual",ctypes.c_ulonglong)]
        s = MSX(); s.dwLength = ctypes.sizeof(MSX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s))
        mb = 1024**2
        out["mem"] = {"total_mb": int(s.ullTotalPhys/mb), "free_mb": int(s.ullAvailPhys/mb),
                      "pct_used": int(s.dwMemoryLoad)}
    except Exception as e:
        out["mem"] = {"error": str(e)[:60]}
    # Model + portal
    import urllib.request
    try:
        with urllib.request.urlopen("http://127.0.0.1:8888/api/health", timeout=2) as r:
            d = json.loads(r.read())
            out["model_loaded"] = True
    except Exception:
        out["model_loaded"] = False
    return {"ok": True, **out}
```

Register route: `elif path == "/api/host-metrics": send_json(_host_metrics())`

## Step 2: Extend fleet_probe_v2.py

Add to `probe_target()` or as a new function `probe_host_metrics(host, port)`:
```python
def probe_host_metrics(host, port=8099, timeout=5.0):
    """GET http://host:port/api/host-metrics — returns dict or None on failure."""
    import urllib.request
    try:
        url = f"http://{host}:{port}/api/host-metrics"
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception:
        return None
```

In the main probe loop, after the latency probe, call `probe_host_metrics` and merge into the entry:
```python
entry["disk_pct"] = hm.get("disk", {}).get("pct_used") if hm else None
entry["mem_pct"]  = hm.get("mem", {}).get("pct_used") if hm else None
```

## Step 3: Alert thresholds (add to main loop)

| Metric | WARN | CRIT |
|--------|------|------|
| disk_pct | >85% | >95% |
| mem_pct | >90% | >97% |

Emit same WARN/CRIT log format as existing latency alerts. Append to `memory/ops/slo-alerts.jsonl`.

## Step 4: Deploy + verify

1. Edit agent_portal.py on White → restart portal (elev.py).
2. Copy updated agent_portal.py to Red/Pale/Black via SMB mirror (automatic) or manual copy.
3. Restart portals on remotes (or wait for next mirror cycle if auto-restart is wired).
4. Run `python memory/ops/fleet_probe_v2.py` from White → verify JSONL entries include disk_pct/mem_pct for all 4 hosts.
5. Record evidence: `python memory/researcher/goal_ledger.py --record mechanic <goal#> --note '...'`

## Acceptance Test

One run of fleet_probe_v2.py produces entries with non-null `disk_pct` and `mem_pct` for all 4 hosts (White + 3 remotes). If a remote portal is down, those fields are null (graceful degradation, no crash).
