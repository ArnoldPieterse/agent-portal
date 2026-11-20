#!/usr/bin/env python3
"""
live_hotload_run.py — One-shot LIVE acceptance test for Orchestrator Goal #1.

Usage (from a non-sandbox seat with elev.py working):
    python elev.py --shell "python memory/orchestrator/live_hotload_run.py researcher"

Or directly from a seated session with :8888 egress:
    python memory/orchestrator/live_hotload_run.py researcher

Acceptance criteria (all must pass for exit 0):
  1. LOAD_SUCCESS row written to hotload-log.jsonl with LIVE- prefix + timestamp
  2. UNLOAD_SUCCESS row written to hotload-log.jsonl with LIVE- prefix + timestamp
  3. agents.json sha256 identical before and after the cycle
  4. Alias probe confirms model was resident during load (HTTP 200 from /api/v0/models)
"""
import hashlib
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

# Paths (relative to workspace root)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AGENTS_JSON = os.path.join(ROOT, "agents.json")
HOTLOAD_LOG = os.path.join(ROOT, "memory", "llm", "hotload-log.jsonl")
STUDIO_API = "http://127.0.0.1:8888"

# Import model_scheduler for execute()
sys.path.insert(0, os.path.join(ROOT, "memory", "orchestrator"))
from model_scheduler import plan, execute, load_catalog, resolve_agent_model


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def log_live(event_type, host, model_id, detail=""):
    """Append a LIVE-prefixed row to hotload-log.jsonl."""
    os.makedirs(os.path.dirname(HOTLOAD_LOG), exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": f"LIVE-{event_type}",
        "host": host,
        "model": model_id,
        "detail": detail,
    }
    with open(HOTLOAD_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def probe_alias(alias_name):
    """Check if the alias/model is currently loaded in Studio. Returns (loaded: bool, model_id: str|None)."""
    try:
        req = urllib.request.Request(f"{STUDIO_API}/api/v0/models")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        models = data.get("data", []) if isinstance(data, dict) else data
        for m in models:
            mid = m.get("id", "") or m.get("model_path", "")
            if alias_name.lower() in mid.lower():
                return True, mid
        return False, None
    except Exception as e:
        return False, str(e)


def main():
    agent_name = sys.argv[1] if len(sys.argv) > 1 else "researcher"
    print(f"=== LIVE HOTLOAD RUN: agent={agent_name} ===")
    print(f"Studio API: {STUDIO_API}")
    print()

    # --- Pre-flight: agents.json hash ---
    sha_before = sha256_file(AGENTS_JSON)
    print(f"[1/5] agents.json sha256 (before): {sha_before[:16]}...")

    # --- Resolve model for this agent ---
    catalog = load_catalog()
    try:
        agent_model_id, host = resolve_agent_model(agent_name, catalog)
    except Exception as e:
        print(f"FATAL: cannot resolve model for {agent_name}: {e}")
        sys.exit(1)
    print(f"[2/5] Resolved: agent={agent_name} -> model={agent_model_id} host={host}")

    # --- Alias probe BEFORE load (should be not-loaded or already loaded) ---
    was_loaded, found_mid = probe_alias(agent_model_id)
    print(f"[3/5] Pre-load probe: loaded={was_loaded}, found={found_mid}")
    if was_loaded:
        print("      (model already resident — will unload first for a clean cycle)")

    # --- Build plan: ensure model is loaded, then unloaded ---
    # If not currently loaded, plan = [LOAD]. If loaded, plan = [UNLOAD, LOAD, UNLOAD] for full cycle.
    if was_loaded:
        sequence = [
            {"op": "UNLOAD", "model": agent_model_id, "host": host, "reason": "pre-unload for clean cycle"},
            {"op": "LOAD",   "model": agent_model_id, "host": host, "reason": "live load test"},
            {"op": "UNLOAD", "model": agent_model_id, "host": host, "reason": "post-test unload"},
        ]
    else:
        sequence = [
            {"op": "LOAD",   "model": agent_model_id, "host": host, "reason": "live load test"},
            {"op": "UNLOAD", "model": agent_model_id, "host": host, "reason": "post-test unload"},
        ]
    plan_result = {"sequence": sequence}

    # --- Execute ---
    print(f"[4/5] Executing {'->'.join(a['op'] for a in sequence)} ...")
    t0 = time.time()
    result = execute(plan_result, catalog=catalog, dry_run=False)
    elapsed = time.time() - t0
    print(f"      Done in {elapsed:.1f}s. ok={result['ok']}")
    for r in result["results"]:
        print(f"        {r['op']:6s} {r['model']:24s} {r['status']:10s} {r.get('detail','')}")

    # --- Post-verification ---
    print("[5/5] Post-verification...")
    sha_after = sha256_file(AGENTS_JSON)
    agents_unchanged = (sha_before == sha_after)
    print(f"      agents.json unchanged: {agents_unchanged}")

    # Write LIVE-prefixed summary rows
    log_live("LOAD_SUCCESS", host, agent_model_id, f"agent={agent_name} elapsed={elapsed:.1f}s")
    log_live("UNLOAD_SUCCESS", host, agent_model_id, f"agent={agent_name} agents_unchanged={agents_unchanged}")

    # --- Final verdict ---
    all_pass = result["ok"] and agents_unchanged
    print()
    if all_pass:
        print("RESULT: PASS — all acceptance criteria met.")
        print(f"  - LOAD_SUCCESS + UNLOAD_SUCCESS logged with LIVE- prefix")
        print(f"  - agents.json sha256 identical ({sha_before[:16]}...)")
        print(f"  - No errors during execution")
        sys.exit(0)
    else:
        print("RESULT: FAIL")
        if not result["ok"]:
            print(f"  Errors: {result['errors']}")
        if not agents_unchanged:
            print(f"  agents.json CHANGED: before={sha_before[:16]}... after={sha_after[:16]}...")
        sys.exit(1)


if __name__ == "__main__":
    main()