#!/usr/bin/env python3
"""
non-sandbox-seat eligibility gate (Forge) - Fleet Autonomy Convergence assist for Pixel #6.

Pixel goal #6 (live CDP screenshot leg @375/@768) is blocked on a NON-SANDBOX seat with:
  (1) Edge/Chrome present, (2) `websockets` importable, (3) portal up on :8099.
The one-command unblock is:  python memory/pixel/cdp_375_dom_check.py   (see memory/ops/blockers.md).

This gate does NOT re-probe the screenshot wall. It is a BOUNDED preflight that answers,
with an exit code + JSON evidence, whether the current seat can run that one command.
That turns "waiting on a seat" into a reproducible green/red convergence signal.

Every network op is hard-timeout-capped so it can never hang (the 300s cdp_375_dom_check.py
hang is exactly what this avoids). Stdlib-only, idempotent.

Exit codes:
  0 = ELIGIBLE   - all required prereqs met; prints the exact run command.
  1 = INELIGIBLE - one or more required prereqs missing (reasons listed).
  2 = PROBE ERROR- a required check itself errored/timed out beyond its bound.

Usage:
  python memory/forge/nonsandbox_seat_gate.py            # report eligibility only (safe)
  python memory/forge/nonsandbox_seat_gate.py --fire     # if ELIGIBLE, run the one-command unblock
  python memory/forge/nonsandbox_seat_gate.py --json-out <path>
"""
import json, os, socket, subprocess, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # .../AgentPortal
CDP_SCRIPT = ROOT / "memory/pixel/cdp_375_dom_check.py"
PORTAL_PORT = 8099
CDP_DEVTOOLS_PORT = 9222                            # advisory: already-exposed DevTools endpoint
TIMEOUT_S = 4                                       # per network probe bound
ELEV_TIMEOUT_S = 20                                 # elev.py escalation probe bound
FIRE_TIMEOUT_S = 200                                # bounded run of the real unblock (under 300s tool cap)

EDGE_PATHS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]


def find_edge():
    for p in EDGE_PATHS:
        if Path(p).exists():
            return p
    return None


def websockets_ok():
    try:
        import websockets  # noqa: F401
        return True, "imported"
    except Exception as e:
        return False, repr(e)


def http_get_json(url, timeout=TIMEOUT_S):
    """Bounded HTTP GET. Returns (ok, detail). Never raises past the socket timeout."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            body = r.read(65536)
            return True, f"HTTP {r.status} ({len(body)}B)"
    except Exception as e:
        return False, repr(e)


def portal_up():
    ok, detail = http_get_json(f"http://127.0.0.1:{PORTAL_PORT}/", timeout=TIMEOUT_S)
    return ok, detail


def cdp_endpoint_probe():
    """Advisory: is a DevTools /json endpoint ALREADY exposed on loopback? (not the full launch)"""
    try:
        s = socket.create_connection(("127.0.0.1", CDP_DEVTOOLS_PORT), timeout=TIMEOUT_S)
        s.close()
        return True, f"loopback :{CDP_DEVTOOLS_PORT} open"
    except Exception as e:
        return False, repr(e)


def elev_alive():
    """Advisory: can `python elev.py` escalate on this seat? (re-probe 2026-11-27 found it DEAD here)."""
    try:
        p = subprocess.run([sys.executable, str(ROOT / "elev.py"), "--shell", "echo ok"],
                           capture_output=True, text=True, timeout=ELEV_TIMEOUT_S)
        return (p.returncode == 0), f"exit {p.returncode}"
    except subprocess.TimeoutExpired:
        return False, f"timeout>{ELEV_TIMEOUT_S}s"
    except Exception as e:
        return False, repr(e)


def main():
    args = set(sys.argv[1:])
    fire = "--fire" in args
    json_out = None
    if "--json-out" in args:
        i = sys.argv.index("--json-out")
        json_out = Path(sys.argv[i + 1]) if i + 1 < len(sys.argv) else None

    t0 = time.time()
    checks = {}

    edge = find_edge()
    checks["edge_present"] = {"ok": bool(edge), "detail": edge or "no msedge.exe/chrome.exe at known paths"}

    wok, wdet = websockets_ok()
    checks["websockets_ok"] = {"ok": wok, "detail": wdet}

    pok, pdet = portal_up()
    checks["portal_up_8099"] = {"ok": pok, "detail": pdet}

    # advisory (do not gate the verdict)
    cok, cdet = cdp_endpoint_probe()
    checks["cdp_endpoint_advisory"] = {"ok": cok, "detail": cdet}
    ek, edet = elev_alive()
    checks["elev_alive_advisory"] = {"ok": ek, "detail": edet}

    required = ["edge_present", "websockets_ok", "portal_up_8099"]
    missing = [k for k in required if not checks[k]["ok"]]
    verdict = "ELIGIBLE" if not missing else "INELIGIBLE"
    exit_code = 0 if verdict == "ELIGIBLE" else 1

    result = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
        "seat": os.environ.get("COMPUTERNAME", "?"),
        "verdict": verdict,
        "missing_required": missing,
        "checks": checks,
        "elapsed_s": round(time.time() - t0, 2),
        "unblock_command": f"python {CDP_SCRIPT.relative_to(ROOT)}",
        "cdp_script_present": CDP_SCRIPT.exists(),
    }

    if verdict == "ELIGIBLE" and fire:
        print(f"[gate] ELIGIBLE - firing unblock (bounded {FIRE_TIMEOUT_S}s)...")
        try:
            p = subprocess.run([sys.executable, str(CDP_SCRIPT)],
                               capture_output=True, text=True, timeout=FIRE_TIMEOUT_S)
            result["fire"] = {"exit": p.returncode,
                              "tail": (p.stdout or p.stderr)[-500:]}
        except subprocess.TimeoutExpired:
            result["fire"] = {"exit": None, "tail": f"timeout>{FIRE_TIMEOUT_S}s (CDP egress likely blocked)"}
        exit_code = 0 if result["fire"].get("exit") == 0 else 1
    elif verdict == "ELIGIBLE" and not fire:
        result["note"] = "eligible but --fire not set; run the unblock_command to close Pixel #6"

    out = {
        "edge_present": checks["edge_present"]["detail"],
        "websockets_ok": checks["websockets_ok"]["ok"],
        "portal_up_8099": checks["portal_up_8099"]["ok"],
        "cdp_endpoint_advisory": checks["cdp_endpoint_advisory"]["detail"],
        "elev_alive_advisory": checks["elev_alive_advisory"]["detail"],
        "missing_required": missing,
        "verdict": verdict,
        "elapsed_s": result["elapsed_s"],
    }
    if "fire" in result:
        out["fire"] = result["fire"]

    dest = json_out or (ROOT / "memory/forge/nonsandbox_seat_gate_last.json")
    try:
        dest.write_text(json.dumps(result, indent=2), encoding="utf-8")
        out["report"] = str(dest.relative_to(ROOT)) if str(dest).startswith(str(ROOT)) else str(dest)
    except Exception as e:
        out["report_err"] = repr(e)

    print(json.dumps(out, indent=1))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
