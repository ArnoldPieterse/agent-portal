"""action_log.py - Unified autonomous-action logger for the fleet.

Implements Mechanic's spec (memory/ops/autonomous-action-log-spec-2026-11-24.md).
All fleet scripts call log_action() at the point where they take an autonomous action.
The cockpit reads tail_entries() to render the "Fleet Acted" panel.

Usage:
    from memory.ops.action_log import log_action
    log_action(action="restart_portal", host="White", trigger="health_check",
               outcome="success", detail="Portal restarted after 3 failed health checks")
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

LOG_PATH = Path(__file__).resolve().parent / "autonomous-actions.jsonl"

# Valid enum values per spec (for validation, not enforcement)
VALID_ACTIONS = {
    "restart_portal", "deploy_canary", "hotpatch_rollback", "boot_recovery",
    "auto_clean_disk", "net_probe_alert", "model_reload", "feed_refresh",
    "state_collect", "mirror_sync", "git_commit"
}
VALID_TRIGGERS = {
    "health_check", "net_probe", "disk_monitor", "watchdog",
    "manual_schtasks", "collector_cycle", "idle_rotation"
}
VALID_OUTCOMES = {"success", "failed", "rolled_back", "blocked"}


def log_action(
    action: str,
    host: str,
    trigger: str,
    outcome: str,
    detail: str,
    reversible: bool = True,
    source_script: Optional[str] = None,
) -> dict:
    """Append one autonomous-action record to the unified log.

    Returns the record dict (useful for callers that need the ts).
    Never raises on write failure - logs to stderr and returns empty dict.
    """
    if source_script is None:
        # Best-effort: infer from caller's file path
        import sys
        for mod in list(sys.modules.values()):
            f = getattr(mod, "__file__", None)
            if f and "memory/" in f and "action_log" not in f:
                source_script = f.replace(str(Path(__file__).parent.parent.parent), "").lstrip("/")
                break

    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "host": host,
        "action": action,
        "trigger": trigger,
        "outcome": outcome,
        "detail": detail,
        "reversible": reversible,
        "source_script": source_script or "unknown",
    }

    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as e:
        import sys
        print(f"[action_log] WARN: failed to write: {e}", file=sys.stderr)
        return {}

    return record


def tail_entries(n: int = 20, since_hours: Optional[float] = None) -> list:
    """Read the last n entries from the unified log.

    If since_hours is given, filter to only records within that window.
    Returns a list of dicts (oldest first).
    """
    if not LOG_PATH.exists():
        return []

    try:
        lines = LOG_PATH.read_text(encoding="utf-8").strip().splitlines()
    except OSError:
        return []

    entries = []
    for line in lines:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # skip malformed lines

    if since_hours is not None:
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        entries = [
            e for e in entries
            if _parse_ts(e.get("ts", "")) >= cutoff
        ]

    return entries[-n:]


def today_summary() -> dict:
    """Return a summary of today's actions (for cockpit feed)."""
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if not LOG_PATH.exists():
        return {"total": 0, "by_outcome": {}, "last_action_ts": None}

    try:
        lines = LOG_PATH.read_text(encoding="utf-8").strip().splitlines()
    except OSError:
        return {"total": 0, "by_outcome": {}, "last_action_ts": None}

    today_entries = []
    for line in lines:
        try:
            e = json.loads(line)
            if _parse_ts(e.get("ts", "")) >= midnight:
                today_entries.append(e)
        except json.JSONDecodeError:
            continue

    by_outcome = {}
    for e in today_entries:
        o = e.get("outcome", "unknown")
        by_outcome[o] = by_outcome.get(o, 0) + 1

    return {
        "total": len(today_entries),
        "by_outcome": by_outcome,
        "last_action_ts": today_entries[-1]["ts"] if today_entries else None,
    }


def _parse_ts(ts: str):
    """Parse ISO-8601 timestamp, return datetime or epoch 0 on failure."""
    try:
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return datetime(1970, 1, 1, tzinfo=timezone.utc)


if __name__ == "__main__":
    # Self-test: log a test entry and read it back
    rec = log_action(
        action="self_test", host="White", trigger="manual_schtasks",
        outcome="success", detail="action_log.py self-test entry",
        source_script="memory/ops/action_log.py"
    )
    entries = tail_entries(5)
    print(f"Logged: {rec.get('ts', 'FAILED')}")
    print(f"Tail ({len(entries)} entries):")
    for e in entries:
        print(f"  {e['ts']} [{e['outcome']}] {e['action']} on {e['host']}: {e['detail'][:60]}")
    summary = today_summary()
    print(f"Today: {summary['total']} actions, outcomes={summary['by_outcome']}")
