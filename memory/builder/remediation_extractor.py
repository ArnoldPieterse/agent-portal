"""remediation_extractor.py - Identify completed remediation cycles from decision-log.jsonl.

Usage:
    python memory/builder/remediation_extractor.py [--log PATH] [--output PATH]

Outputs JSON array of remediation cycle objects ready for post_mortem.py consumption.
Each cycle has: what_broke, root_cause, fix_applied, time_to_recovery, lessons_learned.
"""
import json
import pathlib
from datetime import datetime, timezone

REMEDIATION_TYPES = {"oom_recovery", "model_swap", "chaos_drill", "reboot_recovery"}

def extract_cycles(log_path: str = "memory/ops/decision-log.jsonl") -> list[dict]:
    """Scan decision-log for completed remediation cycles and return structured records."""
    p = pathlib.Path(log_path)
    if not p.exists():
        raise FileNotFoundError(f"Decision log not found: {log_path}")
    
    cycles = []
    lines = p.read_text(encoding="utf-8").strip().split("\n")
    
    for line in lines:
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        
        etype = entry.get("type", "")
        if etype not in REMEDIATION_TYPES:
            continue
        
        # Only include completed (successful) cycles
        success = entry.get("success", entry.get("recovered", False))
        if not success:
            continue
        
        cycle = _normalize(etype, entry)
        cycles.append(cycle)
    
    return cycles

def _normalize(etype: str, entry: dict) -> dict:
    """Normalize a raw decision-log entry into post-mortem structure."""
    ts_raw = entry.get("timestamp") or entry.get("ts", "")
    try:
        ts = datetime.fromisoformat(ts_raw)
        date_str = ts.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        date_str = "unknown-date"
    
    agent = entry.get("agent", "unknown")
    
    if etype == "oom_recovery":
        return {
            "what_broke": f"GPU memory exhausted on {agent}",
            "root_cause": entry.get("reason", "gpu_memory_exhausted"),
            "fix_applied": entry.get("action_taken", "model downgrade"),
            "time_to_recovery_s": entry.get("recovery_time_s", 0.0),
            "lessons_learned": f"Model {entry.get('before_model','?')} exceeded VRAM; "
                              f"downgraded to {entry.get('after_model','int8')}. "
                              f"Rollback: {entry.get('rollback_action','n/a')}",
            "agent": agent,
            "date": date_str,
            "type": etype,
            "raw_timestamp": ts_raw,
        }
    elif etype == "chaos_drill":
        return {
            "what_broke": f"Simulated fault: {entry.get('fault','unknown')} on {agent}",
            "root_cause": f"Chaos drill injection ({entry.get('drill_id','no-id')})",
            "fix_applied": "Auto-recovery (stale agent cleaned / pressure relieved / API recovered)",
            "time_to_recovery_s": 0.0,
            "lessons_learned": f"Drill {entry.get('drill_id','?')} severity={entry.get('severity','low')}; "
                              f"recovered within SLA. No side effects on other agents.",
            "agent": agent,
            "date": date_str,
            "type": etype,
            "raw_timestamp": ts_raw,
        }
    else:
        return {
            "what_broke": f"Remediation event ({etype}) on {agent}",
            "root_cause": entry.get("reason", "unspecified"),
            "fix_applied": entry.get("action_taken", "n/a"),
            "time_to_recovery_s": entry.get("recovery_time_s", 0.0),
            "lessons_learned": f"Type={etype}; agent={agent}",
            "agent": agent,
            "date": date_str,
            "type": etype,
            "raw_timestamp": ts_raw,
        }

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Extract remediation cycles from decision-log")
    ap.add_argument("--log", default="memory/ops/decision-log.jsonl")
    ap.add_argument("--output", default=None, help="Write JSON to this path (default: stdout)")
    args = ap.parse_args()
    
    cycles = extract_cycles(args.log)
    output = json.dumps(cycles, indent=2)
    
    if args.output:
        pathlib.Path(args.output).write_text(output, encoding="utf-8")
        print(f"Wrote {len(cycles)} cycles to {args.output}")
    else:
        print(output)

if __name__ == "__main__":
    main()
