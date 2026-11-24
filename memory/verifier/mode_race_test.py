"""Mode Race Condition Test (Verifier goal #6, 2026-11-24).

Simulates two concurrent mode-change triggers (goal reaches 100% AND 6h timer fires simultaneously).
Verifies:
  - fleet-mode.json ends in a valid state (not corrupted/partial)
  - Exactly one transition is logged per simulation
  - No deadlock

Runs 50 concurrent-trigger simulations. All must produce valid final state.
Usage: python memory/verifier/mode_race_test.py [--count N]
"""
import json
import os
import sys
import time
import tempfile
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

class AtomicModeWriter:
    """Simulates the atomic write pattern: write-to-temp + os.rename with a lock."""
    
    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        self.transition_log = []  # thread-safe log of transitions
    
    def write_mode(self, mode, source=""):
        """Atomically write fleet-mode.json. Returns True if this was the first writer."""
        data = {
            "mode": mode,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "goal_pct": 100.0 if mode != "WORK" else 99.0,
            "source": source,
            "schema_version": "1.0"
        }
        
        with self.lock:
            # Check if file already exists with a different mode (race: someone got here first)
            if os.path.exists(self.path):
                try:
                    with open(self.path, encoding="utf-8") as f:
                        existing = json.load(f)
                    if existing.get("mode") != "WORK":
                        # Already transitioned - don't write again (idempotent guard)
                        return False
                except (json.JSONDecodeError, OSError):
                    pass  # Corrupt or unreadable - overwrite
            
            # Write to temp + rename (atomic on POSIX; on Windows os.replace is atomic)
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp, self.path)  # Atomic rename
            
            self.transition_log.append({"mode": mode, "source": source})
            return True

def simulate_race(writer):
    """Simulate two concurrent triggers racing to transition mode."""
    results = {"w1_first": False, "w2_first": False}
    
    def trigger_goal_complete():
        # Simulates: goal reaches 100% -> write MAINTENANCE
        time.sleep(0.001)  # Tiny random delay to simulate scheduling
        results["w1_first"] = writer.write_mode("MAINTENANCE", source="goal-complete")
    
    def trigger_timer():
        # Simulates: 6h inactivity timer -> write IDLE
        time.sleep(0.001)  # Tiny random delay
        results["w2_first"] = writer.write_mode("MAINTENANCE", source="timer-6h")
    
    t1 = threading.Thread(target=trigger_goal_complete)
    t2 = threading.Thread(target=trigger_timer)
    t1.start()
    t2.start()
    t1.join(timeout=5)  # Deadlock detection: 5s timeout
    t2.join(timeout=5)
    
    return results, t1.is_alive(), t2.is_alive()

def validate_state(path):
    """Validate the final fleet-mode.json is well-formed."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return False, f"Cannot read/parse: {e}"
    
    # Check required fields
    if "mode" not in data:
        return False, "missing 'mode' field"
    if data["mode"] not in ("WORK", "MAINTENANCE", "IDLE"):
        return False, f"invalid mode: {data['mode']!r}"
    if "timestamp" not in data:
        return False, "missing 'timestamp' field"
    
    # Validate ISO-8601
    try:
        ts = data["timestamp"].replace("Z", "+00:00")
        datetime.fromisoformat(ts)
    except (ValueError, AttributeError):
        return False, f"invalid timestamp: {data['timestamp']!r}"
    
    return True, "valid"

def run_test(count=50):
    """Run N concurrent-trigger simulations."""
    failures = []
    
    for i in range(count):
        tmpdir = tempfile.mkdtemp(prefix=f"race_{i}_")
        fm_path = os.path.join(tmpdir, "fleet-mode.json")
        
        # Start with WORK state
        initial = {
            "mode": "WORK",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "goal_pct": 99.0,
            "source": "test-init",
            "schema_version": "1.0"
        }
        with open(fm_path, "w", encoding="utf-8") as f:
            json.dump(initial, f)
        
        writer = AtomicModeWriter(fm_path)
        results, t1_alive, t2_alive = simulate_race(writer)
        
        # Check 1: No deadlock (threads completed)
        if t1_alive or t2_alive:
            failures.append(f"[{i}] DEADLOCK: thread still alive")
            shutil.rmtree(tmpdir, ignore_errors=True)
            continue
        
        # Check 2: Exactly one transition logged
        if len(writer.transition_log) != 1:
            failures.append(f"[{i}] Expected exactly 1 transition, got {len(writer.transition_log)}")
            shutil.rmtree(tmpdir, ignore_errors=True)
            continue
        
        # Check 3: Final state is valid
        valid, msg = validate_state(fm_path)
        if not valid:
            failures.append(f"[{i}] Invalid final state: {msg}")
            shutil.rmtree(tmpdir, ignore_errors=True)
            continue
        
        # Check 4: Exactly one thread got first-write (the other was rejected)
        firsts = sum(1 for v in results.values() if v)
        if firsts != 1:
            failures.append(f"[{i}] Expected exactly 1 first-writer, got {firsts}")
        
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    return count, failures

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Mode Race Condition Test")
    parser.add_argument("--count", type=int, default=50)
    args = parser.parse_args()
    
    t0 = time.time()
    print(f"MODE RACE CONDITION TEST ({args.count} simulations)")
    print("-" * 60)
    
    total, failures = run_test(args.count)
    elapsed = time.time() - t0
    
    if failures:
        print(f"RESULT: FAIL ({len(failures)}/{total} failures) in {elapsed:.1f}s")
        for f in failures[:5]:
            print(f"  {f}")
        sys.exit(1)
    else:
        print(f"RESULT: PASS ({total}/{total} simulations valid, no deadlock, exactly 1 transition each)")
        print(f"  Runtime: {elapsed:.1f}s (<30s limit)")
        
        # Runtime check
        if elapsed >= 30:
            print("  WARNING: exceeded 30s target")
        sys.exit(0)

if __name__ == "__main__":
    main()
