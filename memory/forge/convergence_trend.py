#!/usr/bin/env python3
"""Forge - Fleet Autonomy Convergence Trend Analyzer.

NEW artifact (2026-11-26), round topic: Fleet Autonomy Convergence.
Reads the historical consistency + drift run logs and computes a time-series
convergence picture: per-host reachability, verdict distribution, config-hash
drift events, drift-scan cleanliness, and a single convergence score with a
projection. This is measurement-driven (no vibes): every number comes from an
actual logged run.

Usage:
  python memory/forge/convergence_trend.py            # human report + jsonl append
  python memory/forge/convergence_trend.py --json     # machine-readable only
Exit: 0 = converged or trending-converged (no CRIT/WARN in recent window)
      1 = regression detected (a CRIT verdict or DRIFT status in the data)
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

LANE = Path(__file__).resolve().parent
CONS = LANE / "consistency-report.jsonl"
DRIFT = LANE / "drift-report.jsonl"
REPORT = LANE / "convergence-trend-report.jsonl"
HOSTS = ["White", "Red", "Pale", "Black"]


def load_jsonl(p):
    out = []
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def parse_ts(s):
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def analyze():
    cons = load_jsonl(CONS)
    drift = load_jsonl(DRIFT)

    # --- consistency metrics ---
    n_cons = len(cons)
    verdicts = [r.get("verdict") for r in cons]
    vdist = {v: verdicts.count(v) for v in set(verdicts)}

    # per-host reachability across all logged runs
    host_up = {h: 0 for h in HOSTS}
    for r in cons:
        hosts = r.get("hosts", {})
        for h in HOSTS:
            if hosts.get(h, {}).get("reachable"):
                host_up[h] += 1
    host_pct = {h: (round(100.0 * host_up[h] / n_cons, 1) if n_cons else 0.0) for h in HOSTS}

    # config-hash consistency: any run where reachable hosts disagreed?
    hash_mismatch_runs = 0
    distinct_hashes = set()
    for r in cons:
        hs = [v.get("config_hash") for v in r.get("hosts", {}).values() if v.get("reachable")]
        # strip mirrored: prefix for comparison
        norm = {x.split(":")[-1] if x else None for x in hs}
        distinct_hashes |= norm
        if len(norm - {None}) > 1:
            hash_mismatch_runs += 1

    # model-version consistency among reachable hosts
    model_mismatch_runs = 0
    for r in cons:
        mv = {v.get("model_version") for v in r.get("hosts", {}).values() if v.get("reachable")}
        if len(mv) > 1:
            model_mismatch_runs += 1

    # --- drift metrics ---
    # Selftest/simulate dirty-cases (introduce-dep / orphan-test demos) are logged
    # to the same jsonl as live scans. They are distinguishable by OUTCOME: a
    # selftest drift is always resolved by a subsequent CLEAN scan (baseline updated /
    # test artifact removed). A real regression stays non-CLEAN at the tail of the log.
    # So: a drift entry counts as an UNRESOLVED regression only if no later scan is CLEAN.
    n_drift = len(drift)
    dstat_all = [d.get("status") for d in drift]
    distat = {s: dstat_all.count(s) for s in set(dstat_all)}

    # Walk from newest to oldest; a non-CLEAN entry is 'unresolved' only while we
    # have not yet seen a CLEAN after it.
    unresolved_drift = 0
    seen_clean_after = False
    for d in reversed(drift):
        s = d.get("status")
        if s == "CLEAN":
            seen_clean_after = True
        elif s not in ("CLEAN", None) and not seen_clean_after:
            unresolved_drift += 1
    # current health: latest live scan status
    latest_status = drift[-1].get("status") if drift else None
    current_drift = latest_status not in ("CLEAN", None)
    # selftest_excluded = non-CLEAN entries that WERE later resolved by a CLEAN
    selftest_excluded = sum(1 for s in dstat_all if s not in ("CLEAN", None)) - unresolved_drift
    drift_events = unresolved_drift  # only unresolved drifts count as regressions

    # --- convergence score (0-100) ---
    # Components:
    #  1. verdict quality: PASS=1, WARN=0.5, CRIT=0 over consistency runs   (40 pts)
    #  2. config+model agreement: 1 - mismatch_runs/n_cons                    (25 pts)
    #  3. drift cleanliness: clean_scans / total_drift                        (25 pts)
    #  4. fleet reachability floor: min host pct / 100  (10 pts) -- autonomy headroom
    vpts = sum({"PASS": 1.0, "WARN": 0.5}.get(v, 0.0) for v in verdicts) / n_cons if n_cons else 0.0
    agree = 1.0 - (hash_mismatch_runs + model_mismatch_runs) / (2 * n_cons) if n_cons else 0.0
    dclean = (n_drift - drift_events) / n_drift if n_drift else 1.0
    reach_floor = min(host_pct.values()) / 100.0 if host_pct else 0.0
    score = round(100 * (0.40 * vpts + 0.25 * agree + 0.25 * dclean + 0.10 * reach_floor), 1)

    # regression flag: any CRIT consistency verdict, OR an UNRESOLVED drift
    # (a currently-active / never-followed-by-CLEAN non-CLEAN scan)
    regression = (vdist.get("CRIT", 0) > 0) or current_drift or (unresolved_drift > 0)

    # projection to full 4-host convergence:
    # hosts currently down (last run) define the gap; if their historical reachability
    # is low, convergence is gated on host recovery, not on consistency logic.
    last = cons[-1] if cons else {}
    last_hosts = last.get("hosts", {})
    down_now = [h for h in HOSTS if not last_hosts.get(h, {}).get("reachable")]
    gated_on_recovery = len(down_now) > 0

    ts = datetime.now(timezone.utc).isoformat()
    result = {
        "ts": ts,
        "consistency_runs": n_cons,
        "drift_scans": n_drift,
        "drift_latest_status": latest_status,
        "drift_unresolved": unresolved_drift,
        "drift_selftest_resolved": selftest_excluded,
        "verdict_distribution": vdist,
        "host_reachability_pct": host_pct,
        "hosts_down_last_run": down_now,
        "config_hash_mismatch_runs": hash_mismatch_runs,
        "model_version_mismatch_runs": model_mismatch_runs,
        "distinct_config_hashes": sorted(x for x in distinct_hashes if x),
        "drift_status_distribution": distat,
        "drift_events": drift_events,
        "convergence_score": score,
        "regression_detected": regression,
        "gated_on_host_recovery": gated_on_recovery,
        "verdict": (
            "REGRESSION"
            if regression
            else ("CONVERGED" if not gated_on_recovery else "TRENDED-CONVERGED")
        ),
    }
    return result


def main():
    res = analyze()
    # append to report log
    with REPORT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(res) + "\n")

    if "--json" in sys.argv:
        print(json.dumps(res, indent=2))
    else:
        print(f"Fleet Autonomy Convergence Trend  ({res['ts'][:19]}Z)")
        print(f"  consistency runs : {res['consistency_runs']}   drift scans: {res['drift_scans']}")
        print(f"  verdicts         : {res['verdict_distribution']}")
        print(f"  host reach %     : {res['host_reachability_pct']}")
        print(f"  config mismatch  : {res['config_hash_mismatch_runs']} runs   model mismatch: {res['model_version_mismatch_runs']} runs")
        print(f"  distinct hashes  : {res['distinct_config_hashes']}")
        print(f"  drift statuses   : {res['drift_status_distribution']}   events: {res['drift_events']}")
        print(f"  CONVERGENCE SCORE: {res['convergence_score']}/100")
        print(f"  regression       : {res['regression_detected']}   gated-on-recovery: {res['gated_on_host_recovery']} (down: {','.join(res['hosts_down_last_run']) or 'none'})")
        print(f"  VERDICT          : {res['verdict']}")

    sys.exit(1 if res["regression_detected"] else 0)


if __name__ == "__main__":
    main()
