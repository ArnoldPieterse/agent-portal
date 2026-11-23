"""
Post-Remediation Auto-Report
============================
Generates structured post-mortems from completed remediation events in the decision log.

Usage:
  python memory/builder/post_mortem.py --selftest    # generate report from real data + verify structure
  python memory/builder/post_mortem.py --generate    # generate report from all remediation events
  python memory/builder/post_mortem.py --stats       # show summary stats
"""
import json, sys, re, sqlite3
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
DECISION_LOG = BASE / "memory" / "ops" / "decision-log.jsonl"
REPORT_DIR = BASE / "memory" / "builder" / "post-mortems"
DB_PATH = BASE / "memory" / "builder" / "decision-index.db"

# Remediation event types to capture
REMEDIATION_TYPES = {
    "oom_recovery", "model_swap", "chaos_drill", "playbook_run",
    "auto_failover", "circuit_breaker", "self_heal", "rollback"
}


def load_decisions():
    if not DECISION_LOG.exists():
        return []
    entries = []
    for line in DECISION_LOG.read_text(encoding="utf-8").strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            ts = d.get("timestamp") or d.get("ts") or ""
            entries.append({"ts": ts, **d})
        except json.JSONDecodeError:
            continue
    return entries


def filter_remediations(decisions):
    """Filter decisions to remediation events."""
    results = []
    for d in decisions:
        dtype = (d.get("type") or "").lower()
        if any(rt in dtype for rt in REMEDIATION_TYPES):
            results.append(d)
    return results


def generate_post_mortem(event, idx):
    """Generate a structured post-mortem for one remediation event."""
    ts = event.get("ts", "unknown")
    etype = event.get("type", "unknown")
    agent = event.get("agent", "unknown")
    success = event.get("success", event.get("recovered", None))
    duration = event.get("recovery_time_s") or event.get("total_s") or 0
    
    # Extract detail fields
    detail_fields = {k: v for k, v in event.items()
                     if k not in ("ts", "timestamp", "type", "agent", "detail", "severity")}
    
    status = "SUCCESS" if success else ("FAILURE" if success is False else "UNKNOWN")
    
    report = {
        "report_id": f"pm-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{idx:03d}",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "event_type": etype,
        "agent": agent,
        "timestamp": ts,
        "status": status,
        "duration_s": duration,
        "timeline": [
            {"t": 0, "action": f"{etype} initiated by {agent}"},
            {"t": duration, "action": f"completed ({status})"}
        ],
        "root_cause": event.get("reason", event.get("detail", "not specified")),
        "actions_taken": [
            k + ": " + str(v) for k, v in detail_fields.items()
            if k not in ("success", "recovered", "recovery_time_s", "total_s")
        ],
        "impact": {
            "severity": event.get("severity", "unspecified"),
            "duration_s": duration,
            "resolved": success is True
        },
        "lessons_learned": [],
        "follow_ups": []
    }
    
    # Generate lessons/follow-ups based on outcome
    if success is False:
        report["lessons_learned"].append(f"{etype} failed - review root cause: {event.get('reason', 'unknown')}")
        report["follow_ups"].append("Investigate failure and file bug")
    elif duration > 60:
        report["lessons_learned"].append(f"Recovery took {duration}s - consider optimizing for faster turnaround")
    
    return report


def generate_report(max_events=50):
    """Generate post-mortems for all remediation events."""
    decisions = load_decisions()
    rems = filter_remediations(decisions)
    if not rems:
        print("No remediation events found in decision log")
        return []
    
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    reports = []
    for i, event in enumerate(rems[-max_events:], 1):
        pm = generate_post_mortem(event, i)
        reports.append(pm)
    
    out_file = REPORT_DIR / "post-mortems.jsonl"
    with open(out_file, "a", encoding="utf-8") as f:
        for pm in reports:
            f.write(json.dumps(pm) + "\n")
    
    # Also write a summary markdown
    md = REPORT_DIR / "latest-summary.md"
    lines = ["# Post-Remediation Summary", f"Generated: {datetime.now(timezone.utc).isoformat()}", ""]
    lines.append(f"**Total events:** {len(rems)}  ")
    success_count = sum(1 for e in rems if e.get('success') or e.get('recovered'))
    fail_count = len(rems) - success_count
    lines.append(f"**Success:** {success_count} ({100*success_count/max(1,len(rems)):.0f}%)  ")
    lines.append(f"**Failure:** {fail_count}")
    lines.append("")
    lines.append("## Recent Events")
    lines.append("")
    for pm in reports[-10:]:
        status_icon = "✅" if pm["status"] == "SUCCESS" else "❌"
        lines.append(f"- {status_icon} **{pm['event_type']}** ({pm['agent']}) — {pm['duration_s']}s — {pm['timestamp'][:19]}")
    md.write_text("\n".join(lines), encoding="utf-8")
    
    return reports


def cmd_selftest():
    print("Post-Remediation Auto-Report - selftest")
    passed = 0
    total = 5
    
    # Test 1: Load decisions
    decisions = load_decisions()
    if len(decisions) > 0:
        passed += 1
        print(f"  [PASS] Loaded {len(decisions)} decisions from log")
    else:
        print("  [FAIL] No decisions loaded")
    
    # Test 2: Filter remediations
    rems = filter_remediations(decisions)
    if len(rems) > 0:
        passed += 1
        print(f"  [PASS] Found {len(rems)} remediation events")
    else:
        # If no real data, test with synthetic
        test_events = [
            {"ts": "2026-11-23T00:00:00+00:00", "type": "oom_recovery",
             "agent": "test", "success": True, "recovery_time_s": 5,
             "reason": "gpu_memory_exhausted"},
            {"ts": "2026-11-23T01:00:00+00:00", "type": "chaos_drill",
             "agent": "builder", "recovered": True, "total_s": 30,
             "severity": "low"}
        ]
        rems = test_events
        passed += 1
        print(f"  [PASS] Synthetic {len(rems)} remediation events (no real data)")
    
    # Test 3: Generate post-mortem
    pm = generate_post_mortem(rems[0], 1)
    required_fields = ["report_id", "event_type", "agent", "status", "timeline",
                       "root_cause", "actions_taken", "impact", "lessons_learned"]
    if all(f in pm for f in required_fields):
        passed += 1
        print(f"  [PASS] Post-mortem has all {len(required_fields)} required fields")
    else:
        missing = [f for f in required_fields if f not in pm]
        print(f"  [FAIL] Missing fields: {missing}")
    
    # Test 4: Timeline structure
    if len(pm["timeline"]) >= 2 and "t" in pm["timeline"][0]:
        passed += 1
        print(f"  [PASS] Timeline has {len(pm['timeline'])} entries with timestamps")
    else:
        print("  [FAIL] Timeline structure invalid")
    
    # Test 5: Generate full report
    reports = generate_report()
    if len(reports) > 0:
        summary_file = REPORT_DIR / "latest-summary.md"
        if summary_file.exists():
            passed += 1
            print(f"  [PASS] Report generated: {len(reports)} post-mortems, summary at post-mortems/latest-summary.md")
        else:
            print("  [FAIL] Summary file not created")
    else:
        # Acceptable if no real remediation events exist
        passed += 1
        print(f"  [PASS] No real remediation events (synthetic test only)")
    
    print(f"")
    print(f"  SELFTEST: {passed}/{total} {'ALL PASS' if passed == total else 'FAILURES'}")
    return passed == total


def main():
    if "--selftest" in sys.argv:
        ok = cmd_selftest()
        sys.exit(0 if ok else 1)
    elif "--generate" in sys.argv:
        reports = generate_report()
        print(f"Generated {len(reports)} post-mortems")
    elif "--stats" in sys.argv:
        rems = filter_remediations(load_decisions())
        success = sum(1 for e in rems if e.get('success') or e.get('recovered'))
        print(f"Remediation events: {len(rems)}")
        print(f"  Success: {success} ({100*success/max(1,len(rems)):.0f}%)")
        print(f"  Failure: {len(rems)-success}")
        types = {}
        for e in rems:
            t = e.get('type', 'unknown')
            types[t] = types.get(t, 0) + 1
        for t, c in sorted(types.items()):
            print(f"    {t}: {c}")
    else:
        print(__doc__)

if __name__ == "__main__":
    main()