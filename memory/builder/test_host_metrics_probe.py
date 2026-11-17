#!/usr/bin/env python3
"""test_host_metrics_probe.py - sandbox-runnable unit tests (no network, no 4 hosts).
Proves the probe-side logic is correct BEFORE Mechanic wires it into fleet_probe_v2.py
and runs it against live remotes. Run: python memory/builder/test_host_metrics_probe.py
"""
import io
import os
import sys
import json
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import host_metrics_probe as hmp

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("  ok  -", name)
    else:
        FAIL += 1
        print("  FAIL-", name)


def _ok_json(payload):
    resp = mock.Mock()
    resp.read.return_value = json.dumps(payload).encode()
    resp.__enter__ = lambda s: s
    resp.__exit__ = lambda s, *a: False
    return resp


def test_normalize_spec_shape():
    n = hmp.normalize({"disk": {"pct_used": 88.0}, "mem": {"pct_used": 91.0},
                       "model_loaded": True}, source="/api/host-metrics")
    check("spec shape disk", n["disk_pct"] == 88.0)
    check("spec shape mem", n["mem_pct"] == 91.0)
    check("spec shape model", n["model_loaded"] is True)


def test_normalize_ops_fallback():
    # Mechanic's /api/ops uses 'memory' key + bare-number pct + models_loaded
    n = hmp.normalize({"memory": 93, "models_loaded": ["a", "b"]}, source="/api/ops")
    check("ops fallback mem (bare number)", n["mem_pct"] == 93.0)
    check("ops fallback model truthy list", n["model_loaded"] is True)
    check("ops fallback disk absent -> None", n["disk_pct"] is None)


def test_normalize_garbage():
    n = hmp.normalize({"foo": "bar"})
    check("garbage -> all None", n["disk_pct"] is None and n["mem_pct"] is None
          and n["model_loaded"] is None)


def test_probe_success_first_endpoint():
    with mock.patch.object(hmp.urllib.request, "urlopen",
                           return_value=_ok_json({"disk": {"pct_used": 50.0},
                                                 "mem": {"pct_used": 40.0},
                                                 "model_loaded": True})) as m:
        r = hmp.probe_host_metrics("10.0.0.5", 8099)
    check("probe ok=True", r["ok"] is True and r["portal_up"] is True)
    check("probe disk", r["disk_pct"] == 50.0)
    check("probe source=first candidate", r["source"] == "/api/host-metrics")
    check("probe hit canonical url first",
          m.call_args[0][0] == "http://10.0.0.5:8099/api/host-metrics")


def test_probe_fallback_to_ops():
    def side(url, timeout=5.0):
        if url.endswith("/api/host-metrics"):
            raise OSError("404 not found")
        return _ok_json({"memory": 77})
    with mock.patch.object(hmp.urllib.request, "urlopen", side_effect=side) as m:
        r = hmp.probe_host_metrics("10.0.0.6", 8099)
    check("fallback ok=True", r["ok"] is True)
    check("fallback mem from /api/ops", r["mem_pct"] == 77.0)
    check("fallback source=/api/ops", r["source"] == "/api/ops")


def test_probe_down_remote_graceful():
    with mock.patch.object(hmp.urllib.request, "urlopen", side_effect=OSError("conn refused")):
        r = hmp.probe_host_metrics("10.9.9.9", 8099)
    check("down remote ok=False (no raise)", r["ok"] is False and r["portal_up"] is False)
    check("down remote fields None", r["disk_pct"] is None and r["mem_pct"] is None)


def test_classify_thresholds():
    check("ok", hmp.classify_disk_mem(50.0, 40.0) == ("OK", None))
    check("disk warn", hmp.classify_disk_mem(86.0, 10.0) == ("WARN", "disk"))
    check("disk crit beats mem warn", hmp.classify_disk_mem(96.0, 91.0) == ("CRIT", "disk"))
    check("mem warn", hmp.classify_disk_mem(10.0, 92.0) == ("WARN", "mem"))
    check("mem crit", hmp.classify_disk_mem(10.0, 98.0) == ("CRIT", "mem"))
    check("null-safe ok", hmp.classify_disk_mem(None, None) == ("OK", None))
    check("null disk, mem crit", hmp.classify_disk_mem(None, 99.0) == ("CRIT", "mem"))


def test_format_alert():
    e = {"disk_pct": 96.0, "mem_pct": 10.0}
    a = hmp.format_alert("red", 8099, "CRIT", "disk", e)
    check("alert metric", a["metric"] == "disk" and a["value"] == 96.0)
    check("alert msg renders", "CRIT disk on red:8099" in a["msg"])


def main():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        print(fn.__name__)
        fn()
    print("\n%d/%d PASS" % (PASS, PASS + FAIL))
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
