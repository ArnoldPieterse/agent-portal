#!/usr/bin/env python3
"""Gate Heartbeat Monitor — detects stale gate runs.

Checks last-run timestamp of each Forge gate's .jsonl report (or evidence file mtime).
Stale threshold: 4 hours by default (--threshold to override).
Exit 0 = all fresh, 1 = stale detected, 2 = no data at all.

Part of Fleet Autonomy Convergence: gates that self-monitor rather than waiting for prompts.
"""
import pathlib, json, sys
from datetime import datetime, timezone

GATES = {
    "consistency_check": "memory/forge/consistency-report.jsonl",
    "drift_detect": "memory/forge/drift-report.jsonl",
    "runbook_audit": None,
    "convergence_trend": "memory/forge/convergence-trend-report.jsonl",
    "fleet_autonomy_gate": "memory/forge/fleet-autonomy-gate-report.jsonl",
}

DEFAULT_STALE_HOURS = 4.0


def last_jsonl_ts(path: str):
    p = pathlib.Path(path)
    if not p.exists():
        return None
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    for line in reversed(lines):
        try:
            obj = json.loads(line)
            for key in ("ts", "timestamp", "time", "run_at"):
                if key in obj:
                    val = obj[key]
                    if isinstance(val, (int, float)):
                        return datetime.fromtimestamp(val, tz=timezone.utc)
                    return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
        except Exception:
            continue
    return None


def last_mtime(path: str):
    p = pathlib.Path(path)
    if not p.exists():
        return None
    return datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)


def main():
    threshold = DEFAULT_STALE_HOURS
    json_mode = False
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--threshold" and i + 1 < len(args):
            threshold = float(args[i + 1])
        elif a == "--json":
            json_mode = True

    now = datetime.now(timezone.utc)
    results = []

    for name, jsonl_path in GATES.items():
        ts = None
        source = "jsonl"
        if jsonl_path:
            ts = last_jsonl_ts(jsonl_path)
        if ts is None and jsonl_path and pathlib.Path(jsonl_path).exists():
            ts = last_mtime(jsonl_path)
            source = "mtime"
        if ts is None and name == "runbook_audit":
            # prefer machine-readable stamp
            stamp = pathlib.Path("memory/forge/runbook-audit-last-run.json")
            if stamp.exists():
                try:
                    obj = json.loads(stamp.read_text(encoding="utf-8"))
                    ts = datetime.fromisoformat(obj["ts"])
                    source = "stamp"
                except Exception:
                    pass
            if ts is None:
                ev_dir = pathlib.Path("memory/forge")
                candidates = sorted(ev_dir.glob("evidence-runbook*"))
                if candidates:
                    ts = last_mtime(str(candidates[-1]))
                    source = "evidence-mtime"

        if ts is None:
            results.append({"gate": name, "status": "NO-DATA", "age_h": None})
        else:
            age_h = (now - ts).total_seconds() / 3600.0
            status = "FRESH" if age_h <= threshold else "STALE"
            results.append({
                "gate": name, "status": status,
                "age_h": round(age_h, 2),
                "ts": ts.isoformat(), "source": source,
            })

    stale_count = sum(1 for r in results if r["status"] == "STALE")
    no_data = sum(1 for r in results if r["status"] == "NO-DATA")
    verdict = "ALL-FRESH" if stale_count == 0 and no_data == 0 else (
        f"{stale_count} STALE, {no_data} NO-DATA" if no_data else f"{stale_count} STALE"
    )

    report = {
        "ts": now.isoformat(),
        "stale_threshold_h": threshold,
        "gates": results,
        "verdict": verdict,
    }

    hb_path = pathlib.Path("memory/forge/gate-heartbeat.jsonl")
    with hb_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(report) + "\n")

    if json_mode:
        print(json.dumps(report, indent=2))
    else:
        print(f"Gate Heartbeat ({now.strftime('%Y-%m-%d %H:%M UTC')})")
        print(f"  Threshold: {threshold}h")
        for r in results:
            icon = "✓" if r["status"] == "FRESH" else ("✗" if r["status"] == "STALE" else "?")
            age = f"{r['age_h']}h" if r.get("age_h") is not None else "N/A"
            print(f"  {icon} {r['gate']:<24s} {r['status']:<8s} age={age}")
        print(f"  VERDICT: {verdict}")

    if no_data > 0 and stale_count == 0:
        sys.exit(2)
    sys.exit(0 if stale_count == 0 else 1)


if __name__ == "__main__":
    main()
