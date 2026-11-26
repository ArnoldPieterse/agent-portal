#!/usr/bin/env python3
"""
ssot_convergence_gate.py — SSOT Convergence Gate (Forge, contribution 2026-11-27)

Reconciles the two fleet goal-count SSOT files and FAILS if they drift beyond
tolerance. This is a recurring CI gate: it removes the "someone noticed the
dashboard disagrees" dependency by making the disagreement a hard exit code.

Files compared (defaults, overridable via --ledger / --next10):
  * goal_ledger.json          -> authoritative, EVIDENCE-GATED (a goal counts as
                                  reached only when its `verified:` marker exists)
  * memory/goals/next10.json  -> forecast engine output (counts goals it predicts
                                  done; can legitimately lead/lag the gate)

What it checks (per-lane + fleet):
  * total mismatch            (should always be 0; a structural drift = hard fail)
  * reached/done delta        (forecast may lead/lag; bounded by --tolerance)
  * pct drift                 (reported, not gated separately — derived from above)

Exit codes:
  0  CLEAN      within tolerance (total match + every lane |delta| <= tolerance)
  1  DRIFT      beyond tolerance (a real conformance gap to fix before deploy)
  2  BAD INPUT  missing/malformed file, or a lane present in only one source

House rule: --selftest proves the classifier is non-vacuous (clean / injected
drift / total-mismatch each classified + correct exit code). Deterministic.

Usage:
  python memory/forge/ssot_convergence_gate.py                # live gate
  python memory/forge/ssot_convergence_gate.py --tolerance 1  # allow 1-goal lag
  python memory/forge/ssot_convergence_gate.py --selftest     # prove non-vacuous
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]   # repo root (memory/forge/..) -> root
DEFAULT_LEDGER = ROOT / "goal_ledger.json"
DEFAULT_NEXT10 = ROOT / "memory" / "goals" / "next10.json"
REPORT_JSON = ROOT / "memory" / "ops" / "ssot-convergence-gate-report.json"

EXIT_CLEAN, EXIT_DRIFT, EXIT_BADINPUT = 0, 1, 2


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _lane_reached(agent_entry):
    """Evidence-gated reached count from a goal_ledger agent dict."""
    if not isinstance(agent_entry, dict):
        return None
    for k in ("reached", "reached_goals"):
        v = agent_entry.get(k)
        if isinstance(v, int):
            return v
    return None


def _lane_total(agent_entry):
    if not isinstance(agent_entry, dict):
        return None
    for k in ("total", "goals"):
        v = agent_entry.get(k)
        if isinstance(v, int):
            return v
    return None


def load_ledger(path):
    """Return {lane: {'total':int,'reached':int}} from the authoritative ledger."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    agents = data.get("agents") if isinstance(data, dict) else None
    if not isinstance(agents, dict):
        raise ValueError("goal_ledger.json: missing/invalid 'agents' object")
    out = {}
    for lane, entry in agents.items():
        tot, rec = _lane_total(entry), _lane_reached(entry)
        if tot is None or rec is None:
            raise ValueError(f"goal_ledger.json: lane '{lane}' missing total/reached")
        out[lane] = {"total": tot, "reached": rec}
    return out


def load_next10(path):
    """Return {lane: {'total':int,'done':int}} from the forecast engine output."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    lanes = data.get("lanes") if isinstance(data, dict) else None
    if not isinstance(lanes, dict):
        raise ValueError("next10.json: missing/invalid 'lanes' object")
    out = {}
    for lane, entry in lanes.items():
        if not isinstance(entry, dict):
            raise ValueError(f"next10.json: lane '{lane}' is not an object")
        tot, done = entry.get("total"), entry.get("done")
        if not isinstance(tot, int) or not isinstance(done, int):
            raise ValueError(f"next10.json: lane '{lane}' missing total/done ints")
        out[lane] = {"total": tot, "reached": done}
    return out


def reconcile(ledger_lanes, n10_lanes, tolerance=0):
    """Pure classifier. Returns a result dict; no I/O, deterministic."""
    lanes = sorted(set(ledger_lanes) | set(n10_lanes))
    per_lane = []
    total_mismatch = 0
    max_abs_delta = 0
    for lane in lanes:
        lg = ledger_lanes.get(lane)
        fc = n10_lanes.get(lane)
        if lg is None or fc is None:
            per_lane.append({"lane": lane, "status": "MISSING_IN_ONE_SOURCE",
                             "ledger": lg, "forecast": fc, "delta": None})
            total_mismatch += 1
            continue
        delta = fc["reached"] - lg["reached"]          # forecast minus authoritative
        tot_delta = fc["total"] - lg["total"]
        status = "CLEAN"
        if tot_delta != 0:
            status = "TOTAL_MISMATCH"
        elif abs(delta) > tolerance:
            status = "DRIFT"
        per_lane.append({
            "lane": lane,
            "ledger_reached": lg["reached"], "forecast_done": fc["reached"],
            "total_ledger": lg["total"], "total_forecast": fc["total"],
            "delta": delta, "total_delta": tot_delta, "status": status,
        })
        if tot_delta != 0:
            total_mismatch += 1
        max_abs_delta = max(max_abs_delta, abs(delta))

    fleet_ledger_reached = sum(v["reached"] for v in ledger_lanes.values())
    fleet_forecast_done = sum(v["reached"] for v in n10_lanes.values())
    fleet_total = sum(v["total"] for v in ledger_lanes.values())

    if total_mismatch > 0:
        overall = "BAD_INPUT"
    elif max_abs_delta > tolerance:
        overall = "DRIFT"
    else:
        overall = "CLEAN"

    return {
        "overall": overall,
        "exit_code": EXIT_BADINPUT if overall == "BAD_INPUT"
                     else (EXIT_DRIFT if overall == "DRIFT" else EXIT_CLEAN),
        "tolerance": tolerance,
        "fleet": {
            "total": fleet_total,
            "ledger_reached": fleet_ledger_reached,
            "forecast_done": fleet_forecast_done,
            "reached_delta": fleet_forecast_done - fleet_ledger_reached,
        },
        "max_abs_lane_delta": max_abs_delta,
        "lanes": per_lane,
    }


def run(ledger_path, next10_path, tolerance=0, write_report=True):
    try:
        ledger_lanes = load_ledger(ledger_path)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        return _fail(f"cannot read authoritative ledger {ledger_path}: {e}")
    try:
        n10_lanes = load_next10(next10_path)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        return _fail(f"cannot read forecast next10 {next10_path}: {e}")

    result = reconcile(ledger_lanes, n10_lanes, tolerance=tolerance)
    result["generated"] = _now()
    result["sources"] = {"ledger": str(ledger_path), "next10": str(next10_path)}
    if write_report:
        try:
            REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
            REPORT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")
            result["report"] = str(REPORT_JSON.relative_to(ROOT))
        except OSError as e:
            print(f"warn: could not write report: {e}", file=sys.stderr)
    return result


def _fail(msg):
    print(f"SSOT CONVERGENCE GATE — BAD INPUT (exit 2)\n  {msg}", file=sys.stderr)
    r = {"overall": "BAD_INPUT", "exit_code": EXIT_BADINPUT, "error": msg,
         "generated": _now()}
    return r


def print_report(r):
    if r.get("overall") == "BAD_INPUT":
        print(f"SSOT CONVERGENCE GATE — BAD INPUT (exit {r['exit_code']})")
        print(f"  {r.get('error')}")
        return
    f = r["fleet"]
    verdict = r["overall"]
    mark = {"CLEAN": "PASS", "DRIFT": "FAIL", "BAD_INPUT": "ERROR"}[verdict]
    print(f"SSOT CONVERGENCE GATE — {mark} (exit {r['exit_code']}, tolerance={r['tolerance']})")
    print(f"  fleet total={f['total']}  ledger_reached={f['ledger_reached']}  "
          f"forecast_done={f['forecast_done']}  reached_delta={f['reached_delta']:+d}")
    hdr = f"  {'lane':<14}{'ledger':>8}{'forecast':>10}{'delta':>7}  status"
    print(hdr)
    for ln in r["lanes"]:
        if ln["status"] == "MISSING_IN_ONE_SOURCE":
            print(f"  {ln['lane']:<14}{'-':>8}{'-':>10}{'?':>7}  MISSING_IN_ONE_SOURCE")
            continue
        flag = "" if ln["status"] == "CLEAN" else f"  <-- {ln['status']}"
        print(f"  {ln['lane']:<14}{ln['ledger_reached']:>8}{ln['forecast_done']:>10}"
              f"{ln['delta']:>+7}  {ln['status']}{flag}")
    if r.get("report"):
        print(f"  report -> {r['report']}")


def _selftest():
    """Prove the classifier is non-vacuous on synthetic pairs."""
    base_ledger = {
        "archivist": {"total": 10, "reached": 9},
        "forge":     {"total": 10, "reached": 9},
        "builder":   {"total": 10, "reached": 10},
    }
    # NOTE: reconcile() operates on NORMALIZED lane dicts {total, reached} from
    # both sides (load_next10 maps forecast 'done' -> 'reached'), so synthetic
    # forecast dicts use 'reached' too.
    # 1) CLEAN: forecast matches authoritative exactly
    clean_fc = {k: {"total": v["total"], "reached": v["reached"]}
                for k, v in base_ledger.items()}
    r1 = reconcile(base_ledger, clean_fc, tolerance=0)
    assert r1["overall"] == "CLEAN" and r1["exit_code"] == EXIT_CLEAN, r1

    # 2) DRIFT: forecast leads by 2 on two lanes (mirrors live archivist+forge case)
    drift_fc = {k: dict(v) for k, v in clean_fc.items()}
    drift_fc["archivist"]["reached"] = 10   # +1
    drift_fc["forge"]["reached"] = 10       # +1
    r2 = reconcile(base_ledger, drift_fc, tolerance=0)
    assert r2["overall"] == "DRIFT" and r2["exit_code"] == EXIT_DRIFT, r2
    assert r2["fleet"]["reached_delta"] == 2, r2
    # same drift is CLEAN under tolerance=2 (forecast lag within bound is acceptable)
    r2b = reconcile(base_ledger, drift_fc, tolerance=2)
    assert r2b["overall"] == "CLEAN", r2b

    # 3) TOTAL_MISMATCH: structural drift -> BAD_INPUT regardless of reached
    bad_fc = {k: dict(v) for k, v in clean_fc.items()}
    bad_fc["builder"]["total"] = 9      # total disagrees
    r3 = reconcile(base_ledger, bad_fc, tolerance=5)
    assert r3["overall"] == "BAD_INPUT" and r3["exit_code"] == EXIT_BADINPUT, r3

    # 4) lane present in only one source -> BAD_INPUT
    missing_fc = {k: dict(v) for k, v in clean_fc.items()}
    missing_fc.pop("forge")
    r4 = reconcile(base_ledger, missing_fc, tolerance=0)
    assert r4["overall"] == "BAD_INPUT", r4

    print("SSOT CONVERGENCE GATE --selftest: ALL PASS "
          "(clean / injected-drift->DRIFT / total-mismatch->BAD_INPUT / missing-lane->BAD_INPUT)")
    return EXIT_CLEAN


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    ap.add_argument("--next10", default=str(DEFAULT_NEXT10))
    ap.add_argument("--tolerance", type=int, default=0,
                    help="max allowed |forecast-done - ledger-reached| per lane (default 0 = strict)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return _selftest()
    r = run(args.ledger, args.next10, tolerance=args.tolerance, write_report=True)
    print_report(r)
    return r["exit_code"]


if __name__ == "__main__":
    sys.exit(main())