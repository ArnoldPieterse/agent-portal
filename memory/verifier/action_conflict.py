"""Concurrent Action Conflict Detector.
Parses decision-log for overlapping autonomous actions targeting the same resource.
Conflict: (a) same host + temporal overlap >5s, OR (b) same file prefix.
Writes conflicts to memory/ops/action-conflicts.jsonl.
"""
import json, sys, pathlib
from datetime import datetime, timedelta

DECISION_LOG = pathlib.Path("memory/decision-log.jsonl")
OUTPUT_FILE = pathlib.Path("memory/ops/action-conflicts.jsonl")
OVERLAP_THRESHOLD_S = 5  # seconds of overlap required for conflict

def parse_log(path):
    """Parse JSONL into list of (timestamp, entry)."""
    if not path.exists():
        return []
    entries = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                ts = datetime.fromisoformat(e["timestamp"])
                e["_id"] = f"log-{i}"
                entries.append((ts, e))
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
    entries.sort(key=lambda x: x[0])
    return entries

def get_target_host(entry):
    """Extract host from entry."""
    return entry.get("host", entry.get("target", None))

def get_file_prefix(entry):
    """Extract file prefix (first 2 path components) from entry."""
    target = entry.get("target", entry.get("file", ""))
    parts = target.replace("\\", "/").split("/")
    if len(parts) >= 2:
        return "/".join(parts[:2])
    return target

def get_duration(entry):
    """Get action duration in seconds."""
    return float(entry.get("duration_s", 0))

def find_conflicts(entries):
    """Find all conflict pairs. Returns list of conflict dicts."""
    conflicts = []
    n = len(entries)
    
    for i in range(n):
        ts_i, e_i = entries[i]
        host_i = get_target_host(e_i)
        file_prefix_i = get_file_prefix(e_i)
        dur_i = get_duration(e_i)
        end_i = ts_i + timedelta(seconds=dur_i)
        
        for j in range(i + 1, n):
            ts_j, e_j = entries[j]
            
            # Early exit: if start of j is after end of i, no overlap possible
            if ts_j >= end_i and dur_i > 0:
                break
            
            host_j = get_target_host(e_j)
            file_prefix_j = get_file_prefix(e_j)
            dur_j = get_duration(e_j)
            
            # Calculate temporal overlap
            start_overlap = max(ts_i, ts_j)
            end_overlap = min(end_i, ts_j + timedelta(seconds=dur_j))
            overlap_s = (end_overlap - start_overlap).total_seconds()
            
            conflict_reason = None
            
            # Rule (a): same host AND overlap > threshold
            if host_i and host_i == host_j and overlap_s > OVERLAP_THRESHOLD_S:
                conflict_reason = f"same_host:{host_i},overlap:{overlap_s:.1f}s"
            
            # Rule (b): same file prefix
            elif file_prefix_i and file_prefix_i == file_prefix_j and file_prefix_i != "":
                conflict_reason = f"same_file_prefix:{file_prefix_i}"
            
            if conflict_reason:
                conflicts.append({
                    "action_id_1": e_i["_id"],
                    "action_id_2": e_j["_id"],
                    "type_1": e_i.get("type", "unknown"),
                    "type_2": e_j.get("type", "unknown"),
                    "target": host_i or file_prefix_i,
                    "overlap_seconds": round(overlap_s, 2),
                    "reason": conflict_reason,
                    "time_1": ts_i.isoformat(),
                    "time_2": ts_j.isoformat()
                })
    
    return conflicts

def run(decision_log=DECISION_LOG):
    """Main: parse, find conflicts, write output."""
    entries = parse_log(decision_log)
    conflicts = find_conflicts(entries)
    
    if conflicts:
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            for c in conflicts:
                f.write(json.dumps(c) + "\n")
        for c in conflicts:
            print(f"  CONFLICT: {c['action_id_1']} vs {c['action_id_2']} "
                  f"({c['reason']})")
    else:
        print("No action conflicts detected.")
    
    return conflicts, 0

def self_test():
    """Verification cases. Returns (passed, total)."""
    import tempfile, os
    passed = 0
    total = 0
    base = datetime(2026, 11, 24, 10, 0, 0)
    
    # Case 1: two model-swaps on White starting 3s apart with 30s duration = 1 conflict
    total += 1
    entries = [
        {"type": "model_swap", "host": "White", "duration_s": 30, 
         "timestamp": base.isoformat()},
        {"type": "model_swap", "host": "White", "duration_s": 30, 
         "timestamp": (base + timedelta(seconds=3)).isoformat()}
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
        tmp = pathlib.Path(f.name)
    
    try:
        parsed = parse_log(tmp)
        conflicts = find_conflicts(parsed)
        assert len(conflicts) == 1, f"Expected 1 conflict, got {len(conflicts)}"
        assert "same_host:White" in conflicts[0]["reason"], f"Wrong reason: {conflicts[0]['reason']}"
        # Overlap should be 30-3=27s
        assert abs(conflicts[0]["overlap_seconds"] - 27.0) < 0.1, f"Expected ~27s overlap, got {conflicts[0]['overlap_seconds']}"
        passed += 1
    except AssertionError as ex:
        print(f"FAIL case1: {ex}")
    finally:
        os.unlink(tmp)
    
    # Case 2: swap on White + swap on Black concurrent = no conflict
    total += 1
    entries = [
        {"type": "model_swap", "host": "White", "duration_s": 30, 
         "timestamp": base.isoformat()},
        {"type": "model_swap", "host": "Black", "duration_s": 30, 
         "timestamp": (base + timedelta(seconds=1)).isoformat()}
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
        tmp = pathlib.Path(f.name)
    
    try:
        parsed = parse_log(tmp)
        conflicts = find_conflicts(parsed)
        assert len(conflicts) == 0, f"Expected no conflict (different hosts), got {len(conflicts)}"
        passed += 1
    except AssertionError as ex:
        print(f"FAIL case2: {ex}")
    finally:
        os.unlink(tmp)
    
    # Case 3: same-host actions 60s apart = no conflict (below overlap threshold)
    total += 1
    entries = [
        {"type": "model_swap", "host": "White", "duration_s": 30, 
         "timestamp": base.isoformat()},
        {"type": "model_swap", "host": "White", "duration_s": 30, 
         "timestamp": (base + timedelta(seconds=60)).isoformat()}
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
        tmp = pathlib.Path(f.name)
    
    try:
        parsed = parse_log(tmp)
        conflicts = find_conflicts(parsed)
        assert len(conflicts) == 0, f"Expected no conflict (60s apart > 30s duration), got {len(conflicts)}"
        passed += 1
    except AssertionError as ex:
        print(f"FAIL case3: {ex}")
    finally:
        os.unlink(tmp)
    
    # Case 4: same file prefix conflict (different hosts but writing same dir)
    total += 1
    entries = [
        {"type": "file_write", "target": "memory/ops/a.json", "duration_s": 5, 
         "timestamp": base.isoformat()},
        {"type": "file_write", "target": "memory/ops/b.json", "duration_s": 5, 
         "timestamp": (base + timedelta(seconds=1)).isoformat()}
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
        tmp = pathlib.Path(f.name)
    
    try:
        parsed = parse_log(tmp)
        conflicts = find_conflicts(parsed)
        assert len(conflicts) == 1, f"Expected 1 file-prefix conflict, got {len(conflicts)}"
        assert "same_file_prefix" in conflicts[0]["reason"]
        passed += 1
    except AssertionError as ex:
        print(f"FAIL case4: {ex}")
    finally:
        os.unlink(tmp)
    
    # Case 5: boundary - overlap exactly 5s = NO conflict (need >5s)
    total += 1
    entries = [
        {"type": "model_swap", "host": "White", "duration_s": 30, 
         "timestamp": base.isoformat()},
        # Starts at +25s: overlap = 30-25 = 5s exactly (NOT > 5)
        {"type": "model_swap", "host": "White", "duration_s": 30, 
         "timestamp": (base + timedelta(seconds=25)).isoformat()}
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
        tmp = pathlib.Path(f.name)
    
    try:
        parsed = parse_log(tmp)
        conflicts = find_conflicts(parsed)
        assert len(conflicts) == 0, f"Expected no conflict at exactly 5s overlap, got {len(conflicts)}"
        passed += 1
    except AssertionError as ex:
        print(f"FAIL case5: {ex}")
    finally:
        os.unlink(tmp)
    
    # Case 6: run on real decision-log (should be clean - different times/types)
    total += 1
    entries = parse_log(DECISION_LOG)
    conflicts = find_conflicts(entries)
    # Real log entries have no "host" field and duration_s is tiny (<1s), 
    # so they shouldn't conflict unless same file prefix
    # All targets are "Safe Test" which is not a file path, so no file-prefix match
    assert len(conflicts) == 0, f"Unexpected conflicts on real log: {conflicts}"
    passed += 1
    
    print(f"\nSelf-test: {passed}/{total} passed")
    return passed, total

if __name__ == "__main__":
    if "--self-test" in sys.argv:
        p, t = self_test()
        sys.exit(0 if p == t else 1)
    else:
        conflicts, rc = run()
        sys.exit(rc)
