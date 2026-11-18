"""Fleet load probe - measures portal response time + resource usage.
Runs via schtask FleetLoadProbe every 30 min for 7-day collection window.
Output: memory/mechanic/load_trend.jsonl (one JSON line per run)"""
import json, time, urllib.request, socket, os, datetime, pathlib

PORTAL_URL = "http://127.0.0.1:8099/api/health/fleet"
OUT = pathlib.Path("memory/mechanic/load_trend.jsonl")

def probe():
    t0 = time.monotonic()
    try:
        req = urllib.request.Request(PORTAL_URL, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read())
            latency_ms = (time.monotonic() - t0) * 1000
            status = "OK"
    except Exception as e:
        latency_ms = (time.monotonic() - t0) * 1000
        body = {}
        status = f"ERR:{type(e).__name__}"

    # Resource snapshot
    import subprocess
    try:
        wmi = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Processor | Select-Object -ExpandProperty LoadPercentage"],
            capture_output=True, text=True, timeout=5)
        cpu = int(wmi.stdout.strip() or 0)
    except Exception:
        cpu = -1

    try:
        wmi2 = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_OperatingSystem | Select-Object -ExpandProperty FreePhysicalMemory"],
            capture_output=True, text=True, timeout=5)
        mem_free_kb = int(wmi2.stdout.strip() or 0)
    except Exception:
        mem_free_kb = -1

    entry = {
        "ts": datetime.datetime.now().isoformat(),
        "host": socket.gethostname(),
        "status": status,
        "latency_ms": round(latency_ms, 2),
        "cpu_pct": cpu,
        "mem_free_mb": mem_free_kb // 1024 if mem_free_kb > 0 else -1,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry

if __name__ == "__main__":
    e = probe()
    print(json.dumps(e))
