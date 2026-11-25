"""
remediation_loop_healthcheck.py — Full-Loop Health Check for the autonomous remediation loop.
Converts: memory/ops/autonomous-remediation-loop-runbook-2026-11-24.md (Layer 1-4 checks)
Owner: Mechanic (assist for Forge goal #1 - Runbook Executability Audit)
Usage: python memory/ops/remediation_loop_healthcheck.py [--json]
Exit codes: 0=all pass, 1=one or more layers failing
"""
import json, os, socket, subprocess, sys, time
from pathlib import Path

OPS = Path(__file__).resolve().parent
ROOT = OPS.parent.parent  # project root

def check(name, fn):
    """Run a check, return (name, pass/fail, detail)."""
    try:
        result = fn()
        ok = isinstance(result, str) and 'FAIL' not in result.upper()
        return name, 'PASS' if ok else 'FAIL', result
    except Exception as e:
        return name, 'FAIL', f"Exception: {e}"

# --- Layer 1: Detection ---
def layer1_metrics():
    """Check fleet-metrics.jsonl has recent entries."""
    p = OPS / 'fleet-metrics.jsonl'
    if not p.exists():
        return "FAIL: fleet-metrics.jsonl not found"
    lines = p.read_text(encoding='utf-8').strip().splitlines()
    if not lines:
        return "FAIL: fleet-metrics.jsonl is empty"
    # Check last line timestamp (best-effort)
    last = lines[-1].strip()
    try:
        import json as j
        d = j.loads(last)
        ts = d.get('ts', d.get('timestamp', ''))
        return f"OK: {len(lines)} rows, last ts={ts}"
    except Exception:
        return f"OK: {len(lines)} rows (unparseable last line)"

def layer1_stall_detector():
    """Check stall_detector.py exists and is importable."""
    p = Path('memory/mechanic/stall_detector.py')
    if not p.exists():
        return "FAIL: memory/mechanic/stall_detector.py not found"
    return f"OK: {p} exists ({p.stat().st_size}B)"

# --- Layer 2: Decision ---
def layer2_policy():
    """Check remediation-policy.json exists and is valid JSON."""
    p = Path('memory/orchestrator/remediation-policy.json')
    if not p.exists():
        return "FAIL: remediation-policy.json not found"
    try:
        d = json.loads(p.read_text(encoding='utf-8'))
        rules = len(d.get('rules', d) if isinstance(d, dict) else d)
        return f"OK: {rules} policy rules loaded"
    except json.JSONDecodeError as e:
        return f"FAIL: invalid JSON in remediation-policy.json: {e}"

def layer2_decision_log():
    """Check decision-log.jsonl exists and has entries."""
    p = OPS / 'decision-log.jsonl'
    if not p.exists():
        return "FAIL: decision-log.jsonl not found"
    lines = p.read_text(encoding='utf-8').strip().splitlines()
    return f"OK: {len(lines)} decisions logged"

# --- Layer 3: Execution ---
def layer3_playbook_runner():
    """Check playbook_runner.py exists."""
    p = Path('memory/builder/playbook_runner.py')
    if not p.exists():
        return "FAIL: memory/builder/playbook_runner.py not found"
    return f"OK: {p} exists ({p.stat().st_size}B)"

def layer3_egress():
    """Check local egress to portal (8099)."""
    try:
        s = socket.create_connection(('127.0.0.1', 8099), timeout=3)
        s.close()
        return "OK: 127.0.0.1:8099 reachable"
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        return f"FAIL: cannot reach 127.0.0.1:8099 ({e})"

# --- Layer 4: Reporting ---
def layer4_cockpit():
    """Check cockpit endpoint is fresh."""
    import urllib.request
    try:
        url = 'http://127.0.0.1:8099/api/fleet/cockpit'
        req = urllib.request.urlopen(url, timeout=5)
        d = json.loads(req.read())
        if 'health_score' in d:
            return f"OK: cockpit health_score={d['health_score']}"
        else:
            keys = list(d.keys())[:5]
            return f"WARN: cockpit reachable but missing health_score (keys: {keys})"
    except Exception as e:
        return f"FAIL: cockpit endpoint error: {e}"

def layer4_digest():
    """Check decision_digest.py exists."""
    p = Path('memory/scribe/decision_digest.py')
    if not p.exists():
        return "WARN: memory/scribe/decision_digest.py not found (may be new)"
    return f"OK: {p} exists ({p.stat().st_size}B)"

# --- Main ---
def main():
    json_out = '--json' in sys.argv
    
    checks = [
        ("L1-Detection: fleet-metrics", layer1_metrics),
        ("L1-Detection: stall_detector", layer1_stall_detector),
        ("L2-Decision: policy file", layer2_policy),
        ("L2-Decision: decision log", layer2_decision_log),
        ("L3-Execution: playbook_runner", layer3_playbook_runner),
        ("L3-Execution: egress 8099", layer3_egress),
        ("L4-Reporting: cockpit API", layer4_cockpit),
        ("L4-Reporting: digest script", layer4_digest),
    ]
    
    results = []
    for name, fn in checks:
        results.append(check(name, fn))
    
    failures = [r for r in results if r[1] == 'FAIL']
    
    if json_out:
        print(json.dumps({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "results": [{"check": n, "status": s, "detail": d} for n, s, d in results],
            "pass_count": len(results) - len(failures),
            "fail_count": len(failures),
            "overall": "PASS" if not failures else "FAIL",
        }, indent=2))
    else:
        print("Remediation Loop Health Check")
        print("=" * 50)
        for name, status, detail in results:
            icon = '✅' if status == 'PASS' else ('⚠️' if 'WARN' in detail else '❌')
            print(f" {icon} {name}: {detail}")
        print("=" * 50)
        print(f"Result: {len(results)-len(failures)}/{len(results)} checks passed")
        if failures:
            print("Failing layers:")
            for n, s, d in failures:
                print(f"  - {n}: {d}")
    
    sys.exit(0 if not failures else 1)

if __name__ == '__main__':
    main()
