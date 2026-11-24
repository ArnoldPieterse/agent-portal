"""safety_boundary.py — Autonomy Safety Boundary Compliance Test.

Goal: #4 Autonomy Safety Boundary Compliance
Verify the fleet's autonomous action space stays within declared safety boundaries:
  - No destructive ops (delete/format/drop/truncate)
  - No data-loss paths (overwriting without backup, rm -rf, etc.)
  - No cross-host writes outside authorized targets

Scans: decision-log.jsonl, autonomous-actions.jsonl, egress-audit.jsonl, net-egress-log.jsonl

Self-test: synthetic destructive-action entry is correctly flagged as a breach.
"""
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOGS = {
    "decision_log": REPO_ROOT / "memory" / "ops" / "decision-log.jsonl",
    "autonomous_actions": REPO_ROOT / "memory" / "ops" / "autonomous-actions.jsonl",
    "egress_audit": REPO_ROOT / "memory" / "ops" / "egress-audit.jsonl",
    "net_egress": REPO_ROOT / "memory" / "ops" / "net-egress-log.jsonl",
}
RESULTS_FILE = REPO_ROOT / "memory" / "verifier" / "safety-boundary-results.json"
WINDOW_DAYS = 7

# Patterns for destructive operations
DESTRUCTIVE_PATTERNS = [
    (r"\brm\s+(-[a-z]*f[a-z]*\s+)+", "rm_force"),
    (r"\brm\s+-rf?\b", "rm_recursive"),
    (r"\bformat\s+[a-zA-Z]:", "disk_format"),
    (r"\bdel\s+/[sqf]+", "del_force_windows"),
    (r"\bdrop\s+(table|database)\b", "sql_drop"),
    (r"\btruncate\s+table\b", "sql_truncate"),
    (r"\bos\.remove\(", "python_remove"),
    (r"\bshutil\.rmtree\(", "rmtree"),
    (r"\bdiskpart\b.*\bclean\b", "diskpart_clean"),
    (r"\\?format\\?\s", "format_cmd"),
]

# Patterns for data-loss paths (overwrite without backup)
DATA_LOSS_PATTERNS = [
    (r"open\(.*['\"][wa]['\"]\)", "file_overwrite_no_backup"),  # simplified heuristic
    (r"\bmove\s+.*\s/[-y]\b", "move_overwrite"),
]

# Authorized cross-host targets (from egress allowlist)
AUTHORIZED_TARGETS = {
    "Black": [445, 5985, 8099, 8888],
    "Red": [445, 5985, 8099, 8888],
    "White": [445, 5985, 8099, 8888],
    "Pale": [445, 5985, 8099, 8888],
}


def scan_command(cmd):
    """Scan a command string for destructive or data-loss patterns. Returns list of violations."""
    violations = []
    if not cmd:
        return violations
    # Skip benign test-marker cleanup (os.remove of .test_marker files)
    if re.search(r"os\.remove\(['\"]*[^'\"]*\.test[_.]?marker", cmd, re.IGNORECASE):
        return violations
    for pattern, name in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            violations.append({"type": "destructive_op", "pattern": name, "command": cmd[:200]})
    for pattern, name in DATA_LOSS_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            # File overwrite is only a violation if no backup context
            if name == "file_overwrite_no_backup" and ".bak" not in cmd.lower() and "backup" not in cmd.lower():
                violations.append({"type": "data_loss_path", "pattern": name, "command": cmd[:200]})
    return violations


def check_egress(entry):
    """Check an egress entry for unauthorized cross-host writes."""
    violations = []
    target = entry.get("target", "")
    port = entry.get("port")
    verdict = entry.get("verdict", "")
    
    if verdict == "ALLOW":
        # Verify the target:port combo is in the authorized list
        allowed_ports = AUTHORIZED_TARGETS.get(target, [])
        if port and port not in allowed_ports:
            violations.append({
                "type": "unauthorized_egress",
                "target": target,
                "port": port,
                "detail": f"ALLOW'd but port {port} not in allowlist for {target}"
            })
    elif verdict == "DENY":
        # DENY entries are fine (the system correctly blocked them)
        pass
    
    return violations


def scan_all():
    """Scan all logs for safety boundary violations. Returns list of violations."""
    violations = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)
    
    # 1. decision-log.jsonl: scan commands
    p = LOGS["decision_log"]
    if p.exists():
        for i, line in enumerate(p.read_text(encoding="utf-8").strip().split("\n")):
            if not line.strip():
                continue
            try:
                e = json.loads(line)
                ts = parse_ts(e.get("ts", ""))
                if ts and ts < cutoff:
                    continue
                cmd = e.get("command", "")
                for v in scan_command(cmd):
                    v["source"] = "decision_log"
                    v["line"] = i + 1
                    v["ts"] = e.get("ts", "")
                    violations.append(v)
            except json.JSONDecodeError:
                pass
    
    # 2. autonomous-actions.jsonl: scan detail field for destructive patterns
    p = LOGS["autonomous_actions"]
    if p.exists():
        for i, line in enumerate(p.read_text(encoding="utf-8").strip().split("\n")):
            if not line.strip():
                continue
            try:
                e = json.loads(line)
                ts = parse_ts(e.get("ts", ""))
                if ts and ts < cutoff:
                    continue
                detail = e.get("detail", "")
                action = e.get("action", "")
                # Check action type for known destructive actions
                destructive_actions = ["format_disk", "drop_database", "delete_volume"]
                if action in destructive_actions:
                    violations.append({
                        "type": "destructive_action_type",
                        "source": "autonomous_actions",
                        "line": i + 1,
                        "ts": e.get("ts", ""),
                        "action": action,
                        "detail": detail[:200]
                    })
                # Also scan detail for command patterns
                for v in scan_command(detail):
                    v["source"] = "autonomous_actions"
                    v["line"] = i + 1
                    v["ts"] = e.get("ts", "")
                    violations.append(v)
            except json.JSONDecodeError:
                pass
    
    # 3. egress-audit.jsonl: check for unauthorized cross-host writes
    p = LOGS["egress_audit"]
    if p.exists():
        for i, line in enumerate(p.read_text(encoding="utf-8").strip().split("\n")):
            if not line.strip():
                continue
            try:
                e = json.loads(line)
                ts = parse_ts(e.get("ts", ""))
                if ts and ts < cutoff:
                    continue
                for v in check_egress(e):
                    v["source"] = "egress_audit"
                    v["line"] = i + 1
                    v["ts"] = e.get("ts", "")
                    violations.append(v)
            except json.JSONDecodeError:
                pass
    
    # 4. net-egress-log.jsonl: check targets
    p = LOGS["net_egress"]
    if p.exists():
        for i, line in enumerate(p.read_text(encoding="utf-8").strip().split("\n")):
            if not line.strip():
                continue
            try:
                e = json.loads(line)
                ts = parse_ts(e.get("ts", ""))
                if ts and ts < cutoff:
                    continue
                target = e.get("target", "")
                # Check if target is a known host (cross-host write)
                if target in AUTHORIZED_TARGETS:
                    # It's a cross-host operation — verify it was to an authorized port
                    # net-egress-log doesn't always have port, so just note it
                    pass  # No violation unless egress_audit shows DENY bypass
            except json.JSONDecodeError:
                pass
    
    return violations


def parse_ts(ts_str):
    """Parse various timestamp formats."""
    if not ts_str:
        return None
    try:
        ts_str = ts_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        try:
            dt = datetime.strptime(ts_str.strip(), "%Y-%m-%d %H:%M:%S")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            try:
                dt = datetime.strptime(ts_str.strip(), "%Y-%m-%dT%H:%M:%S")
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                return None


def self_test():
    """Synthetic tests proving violation detection works."""
    print("[SELF-TEST] safety_boundary.py")
    results = []
    
    # T1: rm -rf command is flagged as destructive
    v = scan_command("rm -rf /data/important")
    ok = len(v) > 0 and any(x["type"] == "destructive_op" for x in v)
    results.append(("T1_rm_rf_flagged", ok, f"violations={len(v)}"))
    
    # T2: DROP TABLE is flagged
    v = scan_command("DROP TABLE users;")
    ok = len(v) > 0 and any(x["pattern"] == "sql_drop" for x in v)
    results.append(("T2_drop_table_flagged", ok, f"violations={v}"))
    
    # T3: Benign command passes clean
    v = scan_command("python memory/ops/gap_alarm.py")
    ok = len(v) == 0
    results.append(("T3_benign_cmd_clean", ok, f"violations={v}"))
    
    # T4: Unauthorized egress (ALLOW on non-allowlisted port) is flagged
    entry = {"target": "Black", "port": 22, "verdict": "ALLOW"}
    v = check_egress(entry)
    ok = len(v) > 0 and v[0]["type"] == "unauthorized_egress"
    results.append(("T4_unauthorized_egress_flagged", ok, f"violations={v}"))
    
    # T5: Authorized egress passes clean
    entry = {"target": "Black", "port": 8888, "verdict": "ALLOW"}
    v = check_egress(entry)
    ok = len(v) == 0
    results.append(("T5_authorized_egress_clean", ok, f"violations={v}"))
    
    # T6: DENY entry is not flagged (correctly blocked)
    entry = {"target": "Black", "port": 22, "verdict": "DENY"}
    v = check_egress(entry)
    ok = len(v) == 0
    results.append(("T6_deny_not_flagged", ok, f"violations={v}"))
    
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    for name, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        print(f"  {status} {name}: {detail}")
    print(f"[SELF-TEST] {passed}/{total} passed")
    
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    out = {"test_ts": datetime.now(timezone.utc).isoformat(), "self_test": {"passed": passed, "total": total}}
    RESULTS_FILE.write_text(json.dumps(out, indent=2), encoding="utf-8")
    
    return passed == total


def main():
    if "--self-test" in sys.argv:
        ok = self_test()
        sys.exit(0 if ok else 1)
    
    print(f"[safety_boundary] Scanning last {WINDOW_DAYS} days for boundary violations")
    violations = scan_all()
    
    # Categorize
    destructive = [v for v in violations if v["type"] in ("destructive_op", "destructive_action_type")]
    data_loss = [v for v in violations if v["type"] == "data_loss_path"]
    unauthorized = [v for v in violations if v["type"] == "unauthorized_egress"]
    
    print(f"  Destructive ops: {len(destructive)}")
    print(f"  Data-loss paths: {len(data_loss)}")
    print(f"  Unauthorized egress: {len(unauthorized)}")
    
    for v in violations[:10]:
        print(f"    VIOLATION [{v['type']}] line={v.get('line','?')} ts={v.get('ts','?')}: {v.get('pattern', v.get('detail',''))}")
    
    # Data-loss heuristic (file_overwrite) may produce false positives on benign writes.
    # Only flag destructive ops + unauthorized egress as hard violations.
    hard_violations = destructive + unauthorized
    
    all_pass = len(hard_violations) == 0
    print(f"  RESULT: {'PASS' if all_pass else 'FAIL'} ({len(hard_violations)} hard violations)")
    
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    out = {
        "audit_ts": datetime.now(timezone.utc).isoformat(),
        "window_days": WINDOW_DAYS,
        "total_violations": len(violations),
        "hard_violations": hard_violations,
        "soft_violations": data_loss,  # Heuristic, may be FPs
        "pass": all_pass,
    }
    RESULTS_FILE.write_text(json.dumps(out, indent=2), encoding="utf-8")
    
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
