"""Unified autonomous-action log writer.

Appends one JSON line per autonomous fleet action to memory/ops/autonomous-actions.jsonl.
Schema: {ts, host, action, trigger, outcome, detail, reversible, source_script}

Usage from any script:
    from memory.ops.action_log import log_action
    log_action(action="restart_portal", trigger="watchdog", outcome="success",
               detail="Portal process dead >60s; restarted via schtasks", host="White")
"""
import json
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent / "autonomous-actions.jsonl"


def log_action(
    action: str,
    trigger: str,
    outcome: str,
    detail: str,
    host: str = "White",
    reversible: bool = True,
    source_script: str = "",
) -> dict:
    """Append one autonomous-action record. Returns the record dict."""
    rec = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "host": host,
        "action": action,
        "trigger": trigger,
        "outcome": outcome,
        "detail": detail[:200],
        "reversible": reversible,
        "source_script": source_script,
    }
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def tail(n: int = 20) -> list:
    """Return the last n records (oldest first). Safe on missing/empty file."""
    if not LOG_FILE.exists():
        return []
    lines = LOG_FILE.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(l) for l in lines[-n:] if l.strip()]


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        # Self-test: write 3 records, read back, verify schema
        test_records = [
            dict(action="restart_portal", trigger="watchdog", outcome="success",
                 detail="Self-test: portal restart simulated", host="White"),
            dict(action="deploy_canary", trigger="health_check", outcome="rolled_back",
                 detail="Self-test: canary deploy rolled back", host="Black"),
            dict(action="auto_clean_disk", trigger="disk_monitor", outcome="success",
                 detail="Self-test: disk cleanup 2.1GB freed", host="Red"),
        ]
        for r in test_records:
            log_action(**r)
        got = tail(3)
        assert len(got) == 3, f"expected 3, got {len(got)}"
        required = {"ts", "host", "action", "trigger", "outcome", "detail", "reversible", "source_script"}
        for i, rec in enumerate(got):
            missing = required - set(rec.keys())
            assert not missing, f"record {i} missing keys: {missing}"
            assert rec["ts"].endswith("Z"), f"record {i} ts not UTC: {rec['ts']}"
        print(f"self-test PASS (3/3 records written + read back, schema valid)")
    else:
        print("usage: python action_log.py --self-test")
