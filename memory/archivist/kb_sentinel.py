#!/usr/bin/env python3
"""KB Regression Sentinel - monitors knowledge base for regressions.

Checks:
1. Fact count drops > threshold% vs previous snapshot
2. Critical node in-degree changes (nodes with in-degree >= CRITICAL_THRESHOLD)
3. Previously-resolved contradiction reappears

Usage:
    python memory/archivist/kb_sentinel.py            # normal run
    python memory/archivist/kb_sentinel.py --selftest  # verification suite
    python memory/archivist/kb_sentinel.py --corrupt   # simulate corruption (for testing)
"""
import json, sys, hashlib
from datetime import datetime, timezone
from pathlib import Path

MEMORY = Path(__file__).resolve().parent.parent.parent
SENTINEL_DIR = MEMORY / "memory" / "archivist"
SNAPSHOT_PATH = SENTINEL_DIR / "kb-sentinel-snapshot.json"
ALERT_STATE_PATH = SENTINEL_DIR / "kb-sentinel-alert-state.json"

FACT_DROP_THRESHOLD = 0.05       # alert if fact count drops >5%
CRITICAL_IN_DEGREE = 5           # nodes with in-degree >= this are "critical"
CONTRADICTION_FILE = SENTINEL_DIR / "conflict-report-2026-11-23.json"

def get_fact_count() -> int:
    """Get current doc/fact count from knowledge-index.json."""
    idx_path = SENTINEL_DIR / "knowledge-index.json"
    if not idx_path.exists():
        return 0
    data = json.loads(idx_path.read_text(encoding="utf-8"))
    # Supports both 'facts' and 'docs' keys (schema evolution)
    facts = data.get("facts", data.get("docs", []))
    return len(facts)

def get_critical_nodes() -> dict:
    """Get in-degree of critical nodes from knowledge graph."""
    kg_path = SENTINEL_DIR / "knowledge-graph-v3.json"
    if not kg_path.exists():
        return {}
    data = json.loads(kg_path.read_text(encoding="utf-8"))
    edges = data.get("edges", [])
    in_degree = {}
    for e in edges:
        target = e.get("target", "")
        in_degree[target] = in_degree.get(target, 0) + 1
    # Return only critical nodes (in-degree >= threshold)
    return {k: v for k, v in in_degree.items() if v >= CRITICAL_IN_DEGREE}

def get_resolved_contradictions() -> list:
    """Get subjects that were previously flagged as contradictions."""
    if not CONTRADICTION_FILE.exists():
        return []
    try:
        data = json.loads(CONTRADICTION_FILE.read_text(encoding="utf-8"))
        conflicts = data.get("conflicts", [])
        return [c.get("subject", "") for c in conflicts if c.get("subject")]
    except (json.JSONDecodeError, KeyError):
        return []

def snapshot() -> dict:
    """Capture current KB state."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fact_count": get_fact_count(),
        "critical_nodes": get_critical_nodes(),
        "known_contradictions": get_resolved_contradictions(),
    }

def load_alert_state() -> dict:
    if ALERT_STATE_PATH.exists():
        return json.loads(ALERT_STATE_PATH.read_text(encoding="utf-8"))
    return {"alerted_conditions": []}

def save_alert_state(state: dict):
    ALERT_STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")

def check_regressions(prev: dict, curr: dict) -> list:
    """Compare snapshots and return list of regression alerts."""
    alerts = []
    
    # Check 1: Fact count drop
    prev_facts = prev.get("fact_count", 0)
    curr_facts = curr.get("fact_count", 0)
    if prev_facts > 0:
        drop_pct = (prev_facts - curr_facts) / prev_facts
        if drop_pct > FACT_DROP_THRESHOLD:
            cond_id = f"fact_drop_{drop_pct:.3f}"
            alerts.append({
                "type": "FACT_COUNT_DROP",
                "detail": f"Facts dropped from {prev_facts} to {curr_facts} ({drop_pct*100:.1f}% decrease)",
                "condition_id": cond_id,
            })
    
    # Check 2: Critical node in-degree changes
    prev_nodes = prev.get("critical_nodes", {})
    curr_nodes = curr.get("critical_nodes", {})
    for node, prev_deg in prev_nodes.items():
        curr_deg = curr_nodes.get(node, 0)
        if curr_deg != prev_deg:
            cond_id = f"node_{hashlib.md5(node.encode()).hexdigest()[:8]}"
            alerts.append({
                "type": "CRITICAL_NODE_CHANGE",
                "detail": f"Node '{node}' in-degree changed: {prev_deg} -> {curr_deg}",
                "condition_id": cond_id,
            })
    # New critical nodes appearing
    for node in curr_nodes:
        if node not in prev_nodes:
            cond_id = f"new_node_{hashlib.md5(node.encode()).hexdigest()[:8]}"
            alerts.append({
                "type": "NEW_CRITICAL_NODE",
                "detail": f"New critical node '{node}' with in-degree {curr_nodes[node]}",
                "condition_id": cond_id,
            })
    
    # Check 3: Previously-resolved contradiction reappearing
    # If a subject was in prev's known_contradictions but NOT in curr's (meaning it was resolved),
    # and NOW appears again -> regression
    prev_contra = set(prev.get("known_contradictions", []))
    curr_contra = set(curr.get("known_contradictions", []))
    # For our purposes, we track which contradictions exist now
    # A "reappearance" would mean a contradiction was absent in a prior check but is back
    # Simplified: if current has more contradictions than previous snapshot tracked
    new_contras = curr_contra - prev_contra
    for contra in sorted(new_contras):
        cond_id = f"contra_{hashlib.md5(contra.encode()).hexdigest()[:8]}"
        alerts.append({
            "type": "CONTRADICTION_REAPPEARED",
            "detail": f"Contradiction on subject '{contra}' reappeared",
            "condition_id": cond_id,
        })
    
    return alerts

def dedupe_alerts(alerts: list, state: dict) -> list:
    """Remove alerts for conditions already in the alerted set."""
    already = set(state.get("alerted_conditions", []))
    fresh = [a for a in alerts if a["condition_id"] not in already]
    # Update state with newly-alerted conditions
    for a in fresh:
        state["alerted_conditions"].append(a["condition_id"])
    return fresh

def write_report(alerts: list, curr: dict) -> Path:
    """Write sentinel report."""
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report_path = SENTINEL_DIR / f"kb-sentinel-{date_str}.md"
    
    lines = [
        "# KB Sentinel Report - " + date_str,
        "",
        f"**Run time:** {curr.get('timestamp', 'unknown')}",
        f"**Fact count:** {curr.get('fact_count', 0)}",
        f"**Critical nodes:** {len(curr.get('critical_nodes', {}))}",
        f"**Known contradictions:** {len(curr.get('known_contradictions', []))}",
        "",
    ]
    
    if alerts:
        lines.append(f"## ALERTS ({len(alerts)})")
        lines.append("")
        for a in alerts:
            lines.append(f"- **{a['type']}**: {a['detail']}")
        lines.append("")
    else:
        lines.append("## Status: CLEAN (no regressions detected)")
        lines.append("")
    
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path

def run() -> int:
    """Main sentinel run."""
    # Load previous snapshot
    if SNAPSHOT_PATH.exists():
        prev = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    else:
        prev = None
    
    # Current snapshot
    curr = snapshot()
    
    alerts = []
    if prev is not None:
        raw_alerts = check_regressions(prev, curr)
        state = load_alert_state()
        alerts = dedupe_alerts(raw_alerts, state)
        save_alert_state(state)
    
    # Save current snapshot as new baseline
    SNAPSHOT_PATH.write_text(json.dumps(curr, indent=2), encoding="utf-8")
    
    # Write report
    report = write_report(alerts, curr)
    
    if alerts:
        print(f"ALERTS: {len(alerts)} regression(s) detected -> {report.name}")
        for a in alerts:
            print(f"  [{a['type']}] {a['detail']}")
        return 1
    else:
        print(f"CLEAR: no regressions. Facts={curr['fact_count']}, critical_nodes={len(curr['critical_nodes'])}")
        return 0

def run_selftest() -> bool:
    """Selftest: verify all three alert types trigger correctly."""
    import tempfile, shutil
    
    ok = True
    results = []
    
    # Setup: create a fake previous snapshot with known values
    test_dir = SENTINEL_DIR / "_sentinel_test"
    test_dir.mkdir(exist_ok=True)
    
    # Backup existing state
    backup_snap = None
    if SNAPSHOT_PATH.exists():
        backup_snap = SNAPSHOT_PATH.read_text(encoding="utf-8")
    backup_alerts = None
    if ALERT_STATE_PATH.exists():
        backup_alerts = ALERT_STATE_PATH.read_text(encoding="utf-8")
    
    try:
        # --- Test 1: Fact count drop triggers alert ---
        prev_snap = {
            "timestamp": "2026-11-22T00:00:00Z",
            "fact_count": 1000,
            "critical_nodes": {"nodeA": 10, "nodeB": 5},
            "known_contradictions": ["sub1", "sub2"],
        }
        curr_snap = {
            "timestamp": "2026-11-23T00:00:00Z",
            "fact_count": 900,  # 10% drop > 5% threshold
            "critical_nodes": {"nodeA": 10, "nodeB": 5},
            "known_contradictions": ["sub1", "sub2"],
        }
        alerts = check_regressions(prev_snap, curr_snap)
        t1 = any(a["type"] == "FACT_COUNT_DROP" for a in alerts)
        results.append(("fact_drop_alert", "PASS" if t1 else "FAIL", f"{len(alerts)} alert(s)"))
        ok = ok and t1
        
        # --- Test 2: Clean state is silent ---
        curr_clean = {
            "timestamp": "2026-11-23T00:00:00Z",
            "fact_count": 998,  # <5% drop
            "critical_nodes": {"nodeA": 10, "nodeB": 5},
            "known_contradictions": ["sub1", "sub2"],
        }
        alerts_clean = check_regressions(prev_snap, curr_clean)
        t2 = len(alerts_clean) == 0
        results.append(("clean_state_silent", "PASS" if t2 else "FAIL", f"{len(alerts_clean)} alert(s)"))
        ok = ok and t2
        
        # --- Test 3: Critical node in-degree change triggers alert ---
        curr_node_change = {
            "timestamp": "2026-11-23T00:00:00Z",
            "fact_count": 998,
            "critical_nodes": {"nodeA": 7, "nodeB": 5},  # nodeA changed from 10 to 7
            "known_contradictions": ["sub1", "sub2"],
        }
        alerts_node = check_regressions(prev_snap, curr_node_change)
        t3 = any(a["type"] == "CRITICAL_NODE_CHANGE" for a in alerts_node)
        results.append(("node_in_degree_change", "PASS" if t3 else "FAIL", f"{len(alerts_node)} alert(s)"))
        ok = ok and t3
        
        # --- Test 4: Contradiction reappears triggers alert ---
        curr_contra = {
            "timestamp": "2026-11-23T00:00:00Z",
            "fact_count": 998,
            "critical_nodes": {"nodeA": 10, "nodeB": 5},
            "known_contradictions": ["sub1", "sub2", "sub3"],  # sub3 is new
        }
        alerts_contra = check_regressions(prev_snap, curr_contra)
        t4 = any(a["type"] == "CONTRADICTION_REAPPEARED" for a in alerts_contra)
        results.append(("contradiction_reappears", "PASS" if t4 else "FAIL", f"{len(alerts_contra)} alert(s)"))
        ok = ok and t4
        
        # --- Test 5: Alert deduplication ---
        state = {"alerted_conditions": []}
        first_pass = dedupe_alerts(alerts, state)
        second_pass = dedupe_alerts(alerts, state)
        t5 = len(first_pass) > 0 and len(second_pass) == 0
        results.append(("alerts_deduped", "PASS" if t5 else "FAIL", f"first={len(first_pass)}, second={len(second_pass)}"))
        ok = ok and t5
        
    finally:
        # Restore state
        if backup_snap is not None:
            SNAPSHOT_PATH.write_text(backup_snap, encoding="utf-8")
        else:
            SNAPSHOT_PATH.unlink(missing_ok=True)
        if backup_alerts is not None:
            ALERT_STATE_PATH.write_text(backup_alerts, encoding="utf-8")
        else:
            ALERT_STATE_PATH.unlink(missing_ok=True)
        shutil.rmtree(test_dir, ignore_errors=True)
    
    print("=== KB SENTINEL SELFTEST ===\n")
    for name, status, detail in results:
        print(f"  [{status}] {name}: {detail}")
    print(f"\nResult: {'PASS' if ok else 'FAIL'} ({sum(1 for _,s,_ in results if s=='PASS')}/{len(results)} checks)")
    
    # Save evidence
    evidence = {"results": [{"test": n, "pass": s == "PASS", "detail": d} for n,s,d in results], "all_pass": ok}
    (SENTINEL_DIR / "kb-sentinel-selftest.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    
    return ok

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--selftest" in args:
        ok = run_selftest()
        sys.exit(0 if ok else 1)
    elif "--corrupt" in args:
        # Simulate corruption by reducing fact count in a temp snapshot
        fake_prev = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fact_count": get_fact_count() * 2,  # pretend we had twice as many
            "critical_nodes": {},
            "known_contradictions": [],
        }
        SNAPSHOT_PATH.write_text(json.dumps(fake_prev, indent=2), encoding="utf-8")
        print(f"Corrupted snapshot: pretending fact_count was {fake_prev['fact_count']}")
        run()
    else:
        sys.exit(run())
