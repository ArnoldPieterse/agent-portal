#!/usr/bin/env python3
"""
maintenance_registry.py — Builder's maintenance task registry (cycle 15, goal #8)

Validates memory/ops/maintenance-tasks.json and provides rotation function.

Usage:
  python memory/builder/maintenance_registry.py            # validate + report
  python memory/builder/maintenance_registry.py --rotate <role> <day>  # get task for role on day N
  python memory/builder/maintenance_registry.py --selftest  # acceptance tests
"""
import json, sys, pathlib, datetime

REGISTRY = pathlib.Path("memory/ops/maintenance-tasks.json")
ROLES = ["orchestrator", "researcher", "builder", "archivist", "scribe", "verifier", "mechanic", "designer"]


def load_registry():
    if not REGISTRY.exists():
        raise FileNotFoundError(f"Registry not found: {REGISTRY}")
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def validate(reg):
    """Validate registry structure. Returns (ok, errors)."""
    errors = []
    roles = reg.get("roles", {})

    for role in ROLES:
        if role not in roles:
            errors.append(f"missing role: {role}")
            continue
        task_list = roles[role]
        if len(task_list) < 5:
            errors.append(f"{role} has only {len(task_list)} tasks (need >=5)")

    all_ids = []
    for role, task_list in roles.items():
        for t in task_list:
            tid = t.get("id")
            if not tid:
                errors.append(f"{role}: task missing id")
            elif tid in all_ids:
                errors.append(f"duplicate task id: {tid}")
            else:
                all_ids.append(tid)

    for role, task_list in roles.items():
        for t in task_list:
            for field in ("id", "description", "command", "expected_output"):
                if field not in t or not str(t[field]).strip():
                    errors.append(f"{role}/{t.get('id','?')}: missing/empty field '{field}'")

    return len(errors) == 0, errors


def rotate(role: str, day: int):
    """Return the task for a role on a given day of cycle (0-indexed)."""
    reg = load_registry()
    tasks = reg["roles"][role]
    idx = day % len(tasks)
    return tasks[idx]


def selftest():
    results = []

    # Test 1: registry loads
    try:
        reg = load_registry()
        results.append(("Test 1: registry loads", True, ""))
    except Exception as e:
        results.append(("Test 1: registry loads", False, str(e)))
        print(f"\n  RESULT: 0/{len(results)} PASS (fatal)")
        return False

    # Test 2: validation passes
    ok, errors = validate(reg)
    results.append(("Test 2: validation (8 roles, >=5 tasks, unique IDs, all fields)", ok,
                    "; ".join(errors[:3]) if errors else ""))

    # Test 3: rotation returns correct task for day 0-4
    tasks = reg["roles"]["builder"]
    rot_ok = all(rotate("builder", d)["id"] == tasks[d % len(tasks)]["id"] for d in range(5))
    results.append(("Test 3: rotation day 0-4 correct", rot_ok, ""))

    # Test 4: rotation wraps (day 5 == day 0)
    wrap_ok = rotate("builder", 5)["id"] == rotate("builder", 0)["id"]
    results.append(("Test 4: rotation wraps around", wrap_ok, ""))

    # Test 5: >=40 total tasks with unique IDs
    all_ids = [t["id"] for ts in reg["roles"].values() for t in ts]
    count_ok = len(all_ids) >= 40 and len(set(all_ids)) == len(all_ids)
    results.append(("Test 5: >=40 unique task IDs", count_ok, f"count={len(all_ids)}"))

    # Test 6: all roles rotatable (day 3)
    all_rot = True
    for role in ROLES:
        try:
            rotate(role, 3)
        except Exception:
            all_rot = False
            break
    results.append(("Test 6: all 8 roles rotatable", all_rot, ""))

    # Test 7: non-empty commands for all tasks
    cmd_ok = all(t.get("command", "").strip() for ts in reg["roles"].values() for t in ts)
    results.append(("Test 7: all commands non-empty", cmd_ok, ""))

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    for name, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        suffix = f" ({detail})" if detail and not ok else ""
        print(f"  [{status}] {name}{suffix}")

    print(f"\n  RESULT: {passed}/{total} PASS")
    return passed == total


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    elif "--rotate" in sys.argv:
        idx = sys.argv.index("--rotate")
        role = sys.argv[idx + 1]
        day = int(sys.argv[idx + 2])
        task = rotate(role, day)
        print(json.dumps(task, indent=2))
    else:
        reg = load_registry()
        ok, errors = validate(reg)
        total_tasks = sum(len(v) for v in reg["roles"].values())
        print(f"Registry: {len(reg['roles'])} roles, {total_tasks} tasks")
        print(f"Validation: {'PASS' if ok else 'FAIL'}")
        if errors:
            for e in errors:
                print(f"  {e}")
        sys.exit(0 if ok else 1)
