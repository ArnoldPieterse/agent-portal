#!/usr/bin/env python3
"""
playbook_runner.py - Auto-Remediation Playbook Runner
Goal #1 (Builder, cycle-10)

Usage:
    python memory/builder/playbook_runner.py <runbook.md> [--dry-run] [--inject-failure N] [--timeout-scale F]

Parses a markdown runbook, executes each command step-by-step, verifies output,
logs to decision-log.jsonl, and rolls back on failure.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

DECISION_LOG = Path("memory/ops/decision-log.jsonl")


# --- Runbook Parser -----------------------------------------------------------

def parse_runbook(text: str) -> dict:
    """Parse markdown runbook into structured dict."""
    rb = {
        "title": "",
        "metadata": {},
        "steps": [],
    }

    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if m:
        rb["title"] = m.group(1).strip()

    meta_section = re.search(r"##\s+Metadata\s*\n(.*?)(?=\n##|\Z)", text, re.DOTALL)
    if meta_section:
        for line in meta_section.group(1).splitlines():
            m = re.match(r"^-\s+(\w+)\s*:\s*(.+)$", line.strip())
            if m:
                key, val = m.group(1), m.group(2).strip()
                rb["metadata"][key] = (val == "true") if val in ("true","false") else val

    step_pattern = re.compile(
        r"###\s+Step\s+(\d+)\s*:\s*(.+?)\n(.*?)(?=\n###\s+Step|\Z)",
        re.DOTALL
    )
    for sm in step_pattern.finditer(text):
        step_num = int(sm.group(1))
        desc = sm.group(2).strip()
        body = sm.group(3)

        step = {"num": step_num, "description": desc}

        cm = re.search(r"^-\s+command\s*:\s*`(.+?)`\s*$", body, re.MULTILINE)
        if cm:
            step["command"] = cm.group(1)

        em = re.search(r"^-\s+expected\s*:\s*(.+?)\s*$", body, re.MULTILINE)
        if em:
            raw_expected = em.group(1).strip().strip("`")
            if raw_expected.startswith("exit_code:"):
                step["expected"] = ("exit_code", int(raw_expected.split(":")[1]))
            else:
                step["expected"] = ("pattern", raw_expected)

        tm = re.search(r"^-\s+timeout\s*:\s*(\d+)", body, re.MULTILINE)
        if tm:
            step["timeout"] = int(tm.group(1))
        else:
            step["timeout"] = 30

        rm = re.search(r"^-\s+rollback_command\s*:\s*`(.+?)`\s*$", body, re.MULTILINE)
        if rm:
            step["rollback_command"] = rm.group(1)

        rb["steps"].append(step)

    return rb


# --- Executor -----------------------------------------------------------------

def run_command(cmd: str, timeout: int):
    """Run a shell command. Returns (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, encoding="utf-8", errors="replace"
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT after %ds" % timeout


def verify(expected, exit_code, stdout):
    """Check expected pattern/exit code. Returns (passed, detail)."""
    kind, val = expected
    if kind == "exit_code":
        if exit_code == val:
            return True, "exit_code=%d matches expected %d" % (exit_code, val)
        return False, "exit_code=%d, expected %d" % (exit_code, val)
    else:
        if re.search(val, stdout):
            return True, "pattern '%s' found in output" % val
        return False, "pattern '%s' NOT found; stdout=%r" % (val, stdout[:200])


def log_decision(entry: dict):
    """Append a decision entry to decision-log.jsonl."""
    DECISION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(DECISION_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# --- Main ---------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Auto-Remediation Playbook Runner")
    ap.add_argument("runbook", help="Path to markdown runbook")
    ap.add_argument("--dry-run", action="store_true", help="Show steps without executing")
    ap.add_argument("--inject-failure", type=int, metavar="N",
                    help="Simulate failure at step N (for rollback testing)")
    ap.add_argument("--timeout-scale", type=float, default=1.0,
                    help="Multiply all timeouts by this factor")
    args = ap.parse_args()

    rb_path = Path(args.runbook)
    if not rb_path.exists():
        print("ERROR: runbook not found: %s" % rb_path)
        sys.exit(2)

    text = rb_path.read_text(encoding="utf-8")
    rb = parse_runbook(text)

    print("Runbook: %s" % rb["title"])
    print("Steps:   %d" % len(rb["steps"]))
    print("Agent:   %s" % rb["metadata"].get("agent", "unknown"))
    print()

    if args.dry_run:
        print("[DRY RUN] Steps that would execute:")
        for s in rb["steps"]:
            exp = s.get("expected", ("pattern","?"))
            exp_str = ("exit_code:%d" % exp[1]) if exp[0]=="exit_code" else ("~%s" % exp[1])
            print("  Step %d: %s" % (s["num"], s["description"]))
            print("    cmd:      %s" % s.get("command","?"))
            print("    expected: %s" % exp_str)
            print("    timeout:  %ss" % s.get("timeout",30))
            if "rollback_command" in s:
                print("    rollback: %s" % s["rollback_command"])
        print()
        print("[DRY RUN] No commands executed.")
        log_decision({
            "ts": datetime.now(timezone.utc).isoformat(),
            "agent": rb["metadata"].get("agent", "Builder"),
            "type": "playbook_dry_run",
            "runbook": str(rb_path),
            "steps_parsed": len(rb["steps"]),
            "outcome": "dry_run_complete"
        })
        return

    # Real execution
    t_start = time.time()
    completed_steps = []
    all_results = []
    overall_success = True
    failure_step = None

    for step in rb["steps"]:
        sn = step["num"]
        cmd = step.get("command", "")
        timeout = int(step.get("timeout", 30) * args.timeout_scale)
        expected = step.get("expected", ("exit_code", 0))

        print("Step %d: %s" % (sn, step["description"]))
        print("  cmd: %s" % cmd)

        if args.inject_failure == sn:
            exit_code, stdout, stderr = -1, "", "INJECTED FAILURE (test)"
            print("  [INJECTED FAILURE at this step]")
        else:
            exit_code, stdout, stderr = run_command(cmd, timeout)

        passed, detail = verify(expected, exit_code, stdout)
        status = "OK" if passed else "FAIL"
        print("  result: %s - %s" % (status, detail))

        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "agent": rb["metadata"].get("agent", "Builder"),
            "type": "playbook_step",
            "runbook": str(rb_path),
            "step": sn,
            "description": step["description"],
            "command": cmd,
            "exit_code": exit_code,
            "passed": passed,
            "detail": detail,
        }
        all_results.append(entry)
        log_decision(entry)

        if not passed:
            overall_success = False
            failure_step = sn
            break

        completed_steps.append(step)

    # Rollback on failure
    rollback_results = []
    if not overall_success and rb["metadata"].get("rollback_on_failure"):
        print()
        print("[ROLLBACK] Failure at step %d; rolling back steps %s (reverse order)..."
              % (failure_step, [s["num"] for s in completed_steps]))
        for step in reversed(completed_steps):
            rc_cmd = step.get("rollback_command")
            if not rc_cmd:
                print("  Step %d: no rollback command, skipping" % step["num"])
                continue
            print("  Rolling back step %d: %s" % (step["num"], rc_cmd))
            rc_code, rc_out, rc_err = run_command(rc_cmd, 30)
            ok = rc_code == 0
            print("    %s (exit=%d)" % ("OK" if ok else "FAIL", rc_code))
            rollback_results.append({
                "step": step["num"],
                "command": rc_cmd,
                "exit_code": rc_code,
                "success": ok,
            })
            log_decision({
                "ts": datetime.now(timezone.utc).isoformat(),
                "agent": rb["metadata"].get("agent", "Builder"),
                "type": "playbook_rollback",
                "runbook": str(rb_path),
                "step": step["num"],
                "command": rc_cmd,
                "exit_code": rc_code,
                "success": ok,
            })

    elapsed = time.time() - t_start
    print()
    print("=" * 50)
    print("Overall: %s" % ("SUCCESS" if overall_success else "FAILED"))
    print("Steps executed: %d/%d" % (len(all_results), len(rb["steps"])))
    if rollback_results:
        print("Rollbacks: %d (all ok=%s)" % (len(rollback_results), all(r["success"] for r in rollback_results)))
    print("Elapsed: %.2fs" % elapsed)

    log_decision({
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": rb["metadata"].get("agent", "Builder"),
        "type": "playbook_complete",
        "runbook": str(rb_path),
        "title": rb["title"],
        "outcome": "success" if overall_success else "failed_at_step_%d" % failure_step,
        "steps_total": len(rb["steps"]),
        "steps_executed": len(all_results),
        "rollbacks": rollback_results,
        "elapsed_sec": round(elapsed, 2),
    })

    sys.exit(0 if overall_success else 1)


if __name__ == "__main__":
    main()
