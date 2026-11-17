#!/usr/bin/env python3
"""host_metrics_probe.py - Builder, 2026-11-18 (assists Mechanic goal #7 follow-on).

The PROBE-SIDE half of the remote-host disk/memory gap I flagged. Mechanic already
shipped the SERVER side (each host reports its own disk/memory via /api/health/fleet
+ /api/ops, 15/15 tests). What was missing: the CENTRAL probe (fleet_probe_v2.py)
never pulls those metrics from remotes nor alerts on them. This module is the ready
to-apply client that drops into fleet_probe_v2.run_probe() in ~3 lines.

Stdlib-only, no side effects, importable + unit-testable in sandbox.
Spec: memory/ops/remote-host-metrics-probe-spec.md (Orchestrator-scoped).

Wiring into fleet_probe_v2.py run_probe loop (after the latency probe):
    from host_metrics_probe import probe_host_metrics, classify_disk_mem, format_alert
    hm = probe_host_metrics(host, port)
    entry["disk_pct"] = hm["disk_pct"]; entry["mem_pct"] = hm["mem_pct"]   # None-safe
    sev, which = classify_disk_mem(entry.get("disk_pct"), entry.get("mem_pct"))
    if sev != "OK": save_alert(format_alert(host, port, sev, which, entry))
"""
import json
import urllib.request

# Candidate endpoints, in order. First that yields a parseable dict wins.
#  - /api/host-metrics : the canonical NEW endpoint from the Orchestrator spec
#  - /api/ops          : Mechanic's existing endpoint (already has a memory field)
CANDIDATE_PATHS = ["/api/host-metrics", "/api/ops"]

# Thresholds per spec table.
DISK_WARN, DISK_CRIT = 85.0, 95.0
MEM_WARN, MEM_CRIT = 90.0, 97.0


def _pct(node):
    """Pull a percentage out of a dict-or-number under common key spellings."""
    if isinstance(node, (int, float)):
        return float(node)
    if isinstance(node, dict):
        for k in ("pct_used", "percent", "pct", "used_pct"):
            v = node.get(k)
            if isinstance(v, (int, float)):
                return float(v)
    return None


def normalize(payload, source=None):
    """Map any of the known server shapes -> {disk_pct, mem_pct, model_loaded}.
    Returns a dict with values or None where absent (graceful)."""
    out = {"disk_pct": None, "mem_pct": None, "model_loaded": None, "source": source}
    if not isinstance(payload, dict):
        return out
    out["disk_pct"] = _pct(payload.get("disk", payload.get("disk_usage")))
    mem = payload.get("mem", payload.get("memory"))
    out["mem_pct"] = _pct(mem)
    for k in ("model_loaded", "models_loaded", "model"):
        if k in payload:
            v = payload[k]
            out["model_loaded"] = bool(v) if not isinstance(v, dict) else bool(v.get("loaded", True))
            break
    return out


def probe_host_metrics(host, port=8099, timeout=5.0):
    """GET the remote's own disk/memory/model state. Returns normalized dict with
    ok=True on success; ok=False (all metrics None) on any failure - never raises,
    so a down remote degrades to null fields instead of crashing the probe loop."""
    result = {"host": host, "port": port, "ok": False, "portal_up": False,
              "disk_pct": None, "mem_pct": None, "model_loaded": None, "source": None}
    for path in CANDIDATE_PATHS:
        url = "http://%s:%d%s" % (host, port, path)
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                payload = json.loads(r.read())
        except Exception:
            continue
        result.update(normalize(payload, source=path))
        result["ok"] = True
        result["portal_up"] = True
        break
    return result


def classify_disk_mem(disk_pct, mem_pct):
    """Return (severity, which). severity in OK/WARN/CRIT; which is the worst metric.
    None-safe: a missing metric is simply not considered."""
    worst, why = "OK", None
    for val, warn, crit, name in (
        (disk_pct, DISK_WARN, DISK_CRIT, "disk"),
        (mem_pct, MEM_WARN, MEM_CRIT, "mem"),
    ):
        if val is None:
            continue
        if val > crit and worst != "CRIT":
            worst, why = "CRIT", name
        elif val > warn and worst == "OK":
            worst, why = "WARN", name
    return worst, why


def format_alert(host, port, severity, which, entry):
    """One-line alert matching the existing slo-alerts.jsonl WARN/CRIT style."""
    val = (entry or {}).get("disk_pct") if which == "disk" else (entry or {}).get("mem_pct")
    return {"severity": severity, "metric": which, "host": host, "port": port,
            "value": val, "msg": "%s %s on %s:%d (%.1f%%)" % (
                severity, which, host, port, (val or 0.0))}


if __name__ == "__main__":
    # manual smoke: python host_metrics_probe.py <host> [port]
    import sys
    h = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    p = int(sys.argv[2]) if len(sys.argv) > 2 else 8099
    print(json.dumps(probe_host_metrics(h, p), indent=2))
