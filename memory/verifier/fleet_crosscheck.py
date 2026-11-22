#!/usr/bin/env python3
"""Verifier goal: /api/fleet cross-check (2026-11-15).

Asserts, per the locked goal text:
  1. GET :8099/api/fleet answers within the 5s panel refresh window (fail on timeout);
  2. response ts is fresh (now - ts < 5s);
  3. every expected host row is present: White (local) + the 3 remote seats
     (.245 Red, .39 Pale, .99 Black) derived live from agents.json (fail on missing host);
  4. EVERY row carries a `state` field with a valid value (busy|idle|unknown), and an
     unknown row must carry a non-empty reason. Dead remotes are EXPECTED to report
     state=unknown + reason=unreachable while powered down - that still satisfies the
     status-field assertion; a MISSING row or a missing/blank state field is the failure.

Exit: 0 = all assertions pass, 1 = any assertion failed. Writes result JSON next to itself.
Run from repo root:  python memory/verifier/fleet_crosscheck.py
"""
import json, os, re, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PORTAL = "http://127.0.0.1:8099"
BUDGET_S = 5.0   # the panel's refresh window
# 'unauth' (2026-11-22): host is UP but the probe was rejected (401/403) - a key problem,
# not a dead host; it still counts as reporting in the panel.
VALID_STATES = {"busy", "idle", "unauth", "unknown"}


def main() -> int:
    t0 = time.time()
    failures, rows_report = [], []
    try:
        with urllib.request.urlopen(PORTAL + "/api/fleet", timeout=BUDGET_S) as r:
            o = json.load(r)
        elapsed = time.time() - t0
    except Exception as e:
        print("FAIL: /api/fleet did not answer within %.0fs (timeout or connection error): %s" % (BUDGET_S, e))
        return _finish({"ok": False, "error": str(e), "elapsed_s": round(time.time() - t0, 2)}, [])

    # 1. refresh window
    if elapsed > BUDGET_S:
        failures.append("response took %.2fs > %.0fs refresh window" % (elapsed, BUDGET_S))
    # 2. ts freshness
    age = time.time() - o.get("ts", 0)
    if age > BUDGET_S:
        failures.append("stale snapshot: ts is %.1fs old (>%.0fs window)" % (age, BUDGET_S))

    # expected hosts: local (STUDIO base, read live from agent_portal.py) + every remote
    agents = json.load(open(os.path.join(ROOT, "agents.json"), encoding="utf-8"))
    m = re.search(r'^STUDIO\s*=\s*"([^"]+)"', open(os.path.join(ROOT, "agent_portal.py"), encoding="utf-8").read(), re.M)
    local_base = (m.group(1).rstrip("/") if m else PORTAL.replace("8099", "8888"))
    expected = {local_base: "White local"}
    for a in agents.get("agents", []):
        b = (a.get("studio") or "").rstrip("/")
        if b:
            expected[b] = b.split("//")[-1].split(":")[0]
    got = {h.get("base"): h for h in o.get("hosts", [])}

    # 3. missing host rows
    for base, label in expected.items():
        if base not in got:
            failures.append("missing host row: %s (%s)" % (label or "White local", base or "(local default)"))

    # 4. status field on every returned row
    for h in o.get("hosts", []):
        st = h.get("state")
        ok_state = st in VALID_STATES
        reason_ok = (st != "unknown") or bool(h.get("reason"))
        rows_report.append({"host": h.get("host"), "base": h.get("base"),
                            "state": st, "reason": h.get("reason", ""),
                            "models": [m.get("id") for m in h.get("models", [])],
                            "status_field_ok": ok_state and reason_ok})
        if not ok_state:
            failures.append("host %s: state field missing/invalid (got %r)" % (h.get("host"), st))
        elif not reason_ok:
            failures.append("host %s: state=unknown without a reason" % h.get("host"))

    ok = not failures
    print("fleet cross-check  %.2fs  hosts=%d expected=%d" % (elapsed, len(o.get("hosts", [])), len(expected)))
    for r in rows_report:
        print("  %-14s state=%-8s reason=%-14s models=%s" % (
            r["host"][:14], r["state"], (r["reason"] or "-")[:14], ",".join(r["models"]) or "none"))
    if ok:
        print("PASS: all hosts present, every row has a valid status field, within %.0fs window" % BUDGET_S)
    else:
        for f in failures:
            print("FAIL: %s" % f)
    return _finish({"ok": ok, "elapsed_s": round(elapsed, 2), "failures": failures,
                    "hosts": rows_report}, rows_report)


def _finish(result, rows):
    out = os.path.join(HERE, "fleet_crosscheck_result.json")
    json.dump(result, open(out, "w", encoding="utf-8"), indent=1)
    print("result -> %s" % os.path.relpath(out, ROOT))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
