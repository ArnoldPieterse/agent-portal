"""Forge - Convergence Gate Metrics (goal #7).

Computes gate-specific autonomy metrics from Forge's own evidence logs and merges
them into memory/ops/autonomy-score.json under the "gate" key (non-destructive
read-modify-write; orchestrator/autonomy_score.py owns the base score, Forge owns
the "gate" sub-block). Also writes an SSOT copy to memory/ops/gate-metrics.json so
the block survives orchestrator re-runs (no clobber loop).

Metrics:
  deploys_autonomous_pct   % of deploys completed without human intervention
  smoke_first_try_pass_pct % of smoke host-checks that passed on the first probe
  mttd_minutes             mean time to detect a gate failure (occurred->detected)
  mttr_minutes             mean time to recover from a gate failure (detected->recovered)

Data sources:
  memory/forge/deploy-log.jsonl   (autonomous %, and rollback MTTD/MTTR pairs)
  memory/forge/smoke-results.jsonl(first-try pass %)
  memory/ops/incidents.jsonl      (occurred/detected/recovered triples)

Usage:
  python memory/forge/gate_metrics.py             # compute + merge into autonomy-score.json
  python memory/forge/gate_metrics.py --json      # print computed block only, write nothing
  python memory/forge/gate_metrics.py --selftest  # synthetic known-value proof, exit 0 on pass
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DEPLOY_LOG = ROOT / "memory" / "forge" / "deploy-log.jsonl"
SMOKE_LOG = ROOT / "memory" / "forge" / "smoke-results.jsonl"
INCIDENTS = ROOT / "memory" / "ops" / "incidents.jsonl"
GATE_SSCORE = ROOT / "memory" / "ops" / "autonomy-score.json"
GATE_SSOT = ROOT / "memory" / "ops" / "gate-metrics.json"

# Every canary-pipeline outcome is automated (no human step between canary and rollout).
AUTONOMOUS_STATUSES = {"success", "smoke_rollback", "perf_rollback", "promotion_partial"}
MANUAL_MARKERS = ("manual", "human")


def _parse_ts(value):
    """Parse ISO-Z, ISO-offset, or 'YYYY-MM-DD HH:MM:SS' into a UTC datetime, or None."""
    if not value:
        return None
    s = str(value).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        # space-separated local form used by deploy-log
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
            try:
                dt = datetime.strptime(s, fmt)
                break
            except ValueError:
                continue
        else:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _read_jsonl(path):
    out = []
    p = Path(path)
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _deploy_autonomous(entry):
    status = str(entry.get("status", ""))
    if entry.get("human_intervention") is True:
        return False
    if any(m in status.lower() for m in MANUAL_MARKERS):
        return False
    return status in AUTONOMOUS_STATUSES or status == ""  # unknown status => assume pipeline-automated


def _deploy_failure_events(entry):
    """Yield (occurred, detected, recovered) UTC datetimes for a rollback deploy entry."""
    status = str(entry.get("status", ""))
    if not status.endswith("rollback") and status != "promotion_partial":
        return
    ts = _parse_ts(entry.get("ts"))                 # rollback decision == detection time
    canary = _parse_ts(entry.get("canary_ts")) or _parse_ts(entry.get("occurred_at"))
    recovered = _parse_ts(entry.get("recovered_at")) or ts  # instant auto-rollback => 0 recovery
    if ts is None:
        return
    yield (canary, ts, recovered)


def compute_gate_metrics(deploy_log=DEPLOY_LOG, smoke_log=SMOKE_LOG, incidents=INCIDENTS):
    deploys = _read_jsonl(deploy_log)
    smokes = _read_jsonl(smoke_log)
    incs = _read_jsonl(incidents)

    # --- Metric 1: deploys autonomous % ---
    n_deploys = len(deploys)
    n_autonomous = sum(1 for d in deploys if _deploy_autonomous(d))
    deploys_autonomous_pct = round(100.0 * n_autonomous / n_deploys, 1) if n_deploys else None

    # --- Metric 2: smoke first-try pass % ---
    total_checks = 0
    first_try = 0
    for run in smokes:
        results = run.get("results")
        if not isinstance(results, list):
            continue
        for r in results:
            if not isinstance(r, dict):
                continue
            total_checks += 1
            # pre-remediation status == 'OK' means it passed on the very first probe
            if str(r.get("status", "")).upper() == "OK":
                first_try += 1
    smoke_first_try_pass_pct = round(100.0 * first_try / total_checks, 1) if total_checks else None

    # --- Metrics 3+4: MTTD / MTTR from failure-event triples ---
    detected_gaps = []   # detection - occurrence (minutes)
    recovery_gaps = []   # recovery - detection (minutes)

    def consume(occurred, detected, recovered):
        if occurred and detected:
            detected_gaps.append((detected - occurred).total_seconds() / 60.0)
        if detected and recovered:
            recovery_gaps.append((recovered - detected).total_seconds() / 60.0)

    for d in deploys:
        for ev in _deploy_failure_events(d):
            consume(*ev)
    for inc in incs:
        occurred = _parse_ts(inc.get("occurred_at"))
        detected = _parse_ts(inc.get("detected_at")) or _parse_ts(inc.get("timestamp"))
        recovered = _parse_ts(inc.get("recovered_at"))
        consume(occurred, detected, recovered)

    def mean(xs):
        return round(sum(xs) / len(xs), 2) if xs else None

    return {
        "deploys_total": n_deploys,
        "deploys_autonomous_pct": deploys_autonomous_pct,
        "smoke_host_checks": total_checks,
        "smoke_first_try_pass_pct": smoke_first_try_pass_pct,
        "mttd_minutes": mean(detected_gaps),
        "mttr_minutes": mean(recovery_gaps),
        "failure_events_detected": len(detected_gaps),
        "failure_events_recovered": len(recovery_gaps),
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "deploy_log": str(DEPLOY_LOG.relative_to(ROOT)),
            "smoke_log": str(SMOKE_LOG.relative_to(ROOT)),
            "incidents": str(INCIDENTS.relative_to(ROOT)),
        },
    }


def merge_into_autonomy_score(block, target=GATE_SSCORE):
    """Non-destructively set the 'gate' key on autonomy-score.json (read-modify-write)."""
    target = Path(target)
    data = {}
    if target.exists():
        try:
            data = json.loads(target.read_text(encoding="utf-8", errors="replace"))
        except json.JSONDecodeError:
            data = {}
    if not isinstance(data, dict):
        data = {}
    data["gate"] = block
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def run(write=True):
    block = compute_gate_metrics()
    if write:
        GATE_SSOT.parent.mkdir(parents=True, exist_ok=True)
        GATE_SSOT.write_text(json.dumps(block, indent=2), encoding="utf-8")
        merge_into_autonomy_score(block)
    return block


def selftest():
    """Synthetic known-value proof: 3 test deploys + 1 simulated failure => exact metrics."""
    import tempfile
    print("=== gate_metrics.py SELFTEST ===")
    tmp = Path(tempfile.mkdtemp(prefix="forge_gate_"))
    deploy = tmp / "deploy.jsonl"
    smoke = tmp / "smoke.jsonl"
    inc = tmp / "inc.jsonl"

    # 3 autonomous successes + 1 simulated perf_rollback (occurred->detected = 5min, detected->recovered = 2min)
    deploys = [
        {"ts": "2026-11-25 14:00:00", "file": "a", "status": "success", "promoted": ["Red"]},
        {"ts": "2026-11-25 14:10:00", "file": "b", "status": "success", "promoted": ["Red"]},
        {"ts": "2026-11-25 14:20:00", "file": "c", "status": "success", "promoted": ["Red"]},
        {"ts": "2026-11-25 14:35:00", "file": "d", "canary_ts": "2026-11-25 14:30:00",
         "status": "perf_rollback", "recovered_at": "2026-11-25 14:37:00"},
    ]
    deploy.write_text("\n".join(json.dumps(d) for d in deploys), encoding="utf-8")

    # one smoke run: 3 hosts OK first-try + 1 host CRIT (not first-try) => 75%
    smoke.write_text(json.dumps({"ts": "2026-11-25T14:00:00Z", "results": [
        {"host": "White", "status": "OK", "final_status": "OK"},
        {"host": "Red", "status": "OK", "final_status": "OK"},
        {"host": "Pale", "status": "OK", "final_status": "OK"},
        {"host": "Black", "status": "CRIT", "remediated": True, "final_status": "OK"},
    ]}), encoding="utf-8")

    inc.write_text("", encoding="utf-8")  # no incident triples; MTTD/MTTR come from the rollback

    m = compute_gate_metrics(deploy, smoke, inc)
    checks = [
        ("deploys_autonomous_pct == 100.0", m["deploys_autonomous_pct"] == 100.0),
        ("deploys_total == 4", m["deploys_total"] == 4),
        ("smoke_first_try_pass_pct == 75.0", m["smoke_first_try_pass_pct"] == 75.0),
        ("mttd_minutes == 5.0", m["mttd_minutes"] == 5.0),
        ("mttr_minutes == 2.0", m["mttr_minutes"] == 2.0),
    ]
    ok = True
    for label, passed in checks:
        print(f"  [{'PASS' if passed else 'FAIL'}] {label} (got deploys={m['deploys_autonomous_pct']}% smoke={m['smoke_first_try_pass_pct']}% mttd={m['mttd_minutes']} mttr={m['mttr_minutes']})")
        ok = ok and passed
    print(f"  SELFTEST: {'PASS' if ok else 'FAIL'}")
    return ok


def main():
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    block = run(write="--json" not in sys.argv)
    print(json.dumps(block, indent=2))


if __name__ == "__main__":
    main()
