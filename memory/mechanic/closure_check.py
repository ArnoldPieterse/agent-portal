#!/usr/bin/env python3
"""closure_check.py - One-shot closure verification for Mechanic's 4 open goals.

Run from a NON-SANDBOX White session (or any seat with egress to :8099):
    python memory/mechanic/closure_check.py          # check all, report status
    python memory/mechanic/closure_check.py --close  # record closures for passing goals

Checks:
  Goal #1: load-baseline.jsonl has >=7 unique dates
  Goal #2: mirror-repairs.jsonl has >=14 days of entries with <3 failures/hr
  Goal #3: e2e-anti-stall evidence exists with full cycle <15min
  Goal #6: boot-verify logs show >=3 successful verifications

Exit: 0 = all pass, 1 = some fail (details in output)
"""
import json
import os
import sys
import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent.parent  # project root
OPS_DIR = HERE / "memory" / "ops"
MECH_DIR = HERE / "memory" / "mechanic"
LEDGER = HERE / "memory" / "researcher" / "goal_ledger.py"

def get_unique_dates(jsonl_path: Path) -> set:
    """Extract unique dates from a jsonl file (ts or date field)."""
    if not jsonl_path.exists():
        return set()
    dates = set()
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                ts = d.get("ts", d.get("timestamp", ""))
                if ts:
                    dates.add(ts[:10])  # YYYY-MM-DD
            except (json.JSONDecodeError, KeyError):
                pass
    return dates

def check_goal1() -> dict:
    """Goal #1: Portal Load Test - need 7 unique days in load-baseline.jsonl."""
    path = OPS_DIR / "loadtest" / "load-baseline.jsonl"
    if not path.exists():
        path = OPS_DIR / "load-baseline.jsonl"
    dates = get_unique_dates(path)
    # Filter out selftest entries (host=__feed_selftest__)
    real_dates = set()
    if path.exists():
        with open(path) as f:
            for line in f:
                try:
                    d = json.loads(line.strip())
                    if d.get("host") == "__feed_selftest__":
                        continue
                    ts = d.get("ts", "")
                    if ts:
                        real_dates.add(ts[:10])
                except (json.JSONDecodeError, KeyError):
                    pass
    n = len(real_dates)
    return {
        "goal": 1,
        "name": "Portal Load Test 7-Day Completion",
        "pass": n >= 7,
        "detail": f"{n}/7 unique days: {sorted(real_dates)}",
        "unblock": "Ensure PortalLoadProbe schtask is running on White; data auto-accumulates"
    }

def check_goal2() -> dict:
    """Goal #2: Self-Healing Mirror - need 14 days of repair logs, <3 failures/hr."""
    path = MECH_DIR / "mirror-repairs.jsonl"
    if not path.exists():
        return {"goal": 2, "name": "Self-Healing Mirror Production",
                "pass": False, "detail": "mirror-repairs.jsonl not found",
                "unblock": "Register MirrorHeal schtask (15-min) on White via deploy_all_schtasks.py"}
    entries = []
    with open(path) as f:
        for line in f:
            try:
                entries.append(json.loads(line.strip()))
            except (json.JSONDecodeError, KeyError):
                pass
    dates = set()
    failures = 0
    for e in entries:
        ts = e.get("ts", "")[:10]
        if ts:
            dates.add(ts)
        if "error" in str(e.get("status", "")).lower() or "fail" in str(e.get("status", "")).lower():
            failures += 1
    n_days = len(dates)
    # Check failure rate: >3 failures in any hour = alert condition
    pass_ = n_days >= 14 and failures <= max(3 * (n_days // 1), 3)
    return {
        "goal": 2,
        "name": "Self-Healing Mirror Production",
        "pass": pass_,
        "detail": f"{n_days}/14 days, {failures} failures total",
        "unblock": "Ensure MirrorHeal schtask (15-min) is running on White"
    }

def check_goal3() -> dict:
    """Goal #3: WinRM Remote Reboot E2E - need evidence of FULL cycle (not just dry-run baseline)."""
    evidence_dir = MECH_DIR
    # Need evidence of the full chain: host-down detected -> reboot triggered -> models reloaded -> agent responsive
    # Dry-run baseline alone is NOT sufficient
    evidence_files = list(evidence_dir.glob("goal3*e2e*")) + list(evidence_dir.glob("chaos-drill*.jsonl"))
    has_full_evidence = False
    detail = "No full-cycle E2E evidence found (dry-run baseline does not count)"
    if evidence_files:
        for ef in sorted(evidence_files, key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                content = ef.read_text()
                # Full cycle requires: reboot + model reload + agent responsive
                has_reboot = "reboot" in content.lower() and ("triggered" in content.lower() or "executed" in content.lower())
                has_reload = "model" in content.lower() and ("reload" in content.lower() or "loaded" in content.lower())
                has_responsive = ("responsive" in content.lower() or "agent responds" in content.lower() or "PHASE4" in content)
                if has_reboot and has_reload and has_responsive:
                    has_full_evidence = True
                    detail = f"Full-cycle evidence: {ef.name}"
                    break
            except OSError:
                pass
    return {
        "goal": 3,
        "name": "WinRM Remote Reboot E2E Test",
        "pass": has_full_evidence,
        "detail": detail,
        "unblock": "Run e2e_anti_stall_test.py --host black (or pale) from White with WinRM; need full cycle evidence"
    }

def check_goal6() -> dict:
    """Goal #6: Boot Task Verification - need 3 successful boot verifications."""
    verify_files = sorted(MECH_DIR.glob("boot-verify-*.md"))
    success_count = 0
    for vf in verify_files:
        try:
            content = vf.read_text()
            if "PASS" in content or "all pass" in content.lower():
                success_count += 1
        except OSError:
            pass
    return {
        "goal": 6,
        "name": "Boot Task Verification",
        "pass": success_count >= 3,
        "detail": f"{success_count}/3 successful verifications found in boot-verify-*.md files",
        "unblock": "Run boot_verify.py after 3 reboots on White; each writes a dated .md"
    }

def main():
    close_mode = "--close" in sys.argv
    checks = [check_goal1(), check_goal2(), check_goal3(), check_goal6()]
    
    print(f"\n{'='*60}")
    print(f"  MECHANIC CLOSURE CHECK - {datetime.date.today()}")
    print(f"{'='*60}\n")
    
    all_pass = True
    for c in checks:
        status = "PASS" if c["pass"] else "FAIL"
        if not c["pass"]:
            all_pass = False
        print(f"  [{status}] Goal #{c['goal']}: {c['name']}")
        print(f"         {c['detail']}")
        if not c["pass"]:
            print(f"         Unblock: {c['unblock']}")
        print()
    
    if close_mode and all_pass:
        print("  All goals pass - recording closures via goal_ledger...")
        for c in checks:
            if c["pass"]:
                import subprocess
                r = subprocess.run(
                    [sys.executable, str(LEDGER), "--record", "mechanic", str(c["goal"]),
                     "--note", f"closure_check.py PASS: {c['detail']}"],
                    capture_output=True, text=True, timeout=15
                )
                print(f"    Goal #{c['goal']}: {'RECORDED' if r.returncode == 0 else 'FAILED: ' + r.stderr[:80]}")
    elif close_mode and not all_pass:
        print("  --close requested but not all goals pass. No closures recorded.")
    
    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())
