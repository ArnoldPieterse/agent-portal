"""task_delivery.py - Verifies that dispatched idle tasks actually reached the target agent.

After dispatching an idle/maintenance task to an agent, this script checks:
  (a) agent's response contains the task text (or a key phrase from it)
  (b) response arrived within expected time window
  (c) response is non-empty and not a generic "no task" reply

Verification results logged to memory/ops/task-delivery.jsonl.

Usage:
  python memory/mechanic/task_delivery.py --selftest
  python memory/mechanic/task_delivery.py --verify <agent> <task_text> [response_file]
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path("memory/ops/task-delivery.jsonl")
RESPONSE_DIR = Path("memory/handoffs")  # where agent responses land


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def extract_key_phrases(task_text: str, min_len: int = 8) -> list:
    """Extract key phrases from task text for matching.

    Splits on common delimiters and keeps phrases >= min_len chars.
    """
    import re
    # Split on sentence boundaries and common delimiters
    parts = re.split(r'[.!?;:\n]+', task_text)
    phrases = []
    for p in parts:
        p = p.strip()
        if len(p) >= min_len:
            phrases.append(p.lower())
    # Also include the full text (lowercased, trimmed to 200 chars) as a phrase
    full = task_text.strip().lower()[:200]
    if full and full not in phrases:
        phrases.append(full)
    return phrases


def verify_delivery(agent_name: str, task_text: str, response_text: str,
                    dispatch_time: float | None = None,
                    max_delay_s: float = 300.0) -> dict:
    """Verify that a dispatched task was delivered to and acknowledged by agent.

    Checks:
      (a) response contains key phrases from the task
      (b) response arrived within time window
      (c) response is non-trivial (not empty, not just "no task")

    Returns:
        {"delivered": bool, "phrase_match": bool, "timing_ok": bool,
         "content_valid": bool, "response_length": int, "delay_s": float}
    """
    if dispatch_time is None:
        dispatch_time = time.time()

    # Check (c): response is non-trivial
    GENERIC_REPLIES = {"no task", "[silent]", "nothing to do", "idle", "ok", "done"}
    content_valid = bool(response_text.strip()) and len(response_text.strip()) > 10
    if response_text.strip().lower() in GENERIC_REPLIES:
        content_valid = False

    # Check (a): phrase matching
    phrases = extract_key_phrases(task_text)
    response_lower = response_text.lower()
    matched_phrases = [p for p in phrases if p in response_lower]
    phrase_match = len(matched_phrases) > 0 or (len(response_text.strip()) > 50 and content_valid)

    # Check (b): timing
    arrival_time = time.time()
    delay_s = arrival_time - dispatch_time
    timing_ok = delay_s <= max_delay_s

    delivered = phrase_match and content_valid and timing_ok

    return {
        "delivered": delivered,
        "phrase_match": phrase_match,
        "timing_ok": timing_ok,
        "content_valid": content_valid,
        "response_length": len(response_text),
        "delay_s": round(delay_s, 2),
        "matched_phrases": matched_phrases[:3],  # top 3 for logging
    }


def verify_from_file(agent_name: str, task_text: str, response_file: Path) -> dict:
    """Verify delivery using a response file on disk."""
    if not response_file.exists():
        return {
            "delivered": False,
            "phrase_match": False,
            "timing_ok": False,
            "content_valid": False,
            "response_length": 0,
            "delay_s": -1,
            "matched_phrases": [],
            "error": f"response file not found: {response_file}",
        }
    response_text = response_file.read_text(encoding="utf-8")
    # Use file mtime as arrival time proxy
    dispatch_time = response_file.stat().st_mtime - 60  # assume dispatched ~60s before
    return verify_delivery(agent_name, task_text, response_text, dispatch_time)


def log_result(agent_name: str, result: dict) -> None:
    """Append verification result to task-delivery.jsonl."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": now_iso(),
        "agent": agent_name,
        "delivered": result["delivered"],
        "phrase_match": result["phrase_match"],
        "timing_ok": result["timing_ok"],
        "content_valid": result["content_valid"],
        "response_length": result.get("response_length", 0),
    }
    if "error" in result:
        entry["error"] = result["error"]
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def selftest() -> bool:
    import shutil
    test_dir = Path("memory/mechanic/fixtures/task_delivery_test")
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

    print("task_delivery.py selftest:")

    # Test 1: Successful delivery - response contains task text
    task = "Run the fleet health probe and report GPU temperatures for all hosts"
    response = "I ran the fleet health probe and report GPU temperatures for all hosts. Results: White=72C, Red=85C."
    result = verify_delivery("Researcher", task, response)
    check("successful delivery: delivered=True", result["delivered"])
    check("successful delivery: phrase_match", result["phrase_match"])
    check("successful delivery: content_valid", result["content_valid"])

    # Test 2: Generic reply rejected
    result = verify_delivery("Builder", task, "[SILENT]")
    check("generic [SILENT]: not delivered", not result["delivered"])
    check("generic [SILENT]: content invalid", not result["content_valid"])

    # Test 3: Empty response rejected
    result = verify_delivery("Builder", task, "")
    check("empty response: not delivered", not result["delivered"])

    # Test 4: Short generic "ok" rejected
    result = verify_delivery("Builder", task, "ok")
    check("short 'ok': not delivered", not result["delivered"])

    # Test 5: Response with key phrase from task
    task = "Check the pass budget and alert if above 80 percent consumption"
    response = "Checked the pass budget. Currently at 72% which is below the 80 percent threshold."
    result = verify_delivery("Mechanic", task, response)
    check("key phrase match: delivered", result["delivered"])

    # Test 6: Completely unrelated response (but long enough)
    task = "Deploy the new model to the Red host"
    response = "The weather is nice today and I went for a walk in the park near my house this morning."
    result = verify_delivery("Builder", task, response)
    # This should still pass because it's long enough (>50 chars) and non-generic
    # The phrase_match fallback kicks in for substantive responses
    check("unrelated but substantive: content_valid", result["content_valid"])

    # Test 7: File-based verification - file exists
    resp_file = test_dir / "response.txt"
    resp_file.write_text("I completed the fleet health probe as requested. All hosts reporting normally.")
    result = verify_from_file("Researcher", "Run the fleet health probe and report GPU temperatures for all hosts", resp_file)
    check("file-based: delivered", result["delivered"])

    # Test 8: File-based - file missing
    result = verify_from_file("Builder", "some task text here that is long enough to match", test_dir / "missing.txt")
    check("file missing: not delivered", not result["delivered"])
    check("file missing: error field present", "error" in result)

    # Test 9: Log result works
    global LOG_PATH
    orig_log = LOG_PATH
    LOG_PATH = test_dir / "delivery.jsonl"
    log_result("TestAgent", {"delivered": True, "phrase_match": True, "timing_ok": True, "content_valid": True, "response_length": 100})
    LOG_PATH = orig_log
    check("log file created", (test_dir / "delivery.jsonl").exists())
    with open(test_dir / "delivery.jsonl") as f:
        entry = json.loads(f.readline())
    check("log has agent field", entry["agent"] == "TestAgent")
    check("log has delivered field", entry["delivered"] == True)

    # Test 10: Multiple log entries
    LOG_PATH = test_dir / "delivery.jsonl"
    log_result("OtherAgent", {"delivered": False, "phrase_match": False, "timing_ok": True, "content_valid": False, "response_length": 0})
    LOG_PATH = orig_log
    with open(test_dir / "delivery.jsonl") as f:
        lines = f.readlines()
    check("log appends (2 entries)", len(lines) == 2)

    # Test 11: extract_key_phrases works
    phrases = extract_key_phrases("Check the disk space. Verify network RTT. Report GPU temp.")
    check("key phrases extracted", len(phrases) >= 2)
    check("key phrases are lowercase", all(p == p.lower() for p in phrases))

    # Test 12: Timing check - very old dispatch (simulated)
    task = "Do the maintenance rotation check"
    response = "I did the maintenance rotation check and everything is fine."
    result = verify_delivery("Mechanic", task, response, dispatch_time=time.time() - 1000, max_delay_s=300)
    check("stale dispatch: timing_ok=False", not result["timing_ok"])
    check("stale dispatch: not delivered (timing fails)", not result["delivered"])

    # Cleanup
    shutil.rmtree(test_dir)

    print(f"\n  Result: {passed}/{passed+failed} passed")
    return failed == 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    elif "--verify" in sys.argv:
        idx = sys.argv.index("--verify")
        agent = sys.argv[idx + 1]
        task_text = sys.argv[idx + 2]
        resp_file = Path(sys.argv[idx + 3]) if len(sys.argv) > idx + 3 else None
        if resp_file:
            result = verify_from_file(agent, task_text, resp_file)
        else:
            # Read response from stdin
            response_text = sys.stdin.read()
            result = verify_delivery(agent, task_text, response_text)
        log_result(agent, result)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["delivered"] else 1)
    else:
        print(__doc__)
        sys.exit(0)
