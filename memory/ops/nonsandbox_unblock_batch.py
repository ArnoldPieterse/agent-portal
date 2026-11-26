#!/usr/bin/env python3
"""
Non-Sandbox Unblock Batch — one-shot runner for all currently-blocked-on-non-sandbox items.

WHY: Multiple agents (Pixel, Verifier, Scribe/Mechanic) are hard-blocked on the same
class of issue: sandbox egress-blocks loopback CDP, elev.py SYSTEM is dead, schtasks COM
is not registered. This script bundles ALL such items into a single executable that,
when run from ANY non-sandbox seat (RDP, Pale-Black-Red, or any Windows host with the
portal repo checked out), unblocks everything in one pass.

PREREQS on the target seat:
  - Python 3.10+ with `websockets` installed (`python -m pip install websockets`)
  - Edge or Chrome at default install path (for CDP leg)
  - Portal repo checked out at the same relative structure (memory/...)
  - For chaos-recovery: SEAT_BASE env var set to a reachable Studio URL

USAGE:
  python memory/ops/nonsandbox_unblock_batch.py          # run all unblocked items
  python memory/ops/nonsandbox_unblock_batch.py --list   # list what would be done
  python memory/ops/nonsandbox_unblock_batch.py --only cdp  # run only the CDP leg

EXIT CODES:
  0 = all attempted items passed
  1 = one or more items failed (details in output + report JSON)
  2 = no items could be attempted (prereqs missing)
"""
import argparse, json, os, shutil, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # memory/ops/x.py -> repo root
EVIDENCE_DIR = REPO_ROOT / "memory" / "ops"
REPORT_PATH = EVIDENCE_DIR / "nonsandbox_unblock_report.json"

def ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def run_cmd(cmd, cwd=None, timeout=300, env_extra=None):
    """Run a command, capture output. Returns (exit_code, stdout, stderr)."""
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    try:
        r = subprocess.run(cmd, shell=True, cwd=cwd or str(REPO_ROOT),
                           capture_output=True, text=True, timeout=timeout, env=env)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"TIMEOUT after {timeout}s"
    except Exception as e:
        return 1, "", str(e)

# ─── ITEM 1: Pixel goal #6 — live CDP DOM check @375/@768 ─────────────────────
def item_cdp_screenshot():
    """Run cdp_375_dom_check.py. Exit 0 = all AC pass."""
    script_path = REPO_ROOT / "memory" / "pixel" / "cdp_375_dom_check.py"
    if not script_path.exists():
        return {"item": "cdp_screenshot", "status": "SKIP", "reason": f"script not found: {script_path}"}
    
    # Prereq check: websockets importable
    import importlib.util
    if importlib.util.find_spec('websockets') is None:
        return {"item": "cdp_screenshot", "status": "FAIL", 
                "reason": "websockets not importable in current python",
                "fix": "python -m pip install websockets"}
    
    t0 = time.time()
    r, out, err = run_cmd(f'"{sys.executable}" "{script_path}"', timeout=300)
    elapsed = round(time.time() - t0, 1)
    
    status = "PASS" if r == 0 else "FAIL"
    result = {
        "item": "cdp_screenshot",
        "status": status,
        "exit_code": r,
        "elapsed_s": elapsed,
        "stdout_tail": out[-500:] if out else "",
        "stderr_tail": err[-300:] if err else "",
    }
    # Check for report artifact
    report = REPO_ROOT / "memory" / "pixel" / "cdp_375_dom_check.report.json"
    if report.exists():
        result["report_path"] = str(report.relative_to(REPO_ROOT))
        try:
            data = json.loads(report.read_text(encoding="utf-8"))
            result["report_summary"] = {k: v for k, v in data.items() if k in ("pass", "fail", "widths")}
        except Exception:
            pass
    return result

# ─── ITEM 2: Verifier — chaos-recovery live drill (3 real incidents) ──────────
def item_chaos_recovery_live():
    """Run chaos_recovery_drill.py --live with SEAT_BASE. Requires env var."""
    script_path = REPO_ROOT / "memory" / "verifier" / "chaos_recovery_drill.py"
    if not script_path.exists():
        return {"item": "chaos_recovery_live", "status": "SKIP", "reason": f"script not found: {script_path}"}
    
    seat_base = os.environ.get("SEAT_BASE", "")
    if not seat_base:
        return {"item": "chaos_recovery_live", "status": "SKIP",
                "reason": "SEAT_BASE env var not set",
                "fix": "Set SEAT_BASE to a reachable Studio URL, e.g. http://127.0.0.1:8888"}
    
    t0 = time.time()
    r, out, err = run_cmd(f'"{sys.executable}" "{script_path}" --live', 
                          env_extra={"SEAT_BASE": seat_base}, timeout=600)
    elapsed = round(time.time() - t0, 1)
    
    status = "PASS" if r == 0 else "FAIL"
    return {
        "item": "chaos_recovery_live",
        "status": status,
        "exit_code": r,
        "elapsed_s": elapsed,
        "seat_base": seat_base,
        "stdout_tail": out[-500:] if out else "",
        "stderr_tail": err[-300:] if err else "",
    }

# ─── ITEM 3: Scribe/Mechanic — schtasks registration for commit trigger ──────
def item_schtasks_register():
    """Run register_trigger_task.py to create the scheduled task."""
    script_path = REPO_ROOT / "memory" / "verifier" / "register_trigger_task.py"
    if not script_path.exists():
        return {"item": "schtasks_register", "status": "SKIP", "reason": f"script not found: {script_path}"}
    
    t0 = time.time()
    r, out, err = run_cmd(f'"{sys.executable}" "{script_path}"', timeout=60)
    elapsed = round(time.time() - t0, 1)
    
    status = "PASS" if r == 0 else "FAIL"
    return {
        "item": "schtasks_register",
        "status": status,
        "exit_code": r,
        "elapsed_s": elapsed,
        "stdout_tail": out[-300:] if out else "",
        "stderr_tail": err[-300:] if err else "",
    }

# ─── MAIN ─────────────────────────────────────────────────────────────────────
ITEMS = [
    ("cdp", item_cdp_screenshot, "Pixel goal #6: live CDP DOM check @375/@768"),
    ("chaos", item_chaos_recovery_live, "Verifier: chaos-recovery live drill (needs SEAT_BASE)"),
    ("schtasks", item_schtasks_register, "Scribe/Mechanic: schtasks commit-trigger registration"),
]

def main():
    ap = argparse.ArgumentParser(description="Non-sandbox unblock batch")
    ap.add_argument("--list", action="store_true", help="List items without running")
    ap.add_argument("--only", choices=[k for k, _, _ in ITEMS], help="Run only one item")
    args = ap.parse_args()

    if args.list:
        print(f"Non-Sandbox Unblock Batch — {ts()}")
        print(f"Repo root: {REPO_ROOT}")
        print()
        for key, fn, desc in ITEMS:
            print(f"  [{key:10s}] {desc}")
        return 0

    targets = [(k, f, d) for k, f, d in ITEMS if args.only is None or k == args.only]
    results = []
    print(f"=== Non-Sandbox Unblock Batch — {ts()} ===")
    print(f"Repo: {REPO_ROOT}")
    print()

    for key, fn, desc in targets:
        print(f"[{key}] {desc} ...", end=" ", flush=True)
        try:
            res = fn()
        except Exception as e:
            res = {"item": key, "status": "ERROR", "reason": str(e)}
        results.append(res)
        icon = {"PASS": "✓", "FAIL": "✗", "SKIP": "→", "ERROR": "!"}.get(res.get("status"), "?")
        print(f"{icon} {res.get('status')} ({res.get('elapsed_s', 'N/A')}s)")
        if res.get("reason"):
            print(f"       reason: {res['reason']}")
        if res.get("fix"):
            print(f"       fix:    {res['fix']}")

    # Write report
    report = {"ts": ts(), "seat": os.environ.get("COMPUTERNAME", "unknown"), 
              "python": sys.executable, "results": results}
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nReport: {REPORT_PATH.relative_to(REPO_ROOT)}")

    passed = sum(1 for r in results if r["status"] == "PASS")
    skipped = sum(1 for r in results if r["status"] == "SKIP")
    failed = sum(1 for r in results if r["status"] in ("FAIL", "ERROR"))
    print(f"Summary: {passed} pass, {skipped} skip, {failed} fail / {len(results)} total")

    if failed > 0:
        return 1
    if passed == 0 and skipped == len(results):
        return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())
