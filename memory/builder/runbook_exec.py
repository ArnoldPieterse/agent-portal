"""Runbook Parser + Executor (Builder Goal #9).

Parses markdown runbooks from memory/ops/runbooks/*.md into structured steps,
executes them sequentially with verification, and rolls back on failure.

Usage:
  python memory/builder/runbook_exec.py <runbook.md>           # execute
  python memory/builder/runbook_exec.py <runbook.md> --dry-run # parse only
  python memory/builder/runbook_exec.py <runbook.md> --simulate-failure N  # inject failure at step N
"""

import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

RUNBOOKS_DIR = Path("memory/ops/runbooks")
DECISION_LOG = Path("memory/decision-log.jsonl")


@dataclass
class Step:
    number: int
    title: str
    command: str
    expected: str  # "exit_code:0" or literal string to match in stdout
    timeout: int = 30
    rollback_command: Optional[str] = None
    result: Optional[dict] = None


@dataclass
class Runbook:
    name: str
    agent: str
    trigger: str
    rollback_on_failure: bool
    steps: list = field(default_factory=list)

    def to_dict(self):
        return {
            "name": self.name,
            "agent": self.agent,
            "trigger": self.trigger,
            "rollback_on_failure": self.rollback_on_failure,
            "steps": [
                {
                    "number": s.number,
                    "title": s.title,
                    "command": s.command,
                    "expected": s.expected,
                    "timeout": s.timeout,
                    "rollback_command": s.rollback_command,
                }
                for s in self.steps
            ],
        }


def parse_runbook(path: Path) -> Runbook:
    """Parse a markdown runbook into a structured Runbook object."""
    text = path.read_text(encoding="utf-8")

    # Extract metadata
    agent = "unknown"
    trigger = "manual"
    rollback_on_failure = False

    meta_match = re.search(r"## Metadata\n(.*?)(?=\n## )", text, re.DOTALL)
    if meta_match:
        meta_block = meta_match.group(1)
        m = re.search(r"- agent:\s*(.+)", meta_block)
        if m:
            agent = m.group(1).strip()
        m = re.search(r"- trigger:\s*(.+)", meta_block)
        if m:
            trigger = m.group(1).strip()
        m = re.search(r"- rollback_on_failure:\s*(true|false)", meta_block)
        if m:
            rollback_on_failure = m.group(1) == "true"

    # Extract steps
    steps = []
    step_pattern = re.compile(
        r"### Step (\d+): (.+)\n((?:- .+\n?)+)",
        re.MULTILINE,
    )
    for match in step_pattern.finditer(text):
        num = int(match.group(1))
        title = match.group(2).strip()
        body = match.group(3)

        cmd = _extract_field(body, "command")
        expected = _extract_field(body, "expected", default="exit_code:0")
        timeout_m = re.search(r"- timeout:\s*(\d+)", body)
        timeout = int(timeout_m.group(1)) if timeout_m else 30
        rollback_cmd = _extract_field(body, "rollback_command")

        steps.append(Step(num, title, cmd, expected, timeout, rollback_cmd))

    name = path.stem.replace("_", " ").title()
    return Runbook(name, agent, trigger, rollback_on_failure, steps)


def _extract_field(body: str, field_name: str, default: Optional[str] = None) -> Optional[str]:
    """Extract a backtick-wrapped or plain value from a step body."""
    # Try backtick first
    pattern = rf"- {field_name}:\s*`([^`]+)`"
    m = re.search(pattern, body)
    if m:
        return m.group(1).strip()
    # Plain (e.g., expected: exit_code:0)
    pattern_plain = rf"- {field_name}:\s*(.+)"
    m = re.search(pattern_plain, body)
    if m:
        return m.group(1).strip()
    return default


def execute_step(step: Step, dry_run: bool = False) -> dict:
    """Execute a single step and return its result dict."""
    if dry_run:
        return {"status": "dry-run", "command": step.command, "ok": True}

    start = time.time()
    try:
        proc = subprocess.run(
            step.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=step.timeout,
        )
        elapsed = time.time() - start
        stdout = proc.stdout.strip()
        returncode = proc.returncode

        # Verify expected output
        if step.expected.startswith("exit_code:"):
            expected_code = int(step.expected.split(":")[1])
            ok = (returncode == expected_code)
        else:
            ok = step.expected in stdout or step.expected in (proc.stderr or "")

        result = {
            "status": "ok" if ok else "failed",
            "command": step.command,
            "exit_code": returncode,
            "stdout": stdout[:500],
            "elapsed": round(elapsed, 3),
            "ok": ok,
        }
    except subprocess.TimeoutExpired:
        result = {
            "status": "timeout",
            "command": step.command,
            "elapsed": step.timeout,
            "ok": False,
        }
    except Exception as e:
        result = {
            "status": "error",
            "command": step.command,
            "error": str(e),
            "ok": False,
        }

    step.result = result
    return result


def rollback(runbook: Runbook, failed_step_num: int) -> list:
    """Roll back steps 1..failed_step-1 in reverse order."""
    actions = []
    for step in reversed(runbook.steps[: failed_step_num - 1]):
        if not step.rollback_command:
            continue
        try:
            proc = subprocess.run(
                step.rollback_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=15,
            )
            actions.append({
                "step": step.number,
                "rollback_command": step.rollback_command,
                "exit_code": proc.returncode,
                "ok": proc.returncode == 0,
            })
        except Exception as e:
            actions.append({
                "step": step.number,
                "rollback_command": step.rollback_command,
                "error": str(e),
                "ok": False,
            })
    return actions


def log_decision(entry: dict):
    """Append to decision-log.jsonl."""
    entry["timestamp"] = datetime.now().isoformat()
    DECISION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(DECISION_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def run(runbook_path: Path, dry_run: bool = False, simulate_failure_at: Optional[int] = None) -> dict:
    """Execute a full runbook. Returns report dict."""
    rb = parse_runbook(runbook_path)

    if dry_run:
        print(f"[DRY-RUN] Parsed: {rb.name}")
        print(f"  Agent: {rb.agent}, Trigger: {rb.trigger}, Rollback: {rb.rollback_on_failure}")
        for s in rb.steps:
            print(f"  Step {s.number}: {s.title} -> {s.command[:60]}...")
            print(f"    expected={s.expected}, timeout={s.timeout}s, rollback={'yes' if s.rollback_command else 'no'}")
        return {"name": rb.name, "mode": "dry-run", "steps_parsed": len(rb.steps), "ok": True}

    report = {
        "name": rb.name,
        "agent": rb.agent,
        "trigger": rb.trigger,
        "started": datetime.now().isoformat(),
        "steps": [],
        "rollback_actions": [],
        "overall_ok": True,
    }

    for i, step in enumerate(rb.steps):
        # Simulate failure at specified step
        if simulate_failure_at is not None and step.number == simulate_failure_at:
            step.result = {"status": "simulated-failure", "command": step.command, "ok": False}
            report["steps"].append({"step": step.number, "title": step.title, **step.result})
            print(f"  [{i+1}/{len(rb.steps)}] Step {step.number}: SIMULATED FAILURE")
        else:
            result = execute_step(step)
            report["steps"].append({"step": step.number, "title": step.title, **result})
            status_icon = "OK" if result["ok"] else "FAIL"
            print(f"  [{i+1}/{len(rb.steps)}] Step {step.number}: {status_icon} ({result['elapsed']}s)")

        # If failed, stop and rollback
        if not step.result["ok"]:
            report["overall_ok"] = False
            report["failed_at_step"] = step.number
            print(f"  !! Failure at step {step.number}. Rolling back...")
            if rb.rollback_on_failure:
                report["rollback_actions"] = rollback(rb, step.number)
                for ra in report["rollback_actions"]:
                    print(f"    Rollback step {ra['step']}: {'OK' if ra['ok'] else 'FAIL'}")
            break

    report["finished"] = datetime.now().isoformat()
    duration = (datetime.fromisoformat(report["finished"]) - datetime.fromisoformat(report["started"])).total_seconds()
    report["duration_s"] = round(duration, 3)

    # Log to decision-log
    log_decision({
        "type": "runbook_execution",
        "agent": rb.agent,
        "runbook": rb.name,
        "overall_ok": report["overall_ok"],
        "steps_completed": len([s for s in report["steps"] if s.get("ok")]),
        "steps_total": len(rb.steps),
        "rolled_back": bool(report["rollback_actions"]),
        "duration_s": report["duration_s"],
    })

    return report


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Runbook Parser + Executor")
    ap.add_argument("runbook", help="Path to runbook .md file")
    ap.add_argument("--dry-run", action="store_true", help="Parse only, don't execute")
    ap.add_argument("--simulate-failure", type=int, metavar="N", help="Inject failure at step N (for testing rollback)")
    args = ap.parse_args()

    path = Path(args.runbook)
    if not path.exists():
        print(f"ERROR: {path} not found")
        sys.exit(1)

    report = run(path, dry_run=args.dry_run, simulate_failure_at=args.simulate_failure)

    if args.dry_run:
        print(f"\nParsed {report['steps_parsed']} steps successfully.")
        sys.exit(0)
    else:
        print(f"\n{'SUCCESS' if report['overall_ok'] else 'FAILED'} in {report['duration_s']}s")
        print(json.dumps(report, indent=2))
        sys.exit(0 if report["overall_ok"] else 1)


if __name__ == "__main__":
    main()
