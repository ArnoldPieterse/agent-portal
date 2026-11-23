#!/usr/bin/env python3
"""instrument_health.py - Research-Instrument Health Feed (Researcher goal #6)

Emits a cockpit data feed reporting the health of research instruments:
  - last-run time (from log artifacts or file mtime)
  - coverage (what it monitors)
  - current FP rate (if measurable from recent output)
  - last alert / status
  - staleness flag (not run in >2 cycles ~ 24h)

AC: one JSON record per instrument with last_run + status; flags any
    instrument not run in >2 cycles.

Usage:
  python memory/researcher/instrument_health.py            # emit to stdout + artifact
  python memory/researcher/instrument_health.py --json     # JSON only
"""
import json, os, sys, datetime, glob

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

NOW = datetime.datetime.now()
CYCLE_WINDOW_HOURS = 24  # >2 cycles ~ >24h

# Instrument definitions: name -> {script, log_artifact, coverage}
INSTRUMENTS = [
    {
        "name": "stale_claim_scan",
        "script": "memory/ops/stale_claim_check.py",
        "log_artifact": "memory/researcher/remediation-bus-log.jsonl",
        "coverage": "all memory/**.md claims of artifact existence",
    },
    {
        "name": "dispatch_desync",
        "script": "memory/ops/autoloop.json",
        "log_artifact": "memory/ops/dispatch-desync-log.md",
        "coverage": "autoloop.json vs actual goal-file open counts",
    },
    {
        "name": "reach_matrix",
        "script": "memory/researcher/remediation_bus.py",
        "log_artifact": "memory/researcher/reach-matrix.json",
        "coverage": "all agent goal files (8 seats)",
    },
    {
        "name": "clobber_manifest",
        "script": "memory/ops/clobber-events.jsonl",
        "log_artifact": "memory/researcher/clobber-manifest-summary.md",
        "coverage": "pin/sync clobber events in last 24h",
    },
    {
        "name": "goal_critical_path",
        "script": "memory/researcher/goal_critical_path.py",
        "log_artifact": "memory/researcher/goal-critical-path.json",
        "coverage": "cross-lane handoffs + goal files dependency graph",
    },
    {
        "name": "calib_dispatch",
        "script": "memory/researcher/calib_dispatch.py",
        "log_artifact": "memory/researcher/calib-dispatch-output.json",
        "coverage": "forecast accuracy vs actual goal completion",
    },
    {
        "name": "evidence_quality_trend",
        "script": "memory/researcher/evidence_quality_trend.py",
        "log_artifact": "memory/researcher/evidence-quality-trend-2026-11-17.md",
        "coverage": "evidence leaf quality scores over time",
    },
    {
        "name": "knowledge_decay",
        "script": "memory/researcher/knowledge_decay.py",
        "log_artifact": "memory/researcher/knowledge-decay-cycle10.md",
        "coverage": "KB entry staleness + orphan detection",
    },
    {
        "name": "sla_tracker",
        "script": "memory/researcher/sla_tracker.py",
        "log_artifact": "memory/researcher/sla-report-cycle6.md",
        "coverage": "per-goal SLA adherence across cycles",
    },
    {
        "name": "blocker_triage",
        "script": "memory/researcher/blocker_triage.py",
        "log_artifact": "memory/researcher/blocker-triage-fresh-run-2026-11-22.md",
        "coverage": "OPS-NOTE classification + recurrence detection",
    },
]


def get_last_run_time(instrument):
    """Determine last run time from log artifact or script mtime."""
    # First check the log/artifact file
    artifact = instrument["log_artifact"]
    if os.path.exists(artifact):
        mtime = os.path.getmtime(artifact)
        dt = datetime.datetime.fromtimestamp(mtime)
        return dt, "artifact_mtime"
    
    # Fall back to script mtime (weaker signal: file was edited but may not have run)
    script = instrument["script"]
    if os.path.exists(script):
        mtime = os.path.getmtime(script)
        dt = datetime.datetime.fromtimestamp(mtime)
        return dt, "script_mtime"
    
    return None, "no_artifact"


def compute_status(instrument):
    """Compute health status for one instrument."""
    last_run, source = get_last_run_time(instrument)
    
    if last_run is None:
        return {
            "name": instrument["name"],
            "status": "never_run",
            "last_run": None,
            "source": "no_artifact",
            "coverage": instrument["coverage"],
            "stale": True,
            "fp_rate": None,
            "last_alert": None,
        }
    
    age_hours = (NOW - last_run).total_seconds() / 3600
    stale = age_hours > CYCLE_WINDOW_HOURS
    
    status = "healthy" if not stale else "stale"
    
    return {
        "name": instrument["name"],
        "status": status,
        "last_run": last_run.strftime("%Y-%m-%dT%H:%M:%S"),
        "age_hours": round(age_hours, 1),
        "source": source,
        "coverage": instrument["coverage"],
        "stale": stale,
        "fp_rate": None,  # would need per-instrument FP tracking; not yet available
        "last_alert": None,
    }


def main():
    json_only = "--json" in sys.argv
    
    records = [compute_status(inst) for inst in INSTRUMENTS]
    stale_count = sum(1 for r in records if r["stale"])
    healthy_count = sum(1 for r in records if not r["stale"])
    
    output = {
        "generated": NOW.strftime("%Y-%m-%dT%H:%M:%S"),
        "cycle_window_hours": CYCLE_WINDOW_HOURS,
        "total_instruments": len(records),
        "healthy": healthy_count,
        "stale": stale_count,
        "instruments": records,
    }
    
    # Write artifact
    out_path = os.path.join("memory", "researcher", "instrument-health.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    
    if json_only:
        print(json.dumps(output, indent=2))
    else:
        print("=" * 60)
        print(f"  RESEARCH INSTRUMENT HEALTH FEED - {NOW.strftime('%Y-%m-%dT%H:%M:%S')}")
        print("=" * 60)
        print(f"  Total: {len(records)} | Healthy: {healthy_count} | Stale: {stale_count}")
        print()
        for r in records:
            flag = " [STALE]" if r["stale"] else ""
            age = f"{r.get('age_hours', '?')}h ago" if r['last_run'] else "never"
            print(f"  {r['name']:30s} {r['status']:10s} last={age}{flag}")
        print(f"\n  Artifact: {out_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
