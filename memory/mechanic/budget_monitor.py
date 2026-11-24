"""budget_monitor.py - Monitors pass-budget.json and writes alerts when consumption >80%.

Reads pass-budget.json (expected schema: {"budget": int, "used": int, "cycle": str})
When used/budget > 0.80, writes a warning to memory/ops/budget-alert.md with:
  - current usage (used/budget)
  - projected exhaustion pass number
  - remaining passes

Usage:
  python memory/mechanic/budget_monitor.py --selftest
  python memory/mechanic/budget_monitor.py --check   # run one check cycle
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BUDGET_PATH = Path("memory/ops/pass-budget.json")
ALERT_PATH = Path("memory/ops/budget-alert.md")
THRESHOLD = 0.80


def read_budget(path: Path = BUDGET_PATH) -> dict:
    """Read and validate pass-budget.json."""
    if not path.exists():
        raise FileNotFoundError(f"pass-budget.json not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Validate required fields
    for field in ("budget", "used"):
        if field not in data:
            raise ValueError(f"pass-budget.json missing field: {field}")
    if not isinstance(data["budget"], int) or data["budget"] <= 0:
        raise ValueError(f"budget must be positive int, got {data['budget']!r}")
    if not isinstance(data["used"], int) or data["used"] < 0:
        raise ValueError(f"used must be non-negative int, got {data['used']!r}")
    return data


def check_budget(budget_data: dict) -> dict:
    """Check budget consumption. Returns status dict.

    Returns:
        {"alert": bool, "pct": float, "remaining": int, "projected_exhaustion_pass": int}
    """
    budget = budget_data["budget"]
    used = budget_data["used"]
    pct = used / budget if budget > 0 else 1.0
    remaining = max(0, budget - used)
    projected_exhaustion = used + remaining  # = budget (when to hit 100%)

    return {
        "alert": pct > THRESHOLD,
        "pct": round(pct * 100, 1),
        "remaining": remaining,
        "projected_exhaustion_pass": projected_exhaustion,
        "budget": budget,
        "used": used,
    }


def write_alert(status: dict, cycle: str = "") -> Path:
    """Write budget alert to memory/ops/budget-alert.md. Returns path."""
    ALERT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        f"# BUDGET ALERT - {ts}",
        "",
        f"- **Cycle:** {cycle or 'unknown'}",
        f"- **Usage:** {status['used']}/{status['budget']} ({status['pct']}%)",
        f"- **Remaining:** {status['remaining']} passes",
        f"- **Projected exhaustion:** pass {status['projected_exhaustion_pass']}",
        f"- **Threshold:** {THRESHOLD*100:.0f}%",
        "",
        "## Action Required",
        "- Reduce per-pass scope or extend budget before exhaustion.",
        "- Consider deferring low-priority goals to next cycle.",
        "",
    ]
    ALERT_PATH.write_text("\n".join(lines), encoding="utf-8")
    return ALERT_PATH


def run_check(budget_path: Path = BUDGET_PATH) -> dict:
    """Run one budget check cycle. Returns status dict."""
    data = read_budget(budget_path)
    status = check_budget(data)
    if status["alert"]:
        write_alert(status, data.get("cycle", ""))
        status["alert_written"] = True
    else:
        status["alert_written"] = False
    return status


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def selftest() -> bool:
    """Comprehensive self-test with temp files."""
    import shutil
    test_dir = Path("memory/mechanic/fixtures/budget_monitor_test")
    test_dir.mkdir(parents=True, exist_ok=True)

    passed = 0
    failed = 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  PASS: {name}")
        else:
            failed += 1
            print(f"  FAIL: {name}")

    print("budget_monitor.py selftest:")

    test_budget = test_dir / "pass-budget.json"
    test_alert = test_dir / "budget-alert.md"

    # Test 1: Below threshold - no alert
    test_budget.write_text(json.dumps({"budget": 200, "used": 50, "cycle": "cycle-15"}))
    status = check_budget(read_budget(test_budget))
    check("below threshold: no alert", not status["alert"])
    check("below threshold: pct correct", status["pct"] == 25.0)
    check("below threshold: remaining correct", status["remaining"] == 150)

    # Test 2: At exactly 80% - no alert (threshold is >80%)
    test_budget.write_text(json.dumps({"budget": 200, "used": 160, "cycle": "cycle-15"}))
    status = check_budget(read_budget(test_budget))
    check("at 80%: no alert (strictly greater)", not status["alert"])

    # Test 3: Above threshold - alert triggered
    test_budget.write_text(json.dumps({"budget": 200, "used": 161, "cycle": "cycle-15"}))
    status = check_budget(read_budget(test_budget))
    check("above threshold: alert", status["alert"])
    check("above threshold: pct correct", status["pct"] == 80.5)
    check("above threshold: remaining correct", status["remaining"] == 39)

    # Test 4: Write alert file
    test_budget.write_text(json.dumps({"budget": 200, "used": 180, "cycle": "cycle-15"}))
    data = read_budget(test_budget)
    status = check_budget(data)
    if status["alert"]:
        # Write to test location
        global ALERT_PATH
        orig_alert = ALERT_PATH
        ALERT_PATH = test_alert
        write_alert(status, data.get("cycle", ""))
        ALERT_PATH = orig_alert
        check("alert file written", test_alert.exists())
        content = test_alert.read_text()
        check("alert has usage info", "180/200" in content)
        check("alert has remaining", "Remaining" in content)
        check("alert has projected exhaustion", "Projected exhaustion" in content)

    # Test 5: 100% consumption
    test_budget.write_text(json.dumps({"budget": 100, "used": 100}))
    status = check_budget(read_budget(test_budget))
    check("100%: alert", status["alert"])
    check("100%: remaining 0", status["remaining"] == 0)

    # Test 6: Missing file raises error
    try:
        read_budget(test_dir / "nonexistent.json")
        check("missing file raises", False)
    except FileNotFoundError:
        check("missing file raises", True)

    # Test 7: Invalid budget (zero) raises error
    test_budget.write_text(json.dumps({"budget": 0, "used": 0}))
    try:
        read_budget(test_budget)
        check("budget=0 raises", False)
    except ValueError:
        check("budget=0 raises", True)

    # Test 8: Invalid used (negative) raises error
    test_budget.write_text(json.dumps({"budget": 100, "used": -5}))
    try:
        read_budget(test_budget)
        check("used<0 raises", False)
    except ValueError:
        check("used<0 raises", True)

    # Test 9: Missing field raises error
    test_budget.write_text(json.dumps({"budget": 100}))
    try:
        read_budget(test_budget)
        check("missing used field raises", False)
    except ValueError:
        check("missing used field raises", True)

    # Test 10: Edge case - budget=1, used=0
    test_budget.write_text(json.dumps({"budget": 1, "used": 0}))
    status = check_budget(read_budget(test_budget))
    check("budget=1 used=0: no alert", not status["alert"])

    # Test 11: Edge case - budget=1, used=1
    test_budget.write_text(json.dumps({"budget": 1, "used": 1}))
    status = check_budget(read_budget(test_budget))
    check("budget=1 used=1: alert", status["alert"])

    # Test 12: run_check integration (uses temp path)
    test_budget.write_text(json.dumps({"budget": 200, "used": 190, "cycle": "test-cycle"}))
    orig_alert = ALERT_PATH
    ALERT_PATH = test_alert
    status = run_check(test_budget)
    ALERT_PATH = orig_alert
    check("run_check: alert triggered at 95%", status["alert"])
    check("run_check: alert_written flag", status.get("alert_written") == True)

    # Cleanup
    shutil.rmtree(test_dir)

    print(f"\n  Result: {passed}/{passed+failed} passed")
    return failed == 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    elif "--check" in sys.argv:
        status = run_check()
        print(json.dumps(status, indent=2))
        sys.exit(0)
    else:
        print(__doc__)
        sys.exit(0)
