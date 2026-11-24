"""cycle_transition_ops.py - Executes the infra side of cycle transition.

Pre-flight checks:
  - Disk space >100MB free on target volume
  - Archive directory exists and is writable
  - Goals file is readable

Transition steps:
  - Copy current goals file to archive/ with date stamp
  - Verify archive copy is valid (non-empty, valid text)
  - Write transition record to memory/ops/cycle-transitions.jsonl

Usage:
  python memory/mechanic/cycle_transition_ops.py --selftest
  python memory/mechanic/cycle_transition_ops.py --execute <cycle_name>
"""

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

MIN_DISK_FREE_MB = 100
ARCHIVE_DIR = Path("memory/goals/archive")
TRANSITION_LOG = Path("memory/ops/cycle-transitions.jsonl")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def check_disk_space(path: Path, min_free_mb: int = MIN_DISK_FREE_MB) -> dict:
    """Check available disk space at the given path.

    Returns {"ok": bool, "free_mb": float, "required_mb": int}
    """
    try:
        usage = shutil.disk_usage(str(path))
        free_mb = usage.free / (1024 * 1024)
        return {
            "ok": free_mb >= min_free_mb,
            "free_mb": round(free_mb, 1),
            "required_mb": min_free_mb,
        }
    except OSError as e:
        return {"ok": False, "free_mb": 0, "required_mb": min_free_mb, "error": str(e)}


def check_archive_writable(archive_dir: Path = ARCHIVE_DIR) -> dict:
    """Check that archive directory exists (or can be created) and is writable.

    Returns {"ok": bool, "path": str, "writable": bool}
    """
    try:
        archive_dir.mkdir(parents=True, exist_ok=True)
        # Test write by creating a temp file
        test_file = archive_dir / ".write_test"
        test_file.write_text("test", encoding="utf-8")
        test_file.unlink()
        return {"ok": True, "path": str(archive_dir), "writable": True}
    except OSError as e:
        return {"ok": False, "path": str(archive_dir), "writable": False, "error": str(e)}


def check_goals_readable(goals_file: Path) -> dict:
    """Check that goals file exists and is readable non-empty text.

    Returns {"ok": bool, "size_bytes": int, "lines": int}
    """
    try:
        if not goals_file.exists():
            return {"ok": False, "error": f"not found: {goals_file}", "size_bytes": 0, "lines": 0}
        content = goals_file.read_text(encoding="utf-8")
        if not content.strip():
            return {"ok": False, "error": "file is empty", "size_bytes": 0, "lines": 0}
        lines = len(content.splitlines())
        return {"ok": True, "size_bytes": len(content), "lines": lines}
    except (OSError, UnicodeDecodeError) as e:
        return {"ok": False, "error": str(e), "size_bytes": 0, "lines": 0}


def preflight(goals_file: Path = Path("memory/goals/mechanic.md"),
              archive_dir: Path = ARCHIVE_DIR) -> dict:
    """Run all pre-flight checks. Returns combined status.

    Returns {"ready": bool, "disk": dict, "archive": dict, "goals": dict}
    """
    disk = check_disk_space(goals_file.parent if goals_file.parent.exists() else Path("."))
    archive = check_archive_writable(archive_dir)
    goals = check_goals_readable(goals_file)

    ready = disk["ok"] and archive["ok"] and goals["ok"]
    return {"ready": ready, "disk": disk, "archive": archive, "goals": goals}


def execute_transition(cycle_name: str, goals_file: Path = Path("memory/goals/mechanic.md"),
                       archive_dir: Path = ARCHIVE_DIR) -> dict:
    """Execute cycle transition: archive current goals file.

    Steps:
      1. Run preflight
      2. If not ready, return failure
      3. Copy goals file to archive with date stamp
      4. Verify archive copy
      5. Log transition record

    Returns {"success": bool, "archive_path": str|None, "preflight": dict}
    """
    pre = preflight(goals_file, archive_dir)
    if not pre["ready"]:
        return {"success": False, "archive_path": None, "preflight": pre,
                "error": "preflight failed"}

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    stem = goals_file.stem  # e.g. "mechanic"
    archive_name = f"{stem}-{cycle_name}-{date_str}.md"
    archive_path = archive_dir / archive_name

    # Copy to archive
    try:
        shutil.copy2(str(goals_file), str(archive_path))
    except OSError as e:
        return {"success": False, "archive_path": None, "preflight": pre,
                "error": f"copy failed: {e}"}

    # Verify archive copy
    try:
        archived = archive_path.read_text(encoding="utf-8")
        if not archived.strip():
            raise ValueError("archived file is empty")
    except (OSError, UnicodeDecodeError) as e:
        return {"success": False, "archive_path": str(archive_path), "preflight": pre,
                "error": f"verify failed: {e}"}

    # Log transition
    record = {
        "timestamp": now_iso(),
        "cycle": cycle_name,
        "agent": stem,
        "source": str(goals_file),
        "archive": str(archive_path),
        "size_bytes": len(archived),
        "status": "success",
    }
    TRANSITION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(TRANSITION_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return {"success": True, "archive_path": str(archive_path), "preflight": pre}


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def selftest() -> bool:
    import shutil
    test_dir = Path("memory/mechanic/fixtures/cycle_transition_test")
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

    print("cycle_transition_ops.py selftest:")

    test_goals = test_dir / "mechanic.md"
    test_archive = test_dir / "archive"
    test_log = test_dir / "transitions.jsonl"

    # Write a fake goals file
    test_goals.write_text("# Test Goals\n1. Goal one\n2. Goal two\n", encoding="utf-8")

    # Test 1: Disk space check (should pass on any normal system)
    disk = check_disk_space(test_dir)
    check("disk space: ok=True", disk["ok"])
    check("disk space: free_mb > 0", disk["free_mb"] > 0)

    # Test 2: Archive writable
    arch = check_archive_writable(test_archive)
    check("archive: ok=True", arch["ok"])
    check("archive: writable=True", arch["writable"])
    check("archive: dir created", test_archive.exists())

    # Test 3: Goals readable
    goals = check_goals_readable(test_goals)
    check("goals: ok=True", goals["ok"])
    check("goals: has lines", goals["lines"] >= 2)
    check("goals: has size", goals["size_bytes"] > 0)

    # Test 4: Goals file missing
    missing = check_goals_readable(test_dir / "nonexistent.md")
    check("goals missing: ok=False", not missing["ok"])
    check("goals missing: error present", "error" in missing)

    # Test 5: Empty goals file
    empty_file = test_dir / "empty.md"
    empty_file.write_text("", encoding="utf-8")
    empty_check = check_goals_readable(empty_file)
    check("empty goals: ok=False", not empty_check["ok"])

    # Test 6: Preflight all pass
    pre = preflight(test_goals, test_archive)
    check("preflight: ready=True", pre["ready"])
    check("preflight: disk ok", pre["disk"]["ok"])
    check("preflight: archive ok", pre["archive"]["ok"])
    check("preflight: goals ok", pre["goals"]["ok"])

    # Test 7: Preflight fails with missing goals
    pre_fail = preflight(test_dir / "missing.md", test_archive)
    check("preflight fail: ready=False", not pre_fail["ready"])

    # Test 8: Execute transition
    global TRANSITION_LOG
    orig_log = TRANSITION_LOG
    TRANSITION_LOG = test_log

    result = execute_transition("cycle-15", test_goals, test_archive)
    check("execute: success=True", result["success"])
    check("execute: archive path set", result["archive_path"] is not None)

    if result["archive_path"]:
        ap = Path(result["archive_path"])
        check("execute: archive file exists", ap.exists())
        content = ap.read_text(encoding="utf-8")
        check("execute: archive has content", "Goal one" in content)

    # Test 9: Transition log written
    check("log file created", test_log.exists())
    with open(test_log) as f:
        entry = json.loads(f.readline())
    check("log has cycle field", entry["cycle"] == "cycle-15")
    check("log has status=success", entry["status"] == "success")
    check("log has archive path", "archive" in entry)

    # Test 10: Execute transition with missing goals fails
    result_fail = execute_transition("cycle-99", test_dir / "missing.md", test_archive)
    check("execute fail: success=False", not result_fail["success"])
    check("execute fail: error present", "error" in result_fail)

    # Test 11: Multiple transitions append to log
    TRANSITION_LOG = test_log
    result2 = execute_transition("cycle-16", test_goals, test_archive)
    check("second transition: success", result2["success"])
    with open(test_log) as f:
        lines = f.readlines()
    check("log has 2 entries", len(lines) == 2)

    TRANSITION_LOG = orig_log

    # Test 12: Disk space with impossibly high requirement fails
    disk_fail = check_disk_space(test_dir, min_free_mb=999_999_999)
    check("disk too low: ok=False", not disk_fail["ok"])

    # Cleanup
    shutil.rmtree(test_dir)

    print(f"\n  Result: {passed}/{passed+failed} passed")
    return failed == 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    elif "--execute" in sys.argv:
        idx = sys.argv.index("--execute")
        cycle_name = sys.argv[idx + 1]
        result = execute_transition(cycle_name)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["success"] else 1)
    elif "--preflight" in sys.argv:
        pre = preflight()
        print(json.dumps(pre, indent=2))
        sys.exit(0 if pre["ready"] else 1)
    else:
        print(__doc__)
        sys.exit(0)
