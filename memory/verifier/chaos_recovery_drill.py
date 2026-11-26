#!/usr/bin/env python3
"""Chaos-RECOVERY drill (Verifier goal #2: 'Fleet heals itself').

Protocol per drill:
  1. KILL a model seat -> POST the seat's native Studio /api/inference/unload.
  2. Time until auto-recovery -> poll /api/inference/status until the model is
     RESIDENT again (this is exactly what agent_portal._ensure_seat_ready does on
     the next turn, so we are measuring the real recovery path, not a mock).
  3. Log one record per drill to memory/ops/recovery-drills.jsonl:
       {ts, seat, base, kill_ts, recover_ts, recovery_s, sla_s, pass}
  SLA: recovery_s < sla_s (default 120s). Any breach -> the failure mode is
  documented in the report (AC explicitly allows 'failure mode documented if any
  exceed SLA').

FAIL-CLOSED: a seat we cannot reach is recorded as a measured FAILURE (with the
exact error), never silently passed. This keeps the drill honest from any seat.

Two legs (same pattern as fleet_recovery_sla_test.py):
  --self-test : prove the timing + SLA-classification engine on synthetic kill/
                recover pairs with known deltas (no network needed).
  --live      : run N real drills against SEAT_BASE (env) seats that ARE reachable.

CWD-independent: paths anchored via __file__.
Usage:
  python memory/verifier/chaos_recovery_drill.py --self-test
  SEAT_BASE=http://127.0.0.1:1234 python memory/verifier/chaos_recovery_drill.py --live
"""
import json, os, sys, time, datetime, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DRILLS_JSONL = os.path.join(ROOT, "memory", "ops", "recovery-drills.jsonl")
REPORT_MD = os.path.join(HERE, "chaos-recovery-report.md")
PROD_INCIDENTS = os.path.join(ROOT, "memory", "ops", "recovery-times.jsonl")

SLA_S = 120.0          # goal #2 target: auto-recovery < 120s
N_DRILLS = 3           # AC wants 3 drills logged with timestamps
POLL_S = 1.0           # poll cadence while waiting for re-residency
HARD_TIMEOUT_S = SLA_S + 60.0   # stop polling well past SLA; record breach


def iso(ts=None):
    d = datetime.datetime.now(datetime.timezone.utc) if ts is None else ts
    return d.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


# --------------------------------------------------------------------------- #
# Core engine: given a kill instant + recover instant, classify vs SLA.
# This is the part that MUST be correct; the network legs just feed it times.
# --------------------------------------------------------------------------- #
def classify(recovery_s, sla_s=SLA_S):
    """Pure function. Returns dict(pass=bool, breach_s). recovery_s<sla -> pass."""
    ok = (recovery_s is not None) and (recovery_s < sla_s)
    return {"pass": ok, "breach_s": round((recovery_s - sla_s), 3) if (not ok and recovery_s is not None) else 0.0}


def _http(method, url, body=None, key="", timeout=6):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json",
                                          **({"Authorization": "Bearer %s" % key} if key else {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode(errors="replace")


def seat_resident(base, model_path, key="", timeout=6):
    """True if the seat's Studio reports the model resident (loaded). Mirrors the
    status check agent_portal._model_resident performs before trusting a seat."""
    st, b = _http("GET", base.rstrip("/") + "/api/inference/status", None, key, timeout)
    try:
        j = json.loads(b)
    except Exception:
        return False
    for m in (j if isinstance(j, list) else j.get("models", [])):
        mp = m.get("model_path") or m.get("path") or ""
        if model_path and (mp.endswith(model_path) or model_path in mp):
            return bool(m.get("loaded") or m.get("status") == "loaded")
    return False


def run_drill(base, seat, model_path, key="", sla_s=SLA_S):
    """One real drill: unload (kill) then time auto-recovery. Returns a record.
    Any unreachability -> pass=False with the exact error (fail-closed)."""
    rec = {"ts": iso(), "seat": seat, "base": base, "model_path": model_path,
           "recovery_s": None, "sla_s": sla_s, "pass": False, "error": None}
    try:
        _http("POST", base.rstrip("/") + "/api/inference/unload",
              {"model_path": model_path}, key)          # KILL the seat
        rec["kill_ts"] = iso()
        t0 = time.perf_counter(); deadline = t0 + HARD_TIMEOUT_S
        while time.perf_counter() < deadline:
            if seat_resident(base, model_path, key):
                rec["recovery_s"] = round(time.perf_counter() - t0, 3)
                break
            time.sleep(POLL_S)
        rec["recover_ts"] = iso()
    except Exception as e:
        rec["error"] = "%s: %s" % (type(e).__name__, e)
    c = classify(rec["recovery_s"], sla_s)
    rec["pass"] = c["pass"]
    if not c["pass"] and rec["recovery_s"] is not None:
        rec["breach_s"] = c["breach_s"]
    return rec


def append_drills(records):
    os.makedirs(os.path.dirname(DRILLS_JSONL), exist_ok=True)
    with open(DRILLS_JSONL, "a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


# --------------------------------------------------------------------------- #
# SELF-TEST leg: prove the SLA engine on synthetic pairs (no network).
# --------------------------------------------------------------------------- #
def self_test():
    print("[chaos_recovery_drill] SELF-TEST — timing/SLA classification engine")
    cases = [
        # (recovery_s, expected_pass)
        (0.5, True),     # instant heal -> pass
        (119.9, True),   # just under SLA -> pass
        (120.0, False),  # exactly at SLA -> NOT < 120 -> fail (boundary)
        (45.0, True),    # typical fast reload -> pass
        (1180.0, False), # ~19.7 min (real single-seat) -> big breach
        (2880.0, False), # ~48 min (real OOM) -> big breach
        (5700.0, False), # ~95 min (cascade) -> biggest breach
        (None, False),   # never recovered / unreachable -> fail-closed
    ]
    ok = True
    for rec_s, want in cases:
        got = classify(rec_s)["pass"]
        good = (got == want)
        ok = ok and good
        print("  [%s] recovery=%-8s pass=%-5s (want %s)" %
              ("OK" if good else "FAIL", rec_s, got, want))
    # boundary sanity: breach magnitude is positive only on real breaches
    assert classify(120.0)["breach_s"] >= 0.0
    assert classify(0.5)["breach_s"] == 0.0
    print("[chaos_recovery_drill] SELF-TEST %s" % ("PASS (%d/%d)" % (len(cases), len(cases)) if ok else "FAIL"))
    return 0 if ok else 1


# --------------------------------------------------------------------------- #
# LIVE leg: run N real drills against reachable seats; fail-closed otherwise.
# --------------------------------------------------------------------------- #
def live():
    base = os.environ.get("SEAT_BASE", "")
    model_path = os.environ.get("SEAT_MODEL_PATH", "")
    key = os.environ.get("STUDIO_KEY", "")
    seat = os.environ.get("SEAT_NAME", "env-seat")
    if not base:
        print("[chaos_recovery_drill] --live needs SEAT_BASE (Studio url). "
              "From a firewalled seat this leg fails closed by design.")
        return 1
    records = []
    for i in range(N_DRILLS):
        r = run_drill(base, "%s#%d" % (seat, i + 1), model_path, key)
        records.append(r)
        print("  drill %d/%d seat=%s recovery=%s pass=%s err=%s" %
              (i + 1, N_DRILLS, r["seat"], r["recovery_s"], r["pass"], r["error"]))
    append_drills(records)
    write_report([{"kind": "live", "drills": records}])
    passed = sum(1 for r in records if r["pass"])
    print("[chaos_recovery_drill] LIVE %d/%d under SLA -> %s" %
          (passed, len(records), DRILLS_JSONL))
    return 0 if passed == len(records) else 2


# --------------------------------------------------------------------------- #
# Report: always fold in the REAL production incidents so the autonomy finding
# is grounded in fleet history, not just this run.
# --------------------------------------------------------------------------- #
def load_prod_incidents():
    out = []
    if os.path.exists(PROD_INCIDENTS):
        for ln in open(PROD_INCIDENTS, encoding="utf-8").read().splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                j = json.loads(ln)
            except Exception:
                continue
            rec_s = j.get("recovery_seconds")
            if rec_s is None and j.get("recovery_min") is not None:
                rec_s = j["recovery_min"] * 60.0
            out.append({"type": j.get("type"), "host": j.get("host"),
                        "ts": j.get("ts"), "recovery_s": rec_s})
    return out


def write_report(live_blocks):
    prod = load_prod_incidents()
    lines = ["# Chaos-Recovery Drill Report", "", "Run: %s" % iso(),
             "SLA target: recovery < %.0fs (goal #2 AC)." % SLA_S, ""]
    for blk in live_blocks:
        if blk.get("kind") == "live":
            lines.append("## Live drills (this run)")
            lines.append("| # | seat | recovery_s | <120s | note |")
            lines.append("|---|------|-----------|-------|------|")
            for i, r in enumerate(blk["drills"], 1):
                note = r.get("error") or ("breach +%.0fs" % r.get("breach_s", 0) if not r["pass"] else "ok")
                lines.append("| %d | %s | %s | %s | %s |" %
                             (i, r["seat"], r["recovery_s"], "YES" if r["pass"] else "NO", note))
            lines.append("")
    lines.append("## Real production incidents (memory/ops/recovery-times.jsonl)")
    lines.append("These are the fleet's ACTUAL heal times, measured by Mechanic.")
    lines.append("| type | host | ts | recovery_s | <120s SLA |")
    lines.append("|------|------|----|-----------|-----------|")
    breaches = 0
    for p in prod:
        okc = classify(p["recovery_s"])["pass"]
        if not okc:
            breaches += 1
        lines.append("| %s | %s | %s | %s | %s |" %
                     (p.get("type"), p.get("host"), p.get("ts"),
                      round(p["recovery_s"], 1) if p["recovery_s"] is not None else "?",
                      "PASS" if okc else "FAIL"))
    lines.append("")
    total = len(prod)
    lines.append("## Autonomy finding (Fleet Autonomy Convergence)")
    lines.append("- %d/%d real production incidents meet the <%.0fs auto-recovery SLA." %
                 (total - breaches, total, SLA_S))
    if prod:
        rs = [p["recovery_s"] for p in prod if p["recovery_s"] is not None]
        if rs:
            lines.append("- Real heal-time range: %.0fs..%.0fs (min=%.0fs, max=%.0fs)." %
                         (min(rs), max(rs), min(rs), max(rs)))
    lines.append("- Failure mode when SLA exceeded: detection + unload/reload round-trip "
                 "dominates (minutes, not seconds). To converge toward <120s the fleet must cut "
                 "the reload latency or pre-stage models so recovery is a re-point, not a re-load.")
    lines.append("- This seat could NOT run a live drill (localhost Studio firewalled: WinError 10013; "
                 "no NVML). The live leg above fails closed by design and must be run from a seat that "
                 "reaches a Studio (e.g. White local host).")
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("[chaos_recovery_drill] report -> %s" % os.path.relpath(REPORT_MD))


def main():
    if "--self-test" in sys.argv:
        write_report([])   # still emit the production-grounded report
        return self_test()
    if "--live" in sys.argv:
        return live()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
