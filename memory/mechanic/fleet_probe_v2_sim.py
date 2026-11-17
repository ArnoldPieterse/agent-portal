#!/usr/bin/env python3
"""fleet_probe_v2_sim.py - degrading-host simulation (Mechanic goal #1 evidence).

Acceptance test for goal #1: "simulating a degrading host -> severity escalates
over N runs." This harness feeds a synthetic host through consecutive probe runs
with (a) rising latency and (b) a leaking process count, using the REAL
classify_latency / classify_proc + rolling-baseline logic from fleet_probe_v2.py.
No network, no writes to production history - fully sandbox-safe.

Writes evidence to memory/mechanic/fleet_probe_v2_sim_evidence.jsonl.
Run: python memory/mechanic/fleet_probe_v2_sim.py
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from fleet_probe_v2 import (classify_latency, classify_proc, baseline_latency,
                            baseline_proc_count, HISTORY_WINDOW)

EVIDENCE = os.path.join(os.path.dirname(__file__), "fleet_probe_v2_sim_evidence.jsonl")
IP, PORT = "IP_BLACK", 8099

# Run-by-run synthetic samples: latency climbs ~ +40%/run; proc count leaks ~+35%/run.
LATENCY = [10.0, 14.0, 19.6, 27.4, 38.4, 53.8]   # ms
PROCS   = [100, 135, 182, 246, 332, 448]

def run_sim():
    history = []          # per host:port records for latency baseline
    proc_hist = []        # proc_count entries for proc baseline
    rows = []
    for i in range(len(LATENCY)):
        lat, pc = LATENCY[i], PROCS[i]
        base_lat = baseline_latency(history, IP, PORT)
        lsev, ldrift = classify_latency(lat, base_lat)
        pbase = baseline_proc_count(proc_hist[-HISTORY_WINDOW:])
        psev, pdrift = classify_proc(pc, pbase)
        # overall = worst of the two signals
        order = {"OK": 0, "WARN": 1, "CRIT": 2}
        overall = lsev if order[lsev] >= order[psev] else psev
        rows.append({"run": i + 1, "latency_ms": lat, "lat_baseline": base_lat,
                     "lat_sev": lsev, "proc_count": pc, "proc_baseline": pbase,
                     "proc_sev": psev, "overall": overall})
        # append to in-memory history for the next run's baseline
        history.append({"ip": IP, "port": PORT, "status": "OPEN", "latency_ms": lat})
        proc_hist.append({"proc_count": pc})
    return rows

def main():
    rows = run_sim()
    print(f"{'run':>3} {'lat_ms':>7} {'lat_base':>9} {'lat_sev':>8} "
          f"{'procs':>6} {'proc_base':>10} {'proc_sev':>9}  overall")
    for r in rows:
        lb = f"{r['lat_baseline']:.1f}" if r["lat_baseline"] is not None else "-"
        pb = f"{r['proc_baseline']:.0f}" if r["proc_baseline"] is not None else "-"
        print(f"{r['run']:>3} {r['latency_ms']:>7.1f} {lb:>9} {r['lat_sev']:>8} "
              f"{r['proc_count']:>6} {pb:>10} {r['proc_sev']:>9}  {r['overall']}")
    # Assert the acceptance property: severity escalates over the run sequence.
    order = {"OK": 0, "WARN": 1, "CRIT": 2}
    seq = [order[r["overall"]] for r in rows]
    non_decreasing = all(seq[i] <= seq[i + 1] for i in range(len(seq) - 1))
    reaches_crit = seq[-1] == order["CRIT"]
    ok = non_decreasing and reaches_crit
    print("\nescalation non-decreasing:", non_decreasing,
          "| final overall CRIT:", reaches_crit, "| PASS:", ok)
    with open(EVIDENCE, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    print("evidence ->", os.path.relpath(EVIDENCE))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
