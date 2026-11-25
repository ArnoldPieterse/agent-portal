#!/usr/bin/env python3
# red_probe.py - focused TCP+API check on Red host (IP_RED).
# Run:  python elev.py python memory/forge/red_probe.py
import socket, time, json, sys, urllib.request, datetime

RED_IP = "IP_RED"
PORT   = 8888
result = {"ts": datetime.datetime.now().isoformat(), "host": "Red", "ip": RED_IP}

def probe_tcp(ip, port, timeout=5):
    start = time.monotonic()
    try:
        s = socket.create_connection((ip, port), timeout=timeout)
        ms = round((time.monotonic()-start)*1000, 1)
        s.close()
        return ms, None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"

def probe_api(ip, port, path):
    url = f"http://{ip}:{port}{path}"
    try:
        r = urllib.request.urlopen(url, timeout=5)
        body = r.read().decode("utf-8", "replace")[:400]
        return r.status, body
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"

# TCP on model port
tcp_ms, tcp_err = probe_tcp(RED_IP, PORT)
result["tcp_8888"] = {"open": tcp_ms is not None, "ms": tcp_ms, "err": tcp_err}
print(f"TCP :8888  {'OPEN %s ms' % tcp_ms if tcp_ms is not None else 'CLOSED %s' % tcp_err}")

# Base-host liveness (SMB / HTTP) to confirm OS up even without model
for port, label in [(445, "SMB"), (80, "HTTP")]:
    ms, err = probe_tcp(RED_IP, port, timeout=3)
    result[f"tcp_{label.lower()}"] = {"open": ms is not None, "ms": ms, "err": err}
    print(f"TCP {label:4}:{port}  {'OPEN %s ms' % ms if ms is not None else 'CLOSED (%s)' % err}")

# API only if model port open
if tcp_ms is not None:
    for path in ["/v1/models", "/health"]:
        st, body = probe_api(RED_IP, PORT, path)
        result[f"api_{path.strip('/')}"] = {"status": st, "body": body}
        print(f"GET {path} -> {st}: {body[:200]}")

# Verdict
if tcp_ms is not None and result.get("api_models", {}).get("status") == 200:
    verdict = "MODEL_LOADED"
elif tcp_ms is not None:
    verdict = "PORT_OPEN_NO_API"
elif result.get("tcp_smb", {}).get("open") or result.get("tcp_http", {}).get("open"):
    verdict = "OS_UP_NO_MODEL"
else:
    verdict = "UNREACHABLE"
result["verdict"] = verdict
print(f"VERDICT: {verdict}")

with open("memory/forge/red_probe_last.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)
print("saved memory/forge/red_probe_last.json")
sys.exit(0 if verdict in ("MODEL_LOADED",) else 1)
