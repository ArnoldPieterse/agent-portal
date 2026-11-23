#!/usr/bin/env python3
"""
runbook_preflight.py - Pre-flight validation for one-click runbook trigger (Builder Goal #10).

Called by the portal POST /api/runbooks/trigger endpoint BEFORE executing a runbook.
Returns a JSON dict: {"ok": bool, "checks": {...}, "reasons": [...]}

Checks performed:
  1. agent_available - target agent exists in agents.json and its model is loaded
  2. host_reachable   - the host where the operation runs responds to a health probe
  3. no_conflict      - no other runbook is currently executing on the same agent/host

Usage (standalone test):
    python memory/mechanic/runbook_preflight.py --agent mechanic --runbook "model-swap"
"""
import argparse
import json
import os
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

AGENTS_JSON = Path("agents.json")
DECISION_LOG = Path("memory/ops/decision-log.jsonl")
LOCK_FILE = Path("memory/ops/.runbook_active.lock")


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def check_agent_available(agent_id: str) -> dict:
    """Verify the agent exists in agents.json and its model is loaded."""
    result = {"pass": False, "detail": ""}
    if not AGENTS_JSON.exists():
        result["detail"] = f"agents.json not found at {AGENTS_JSON}"
        return result
    try:
        raw = json.loads(AGENTS_JSON.read_text(encoding="utf-8"))
    except Exception as e:
        result["detail"] = f"agents.json parse error: {e}"
        return result

    # agents.json formats: {"agents": [...]} | [...] | {agent_id: config}
    if isinstance(raw, dict) and "agents" in raw and isinstance(raw["agents"], list):
        agents = raw["agents"]
    elif isinstance(raw, list):
        agents = raw
    elif isinstance(raw, dict):
        agents = [v for v in raw.values() if isinstance(v, dict)]
    else:
        result["detail"] = "agents.json: unrecognized format"
        return result

    entry = next((a for a in agents if a.get("id") == agent_id or a.get("agent") == agent_id), None)

    if entry is None:
        result["detail"] = f"agent '{agent_id}' not found in agents.json"
        return result

    # Check model loaded status (if present in config)
    model_loaded = entry.get("model_loaded", entry.get("loaded", None))
    # Host extraction: agents.json uses "studio": "http://127.0.0.1:8888" or host/port fields
    studio_url = entry.get("studio", "")
    if studio_url:
        # parse host:port from URL
        import re as _re
        m = _re.search(r'//([^:/]+)(?::(\d+))?/', studio_url)
        if m:
            host = m.group(1)
            port = int(m.group(2)) if m.group(2) else 8888
        else:
            host, port = "127.0.0.1", 8888
    else:
        host = entry.get("host", entry.get("seat", "127.0.0.1"))
        port = int(entry.get("port", 8888))

    if model_loaded is False:
        result["detail"] = f"agent '{agent_id}' found but model not loaded (host={host})"
        return result

    result["pass"] = True
    result["detail"] = f"agent '{agent_id}' OK (host={host}, port={port}, model_loaded={model_loaded})"
    result["_host"] = host
    result["_port"] = port
    return result


def check_host_reachable(host: str, port: int = 8099, timeout: float = 3.0) -> dict:
    """TCP-connect to host:port (portal health endpoint). Falls back to :8888 if :8099 fails."""
    result = {"pass": False, "detail": ""}
    for p in (port, 8888):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            rc = s.connect_ex((host, p))
            s.close()
            if rc == 0:
                result["pass"] = True
                result["detail"] = f"host '{host}' reachable on port {p}"
                return result
        except Exception as e:
            continue
    result["detail"] = f"host '{host}' unreachable (tried ports {port}, 8888; timeout={timeout}s)"
    return result


def check_no_conflict(agent_id: str, runbook_name: str) -> dict:
    """Check lock file for an active runbook on the same agent. Also scan recent decision-log entries."""
    result = {"pass": False, "detail": ""}

    # Lock-file check (set by playbook_runner during execution)
    if LOCK_FILE.exists():
        try:
            lock_data = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
            lock_agent = lock_data.get("agent", "")
            lock_rb = lock_data.get("runbook", "")
            lock_ts = lock_data.get("ts", 0)
            # Stale lock (>10 min) is ignored
            if time.time() - lock_ts < 600:
                if lock_agent == agent_id:
                    result["detail"] = f"conflict: runbook '{lock_rb}' already running on agent '{agent_id}' (ts={lock_ts})"
                    return result
        except Exception:
            pass  # corrupt lock = ignore

    # Decision-log check: look for a 'runbook_start' entry in the last 5 min with no matching 'runbook_end'
    if DECISION_LOG.exists():
        try:
            lines = DECISION_LOG.read_text(encoding="utf-8").strip().splitlines()[-50:]
            running = {}
            for line in reversed(lines):
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                etype = entry.get("type", "")
                eagent = entry.get("agent", "")
                ets = entry.get("ts", 0)
                if time.time() - ets > 300:
                    break
                if etype == "runbook_start" and eagent == agent_id:
                    running[entry.get("runbook", "?")] = True
                elif etype == "runbook_end" and eagent == agent_id:
                    running.pop(entry.get("runbook", "?"), None)
            if running:
                result["detail"] = f"conflict: runbook(s) {list(running.keys())} still active on agent '{agent_id}'"
                return result
        except Exception:
            pass

    result["pass"] = True
    result["detail"] = "no conflicting operations detected"
    return result


def preflight(agent_id: str, runbook_name: str) -> dict:
    """Run all three checks. Returns the full result dict."""
    reasons = []
    checks = {}

    # 1. Agent available
    c1 = check_agent_available(agent_id)
    checks["agent_available"] = {"pass": c1["pass"], "detail": c1["detail"]}
    if not c1["pass"]:
        reasons.append(c1["detail"])

    # 2. Host reachable (use host from agent check if available)
    host = c1.get("_host", "127.0.0.1")
    port = c1.get("_port", 8099)
    # For local agents, use localhost
    if host in ("local", "white", "this-host"):
        host = "127.0.0.1"
    c2 = check_host_reachable(host, port)
    checks["host_reachable"] = {"pass": c2["pass"], "detail": c2["detail"]}
    if not c2["pass"]:
        reasons.append(c2["detail"])

    # 3. No conflict
    c3 = check_no_conflict(agent_id, runbook_name)
    checks["no_conflict"] = {"pass": c3["pass"], "detail": c3["detail"]}
    if not c3["pass"]:
        reasons.append(c3["detail"])

    ok = all(c["pass"] for c in checks.values())
    return {
        "ok": ok,
        "agent": agent_id,
        "runbook": runbook_name,
        "ts": _now_iso(),
        "checks": checks,
        "reasons": reasons,
    }


def main():
    ap = argparse.ArgumentParser(description="Pre-flight validation for runbook trigger")
    ap.add_argument("--agent", required=True, help="Agent ID to validate")
    ap.add_argument("--runbook", default="unknown", help="Runbook name (for conflict check)")
    args = ap.parse_args()

    result = preflight(args.agent, args.runbook)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
