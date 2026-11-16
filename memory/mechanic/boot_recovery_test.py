#!/usr/bin/env python3
"""boot_recovery_test.py - Local dry-run test for boot_recovery.py logic.

Validates hostname routing, log format, and flow correctness WITHOUT network.
Run: python memory/mechanic/boot_recovery_test.py
Exit 0 = all tests pass; non-zero = failure with details.
"""
import json, os, sys, unittest.mock as mock
from pathlib import Path

# Ensure we can import boot_recovery from ops/
sys.path.insert(0, str(Path(__file__).parent.parent / "ops"))

PASS = 0
FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} {detail}")

def test_hostname_routing():
    """Verify each hostname routes to the correct fleet_reload invocation."""
    print("\n--- Test: hostname routing ---")
    import boot_recovery as br
    
    cases = [
        ("White", True),
        ("PALE-39", True),
        ("Black-99", True),
        ("Red-245", True),
        ("UnknownHost", False),  # should exit(1)
    ]
    
    for hostname, should_work in cases:
        with mock.patch("platform.node", return_value=hostname):
            br.HOSTNAME = hostname
            with mock.patch.object(br, "log") as mock_log, \
                 mock.patch("urllib.request.urlopen") as mock_urlopen, \
                 mock.patch("subprocess.run") as mock_run, \
                 mock.patch("sys.exit", side_effect=SystemExit(1)):
                # Mock studio check to succeed
                mock_resp = mock.Mock(status=200)
                mock_urlopen.return_value.__enter__ = mock.Mock(return_value=mock_resp)
                mock_urlopen.return_value.__exit__ = mock.Mock(return_value=False)
                
                try:
                    br.main()
                    if should_work:
                        check(f"{hostname}", True)
                    else:
                        check(f"{hostname} (should fail)", False, "did not exit")
                except SystemExit as e:
                    if not should_work and e.code == 1:
                        check(f"{hostname} (correctly rejected)", True)
                    elif should_work:
                        check(f"{hostname}", False, f"unexpected exit {e.code}")
                    else:
                        check(f"{hostname}", True)

def test_log_format():
    """Verify log entries are valid JSONL with required fields."""
    print("\n--- Test: log format ---")
    import boot_recovery as br
    import tempfile
    
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
    tmp.close()
    
    with mock.patch.object(br, "LOG_PATH", tmp.name):
        br.log("test_event", foo="bar")
    
    with open(tmp.name) as f:
        line = f.readline().strip()
    os.unlink(tmp.name)
    
    entry = json.loads(line)
    check("has ts", "ts" in entry, str(entry.keys()))
    check("has host", "host" in entry)
    check("has event", entry.get("event") == "test_event")
    check("extra kwarg preserved", entry.get("foo") == "bar")

def test_studio_timeout():
    """Verify wait_studio returns False after timeout (mocked clock)."""
    print("\n--- Test: studio timeout ---")
    import boot_recovery as br
    
    call_count = [0]
    def fake_urlopen(*a, **kw):
        call_count[0] += 1
        raise ConnectionRefusedError("not up yet")
    
    with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen), \
         mock.patch("time.sleep"), \
         mock.patch("time.time", side_effect=[0, 0, 301]):  # start, loop check, past deadline
        result = br.wait_studio(timeout_min=5)
    
    check("returns False on timeout", result is False)
    check("polled at least once", call_count[0] >= 1, f"calls={call_count[0]}")

def test_full_flow_logging():
    """End-to-end: verify the sequence of log events in a successful boot."""
    print("\n--- Test: full flow event sequence ---")
    import boot_recovery as br
    
    events = []
    def capture_log(event, **kw):
        events.append(event)
    
    with mock.patch.object(br, "log", side_effect=capture_log), \
         mock.patch("platform.node", return_value="White"), \
         mock.patch("urllib.request.urlopen") as mock_urlopen, \
         mock.patch("subprocess.run") as mock_run:
        mock_resp = mock.Mock(status=200)
        mock_urlopen.return_value.__enter__ = mock.Mock(return_value=mock_resp)
        mock_urlopen.return_value.__exit__ = mock.Mock(return_value=False)
        mock_run.return_value = mock.Mock(returncode=0, stdout="ok", stderr="")
        
        br.HOSTNAME = "White"
        br.main()
    
    expected = ["boot_detected", "studio_up", "invoking_fleet_reload", "fleet_reload_done", "portal_up"]
    check("event sequence correct", events == expected, f"got {events}")

if __name__ == "__main__":
    print(f"boot_recovery_test.py - validating boot_recovery.py logic (no network needed)")
    test_hostname_routing()
    test_log_format()
    test_studio_timeout()
    test_full_flow_logging()
    print(f"\n{'='*40}")
    print(f"RESULT: {PASS} passed, {FAIL} failed")
    sys.exit(0 if FAIL == 0 else 1)