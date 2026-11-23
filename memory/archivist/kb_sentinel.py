#!/usr/bin/env python3
"""KB Regression Sentinel (archivist goal 8).

Scheduled check that raises an alert leaf if:
- Total fact count drops >X% vs previous snapshot
- A critical node's in-degree changes
- A previously-resolved contradiction reappears

Alerts are deduped (no repeat for same condition). Report at memory/archivist/kb-sentinel-<date>.md.

Usage:
  python memory/archivist/kb_sentinel.py --check      # run sentinel check
  python memory/archivist/kb_sentinel.py --selftest   # run selftest
"""
import json, sys, hashlib
from datetime import datetime, timezone
from pathlib import Path

MEMORY = Path("memory")
ARCHIVIST = MEMORY / "archivist"
STATE_FILE = ARCHIVIST / ".kb_sentinel_state.json"
KNOWLEDGE_INDEX = ARCHIVIST / "knowledge-index.json"
CONFLICT_REPORT = ARCHIVIST / "conflict-resolver-report.json"

FACT_DROP_THRESHOLD = 0.10  # alert if fact count drops >10%
CRITICAL_IN_DEGREE = 5      # nodes with in-degree >= this are critical


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding='utf-8'))
    return {"last_fact_count": None, "critical_nodes": {}, "resolved_conflicts": [], "alerts_issued": []}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding='utf-8')


def get_fact_count() -> int:
    if not KNOWLEDGE_INDEX.exists():
        return 0
    data = json.loads(KNOWLEDGE_INDEX.read_text(encoding='utf-8'))
    facts = data.get("facts", data if isinstance(data, list) else [])
    return len(facts)


def get_critical_nodes() -> dict:
    """Compute in-degree from knowledge graph if available."""
    graph_file = ARCHIVIST / "knowledge-deps.json"
    if not graph_file.exists():
        return {}
    try:
        data = json.loads(graph_file.read_text(encoding='utf-8'))
        edges = data.get("edges", [])
        in_degree = {}
        for e in edges:
            target = e.get("target", "")
            in_degree[target] = in_degree.get(target, 0) + 1
        return {k: v for k, v in in_degree.items() if v >= CRITICAL_IN_DEGREE}
    except Exception:
        return {}


def get_active_conflicts() -> list:
    """Get currently active (unresolved) conflicts."""
    if not CONFLICT_REPORT.exists():
        return []
    try:
        data = json.loads(CONFLICT_REPORT.read_text(encoding='utf-8'))
        conflicts = data.get("conflicts", [])
        return [c.get("subject", "") for c in conflicts if not c.get("resolved", False)]
    except Exception:
        return []


def run_check() -> dict:
    """Run the sentinel check, return report dict."""
    state = load_state()
    alerts = []

    # Check 1: Fact count drop
    current_facts = get_fact_count()
    if state["last_fact_count"] is not None and state["last_fact_count"] > 0:
        drop_ratio = (state["last_fact_count"] - current_facts) / state["last_fact_count"]
        if drop_ratio > FACT_DROP_THRESHOLD:
            alert_key = f"fact_drop_{drop_ratio:.2f}"
            alerts.append({
                "type": "FACT_COUNT_DROP",
                "severity": "HIGH",
                "detail": f"Fact count dropped from {state['last_fact_count']} to {current_facts} ({drop_ratio*100:.1f}% drop)",
                "key": alert_key
            })

    # Check 2: Critical node in-degree changes
    current_critical = get_critical_nodes()
    for node, degree in state["critical_nodes"].items():
        if node not in current_critical:
            alerts.append({
                "type": "CRITICAL_NODE_LOST",
                "severity": "MEDIUM",
                "detail": f"Critical node '{node}' (was in-degree {degree}) no longer meets threshold",
                "key": f"critical_lost_{node}"
            })
        elif current_critical[node] != degree:
            alerts.append({
                "type": "CRITICAL_NODE_DEGREE_CHANGE",
                "severity": "MEDIUM",
                "detail": f"Critical node '{node}' in-degree changed: {degree} -> {current_critical[node]}",
                "key": f"critical_degree_{node}_{current_critical[node]}"
            })

    # Check 3: Previously-resolved conflict reappeared
    active_conflicts = get_active_conflicts()
    for subject in state["resolved_conflicts"]:
        if subject in active_conflicts:
            alerts.append({
                "type": "CONFLICT_REGRESSED",
                "severity": "HIGH",
                "detail": f"Previously-resolved conflict on '{subject}' has reappeared",
                "key": f"conflict_regression_{subject}"
            })

    # Dedup: filter out alerts already issued
    existing_keys = set(state["alerts_issued"])
    new_alerts = [a for a in alerts if a["key"] not in existing_keys]

    # Update state
    state["last_fact_count"] = current_facts
    state["critical_nodes"] = current_critical
    # Add newly-resolved conflicts to resolved list
    prev_active = set(state.get("last_active_conflicts", []))
    curr_active = set(active_conflicts)
    newly_resolved = prev_active - curr_active
    state["resolved_conflicts"] = list(set(state["resolved_conflicts"]) | newly_resolved)
    state["last_active_conflicts"] = active_conflicts
    # Record issued alerts
    state["alerts_issued"] = list(existing_keys | {a["key"] for a in new_alerts})
    save_state(state)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fact_count": current_facts,
        "critical_nodes": len(current_critical),
        "active_conflicts": len(active_conflicts),
        "alerts_total": len(alerts),
        "new_alerts": new_alerts,
        "status": "ALERT" if new_alerts else "OK"
    }

    # Write report file
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report_path = ARCHIVIST / f"kb-sentinel-{date_str}.md"
    lines = [f"# KB Sentinel Report {date_str}", "", f"Status: **{report['status']}**", ""]
    lines.append(f"- Fact count: {current_facts}")
    lines.append(f"- Critical nodes: {len(current_critical)}")
    lines.append(f"- Active conflicts: {len(active_conflicts)}")
    lines.append(f"- New alerts: {len(new_alerts)}")
    if new_alerts:
        lines.append("")
        lines.append("## Alerts")
        for a in new_alerts:
            lines.append(f"- [{a['severity']}] {a['type']}: {a['detail']}")
    report_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    report["report_path"] = str(report_path)

    return report


def run_selftest() -> bool:
    """Selftest: simulate corruption, verify alert fires; clean state is silent; dedup works."""
    import shutil
    print("[selftest] KB Regression Sentinel")

    # Backup state
    state_backup = None
    if STATE_FILE.exists():
        state_backup = STATE_FILE.read_text(encoding='utf-8')

    all_pass = True

    try:
        # Setup: initialize state with known values
        test_state = {
            "last_fact_count": 1000,
            "critical_nodes": {"memory/INDEX.md": 10, "memory/goals/orchestrator.md": 7},
            "resolved_conflicts": ["host_white_vram_gb"],
            "alerts_issued": [],
            "last_active_conflicts": []
        }
        STATE_FILE.write_text(json.dumps(test_state), encoding='utf-8')

        # Test 1: Clean state (no changes) should be silent
        # Use ACTUAL current values so no spurious alerts fire
        test_state_clean = dict(test_state)
        test_state_clean["last_fact_count"] = get_fact_count()  # actual count (may be 0)
        test_state_clean["critical_nodes"] = get_critical_nodes()  # actual critical nodes
        STATE_FILE.write_text(json.dumps(test_state_clean), encoding='utf-8')
        r1 = run_check()
        clean_silent = r1["status"] == "OK"
        print(f"  [{'PASS' if clean_silent else 'FAIL'}] Clean state is silent: status={r1['status']}")
        all_pass = all_pass and clean_silent

        # Test 2: Deliberate fact count drop triggers alert
        STATE_FILE.write_text(json.dumps({**test_state_clean, "alerts_issued": []}), encoding='utf-8')
        # Simulate: set last_fact_count very high so current looks like a drop
        drop_state = dict(test_state_clean)
        drop_state["last_fact_count"] = (get_fact_count() or 100) * 3  # 3x current = 66% drop
        STATE_FILE.write_text(json.dumps(drop_state), encoding='utf-8')
        r2 = run_check()
        alert_fired = any(a["type"] == "FACT_COUNT_DROP" for a in r2["new_alerts"])
        print(f"  [{'PASS' if alert_fired else 'FAIL'}] Fact drop triggers alert: alerts={[a['type'] for a in r2['new_alerts']]}")
        all_pass = all_pass and alert_fired

        # Test 3: Dedup - same condition again should NOT re-alert
        r3 = run_check()
        deduped = not any(a["type"] == "FACT_COUNT_DROP" for a in r3["new_alerts"])
        print(f"  [{'PASS' if deduped else 'FAIL'}] Dedup: same alert not repeated")
        all_pass = all_pass and deduped

        # Test 4: Critical node loss triggers alert
        STATE_FILE.write_text(json.dumps({
            "last_fact_count": get_fact_count() or 100,
            "critical_nodes": {"memory/INDEX.md": 10},
            "resolved_conflicts": [],
            "alerts_issued": [],
            "last_active_conflicts": []
        }), encoding='utf-8')
        # Run with no graph file (or empty) so critical_nodes becomes {}
        r4 = run_check()
        node_alert = any(a["type"] == "CRITICAL_NODE_LOST" for a in r4["new_alerts"])
        print(f"  [{'PASS' if node_alert else 'FAIL'}] Critical node loss detected")
        all_pass = all_pass and node_alert

    finally:
        # Restore state
        if state_backup:
            STATE_FILE.write_text(state_backup, encoding='utf-8')
        elif STATE_FILE.exists():
            STATE_FILE.unlink()

    print(f"\n[selftest] {'PASS' if all_pass else 'FAIL'}")
    return all_pass


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok = run_selftest()
        sys.exit(0 if ok else 1)
    elif "--check" in sys.argv:
        report = run_check()
        print(json.dumps(report, indent=2))
    else:
        print(__doc__)
        sys.exit(1)