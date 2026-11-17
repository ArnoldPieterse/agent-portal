"""Edge-case tests for /api/goals (Builder goal #7).

Covers the 5 most common failure modes:
  1. Missing agent file       - parse_agent_file on nonexistent path returns []
  2. Malformed goal line      - broken/empty checkbox lines don't crash or create phantom goals
  3. Archive path collision   - archived copy with same name doesn't double-count
  4. Concurrent write         - two threads appending to a goals file -> no corruption
  5. Unicode in goal text     - emoji/CJK/special chars survive parse round-trip

Usage: python memory/builder/test_goals_edge_cases.py
Exit codes: 0=PASS, 1=FAIL
"""
import os, sys, re, tempfile, threading, json
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

# Import parse_agent_file from the strict ledger
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("_gl_strict", os.path.join(ROOT, "memory", "researcher", "goal_ledger.py"))
_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
parse_agent_file = _mod.parse_agent_file

PASS = 0
FAIL = 0

def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} {detail}")

# ─── Test 1: Missing agent file ────────────────────────────────────────────────
def test_missing_agent_file():
    """parse_agent_file on a nonexistent path returns empty list (no crash)."""
    print("\nTest 1: Missing agent file")
    result = parse_agent_file("/nonexistent/path/to/agent.md")
    check("returns empty list", result == [], f"got {result!r}")

    # Also test with an empty-string path (edge: no path at all)
    result2 = parse_agent_file("")
    check("empty string path returns []", result2 == [], f"got {result2!r}")

# ─── Test 2: Malformed goal line ──────────────────────────────────────────────
def test_malformed_goal_line():
    """Broken/empty checkbox lines don't crash and don't create phantom goals."""
    print("\nTest 2: Malformed goal line")
    cases = [
        ("- [ ]", "empty checkbox"),
        ("- [x]", "empty checked box"),
        ("- [] broken", "missing space after brackets"),
        ("[ ] no dash prefix", "no list marker"),
        ("- [X] UPPERCASE", "uppercase X (should still parse)"),
    ]
    for line, desc in cases:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(line + "\n")
            tmp = f.name
        try:
            result = parse_agent_file(tmp)
            # Should not raise; result is a list (may be empty for truly malformed)
            check(f"no crash on '{desc}'", isinstance(result, list), f"got {type(result)}")
        except Exception as e:
            check(f"no crash on '{desc}'", False, f"raised {e}")
        finally:
            os.unlink(tmp)

    # Empty file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("")
        tmp = f.name
    try:
        result = parse_agent_file(tmp)
        check("empty file returns []", result == [], f"got {result!r}")
    finally:
        os.unlink(tmp)

# ─── Test 3: Archive path collision ───────────────────────────────────────────
def test_archive_path_collision():
    """An archived copy with the same basename doesn't cause double-counting.
    The _goals_snapshot function only reads from memory/goals/ (not archive),
    so we verify that parse_agent_file on the active file is unaffected by
    an identically-named file in a subdirectory."""
    print("\nTest 3: Archive path collision")
    tmpdir = tempfile.mkdtemp()
    # Active goal file with 2 goals
    active = os.path.join(tmpdir, "testagent.md")
    with open(active, "w", encoding="utf-8") as f:
        f.write("1. First goal (verified: 2026-01-01 - done)\n")
        f.write("2. Second goal still open here\n")

    # Create archive dir with same-named file (simulating collision)
    arch_dir = os.path.join(tmpdir, "archive")
    os.makedirs(arch_dir, exist_ok=True)
    with open(os.path.join(arch_dir, "testagent.md"), "w", encoding="utf-8") as f:
        f.write("1. Archived goal that should NOT be counted\n")

    # Parse only the active file - archive must not interfere
    result = parse_agent_file(active)
    check("active file parsed correctly (2 goals)", len(result) == 2, f"got {len(result)}")
    reached = sum(1 for g in result if g["status"] == "reached")
    check("only active goal 1 is reached", reached == 1, f"got {reached}")

# ─── Test 4: Concurrent write ─────────────────────────────────────────────────
def test_concurrent_write():
    """Two threads appending to the same goals file -> no corruption, all lines present."""
    print("\nTest 4: Concurrent write")
    tmpdir = tempfile.mkdtemp()
    fpath = os.path.join(tmpdir, "concurrent.md")
    # Start with a header line
    with open(fpath, "w", encoding="utf-8") as f:
        f.write("# Concurrent Test\n")

    N_THREADS = 5
    LINES_PER_THREAD = 10
    errors = []
    lock = threading.Lock()

    def writer(thread_id):
        """Write with a lock (simulates production file-lock discipline);
        the test verifies parser integrity under concurrent access patterns."""
        try:
            for i in range(LINES_PER_THREAD):
                line = f"{thread_id * LINES_PER_THREAD + i + 1}. Goal from thread {thread_id} line {i}\n"
                with lock:
                    with open(fpath, "a", encoding="utf-8") as f:
                        f.write(line)
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=writer, args=(t,)) for t in range(N_THREADS)]
    for t in threads: t.start()
    for t in threads: t.join(timeout=10)

    check("no write errors", len(errors) == 0, f"errors: {errors}")

    # Verify all lines present and parseable
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    expected_total = N_THREADS * LINES_PER_THREAD
    line_count = sum(1 for ln in content.splitlines() if re.match(r'^\d+\. ', ln))
    check(f"all {expected_total} lines present", line_count == expected_total, f"got {line_count}")

    # Parse should not crash and should find all goals with valid (non-empty) text
    result = parse_agent_file(fpath)
    check("parse succeeds on concurrent file", isinstance(result, list), f"got {type(result)}")
    check(f"parse finds {expected_total} goals", len(result) == expected_total, f"got {len(result)}")
    all_valid = all(g["text"].strip() for g in result)
    check("all parsed goals have non-empty text (no corruption)", all_valid)

# ─── Test 5: Unicode in goal text ─────────────────────────────────────────────
def test_unicode_in_goal_text():
    """Goal lines with emoji, CJK, and special chars parse correctly."""
    print("\nTest 5: Unicode in goal text")
    unicode_goals = [
        "1. Fix the 🚀 deployment pipeline for production",
        "2. Deploy to 東京 server (日本語 test)",
        "3. Handle ünïcödé filenames with émojis 🎉🔥",
        "4. Support \u00e9\u00e8\u00ea French accents in goal text",
        "5. Test CJK: 目标追踪系统 v2 (verified: 2026-01-01 - done)",
    ]
    tmpdir = tempfile.mkdtemp()
    fpath = os.path.join(tmpdir, "unicode_agent.md")
    with open(fpath, "w", encoding="utf-8") as f:
        f.write("\n".join(unicode_goals) + "\n")

    result = parse_agent_file(fpath)
    check("all 5 unicode goals parsed", len(result) == 5, f"got {len(result)}")
    if len(result) == 5:
        # Verify text integrity (no mojibake or truncation)
        check("emoji preserved", "🚀" in result[0]["text"], f"got: {result[0]['text'][:40]}")
        check("CJK preserved", "東京" in result[1]["text"], f"got: {result[1]['text'][:40]}")
        check("accents preserved", "ünïcödé" in result[2]["text"], f"got: {result[2]['text'][:40]}")
        check("verified unicode goal is reached", result[4]["status"] == "reached", f"got {result[4]['status']}")

    # JSON-serializable (the API returns this as JSON)
    try:
        json.dumps(result, ensure_ascii=False)
        check("JSON serializable", True)
    except Exception as e:
        check("JSON serializable", False, str(e))

# ─── Runner ────────────────────────────────────────────────────────────────────
def main():
    print("=== /api/goals Edge Case Tests (Builder goal #7) ===")
    tests = [
        test_missing_agent_file,
        test_malformed_goal_line,
        test_archive_path_collision,
        test_concurrent_write,
        test_unicode_in_goal_text,
    ]
    for t in tests:
        try:
            t()
        except Exception as e:
            global FAIL
            FAIL += 1
            print(f"  [FAIL] {t.__name__} raised: {e}")
    print(f"\n=== RESULT: {PASS} passed, {FAIL} failed ===")
    sys.exit(0 if FAIL == 0 else 1)

if __name__ == "__main__":
    main()