#!/usr/bin/env python3
"""video_engine_probe.py - Reel (Cb) day-0 engine-readiness probe.

Reads a one-line designation of the video-gen engine (engine class + endpoint),
probes it, and writes memory/designer/reel/video-engine-status.json so the
pipeline (see memory/ops/video-pipeline-handoff-2026-11-25.md) can auto-gate
stages 2-4: state=up -> Lumen/Splice/Outlet may run; state=down -> stay draft.

Stdlib only, Windows-safe. No external deps.

Usage:
  python video_engine_probe.py            # real probe, writes status json
  python video_engine_probe.py --selftest # prove classifier + integration down

NOTE (sandbox): the python tool sandbox forbids binding TCP listeners
(WinError 10013), so the live end-to-end "up" path is verified at the pure
classifier level here; it will be confirmed on a real host once an engine lands.
"""
import json, os, socket, sys, urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(HERE, "video-engine-config.json")
STATUS = os.path.join(HERE, "video-engine-status.json")
TIMEOUT = 2.0


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def classify(raw):
    """Pure decision: ('ok', detail) -> up ; ('err', reason) -> down."""
    if isinstance(raw, tuple) and len(raw) == 2 and raw[0] == "ok":
        return "up", raw[1]
    reason = raw[1] if isinstance(raw, tuple) and len(raw) == 2 else str(raw)
    return "down", reason


def _probe_tcp(host, port):
    try:
        with socket.create_connection((host, int(port)), timeout=TIMEOUT):
            return ("ok", "tcp connected %s:%d" % (host, port))
    except Exception as e:
        return ("err", "tcp fail: %s" % type(e).__name__ + ": " + str(e)[:120])


def _probe_http(url):
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
            code = getattr(r, "status", None) or r.getcode()
            return ("ok" if 200 <= int(code) < 400 else "err",
                    "http %s -> %s" % (url, code))
    except Exception as e:
        return ("err", "http fail: %s" % type(e).__name__ + ": " + str(e)[:120])


def load_config():
    if not os.path.exists(CFG):
        return None
    try:
        return json.loads(open(CFG, encoding="utf-8").read())
    except Exception as e:
        return {"_error": "config unparseable: %s" % e}


def probe(cfg=None):
    if cfg is None:
        cfg = load_config()
    if not cfg:
        raw = ("err", "no_config (video-engine-config.json absent)")
    elif "_error" in cfg:
        raw = ("err", cfg["_error"])
    elif cfg.get("url"):
        raw = _probe_http(cfg["url"])
    elif cfg.get("host") and cfg.get("port"):
        raw = _probe_tcp(cfg["host"], cfg["port"])
    else:
        raw = ("err", "config has no url/host+port")
    state, reason = classify(raw)
    status = {
        "state": state,
        "engine": (cfg or {}).get("engine", "unknown"),
        "host": (cfg or {}).get("host", ""),
        "url": (cfg or {}).get("url", ""),
        "checked_at": _now(),
        "reason": reason,
    }
    return state, status


def write_status(status):
    open(STATUS, "w", encoding="utf-8").write(json.dumps(status, indent=2) + "\n")


def selftest():
    print("== video_engine_probe --selftest ==")
    ok = True
    # 1) pure classifier: the exact decision the live path uses
    s, _ = classify(("ok", "connected"))
    r = "up" == s; ok &= r
    print("CLASSIFY-UP   : state=%s -> %s" % (s, "PASS" if r else "FAIL"))
    s, _ = classify(("err", "timeout"))
    r = "down" == s; ok &= r
    print("CLASSIFY-DOWN : state=%s -> %s" % (s, "PASS" if r else "FAIL"))
    # 2) integration DOWN through real probe code path (closed port)
    st, _ = probe({"engine": "none", "host": "127.0.0.1", "port": 1})
    r = "down" == st; ok &= r
    print("INTEG-DOWN    : state=%s -> %s" % (st, "PASS" if r else "FAIL"))
    # 3) no-config path
    st, _ = probe(None) if not os.path.exists(CFG) else (probe({"_error": "x"}), None)
    r = "down" == st; ok &= r
    print("NOCFG         : state=%s -> %s" % (st, "PASS" if r else "FAIL"))
    # 4) http error path (unreachable host, fast fail or timeout -> down)
    st, _ = probe({"engine": "none", "url": "http://127.0.0.1:1/x"})
    r = "down" == st; ok &= r
    print("HTTP-DOWN     : state=%s -> %s" % (st, "PASS" if r else "FAIL"))
    # NOTE: live end-to-end TCP/HTTP 'up' needs a reachable engine; sandbox blocks
    # socket bind (WinError 10013), so it is verified via CLASSIFY-UP above and on
    # a real host once an engine lands.
    print("SELFTEST " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    state, status = probe()
    write_status(status)
    print("video engine: %s (%s | %s)" % (state, status["engine"], status["reason"]))
