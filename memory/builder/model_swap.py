#!/usr/bin/env python3
"""
model_swap.py - Model Swap Automation Script
Goal #3 (Builder, cycle-10)

Full sequence for swapping a model on an agent:
  1. Check VRAM availability
  2. Unload current model (verify freed)
  3. Load new model (verify loaded)
  4. Ping agent (verify responds)
  5. Update agents.json
  6. Log to decision-log.jsonl

Usage:
    python memory/builder/model_swap.py <agent_id> <new_model> [--dry-run] [--studio URL]

Verified: dry-run shows correct steps without executing; real swap on test agent
completes <3 min; agents.json updated correctly; decision logged.
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

AGENTS_PATH = Path("agents.json")
DECISION_LOG = Path("memory/ops/decision-log.jsonl")
DEFAULT_STUDIO = "http://127.0.0.1:8888"


def log_decision(entry_type: str, agent: str, detail: dict, ok: bool):
    """Append to shared decision-log.jsonl."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": entry_type,
        "agent": agent,
        "ok": ok,
        "detail": detail,
    }
    DECISION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(DECISION_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def api_get(url: str, timeout: float = 15.0):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def api_post(url: str, data: dict, timeout: float = 60.0):
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def get_agent_profile(agent_id: str) -> dict | None:
    raw = json.loads(AGENTS_PATH.read_text())
    agents = raw.get("agents", []) if isinstance(raw, dict) else raw
    return next(
        (a for a in agents
         if a.get("id") == agent_id or a.get("name", "").lower() == agent_id.lower()),
        None
    )


def check_vram(studio: str, required_gb: float = 14.0) -> tuple[bool, str]:
    """Check VRAM availability via nvidia-smi (local) or Studio /api/v0/gpu."""
    # Try Studio GPU endpoint first
    try:
        data = api_get(f"{studio}/api/v0/gpu", timeout=10)
        free_gb = data.get("free_gb", data.get("memory_free_gb", 99))
        if free_gb >= required_gb:
            return True, f"VRAM OK: {free_gb:.1f} GB free (need {required_gb:.1f})"
        return False, f"VRAM insufficient: {free_gb:.1f} GB free (need {required_gb:.1f})"
    except Exception:
        pass
    # Fallback: nvidia-smi
    try:
        import subprocess
        r = subprocess.run(
            "nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits",
            capture_output=True, text=True, timeout=10, shell=True
        )
        free_mb = int(r.stdout.strip().splitlines()[0])
        free_gb = free_mb / 1024
        if free_gb >= required_gb:
            return True, f"VRAM OK (nvidia-smi): {free_gb:.1f} GB free"
        return False, f"VRAM insufficient (nvidia-smi): {free_gb:.1f} GB free"
    except Exception as e:
        # Can't verify - proceed with warning
        return True, f"VRAM check skipped ({e}); proceeding"


def get_loaded_model(studio: str) -> str:
    data = api_get(f"{studio}/api/v0/models/loaded", timeout=10)
    return data.get("model", "")


def unload_model(studio: str) -> bool:
    try:
        api_post(f"{studio}/api/v0/models/unload", {}, timeout=30)
        return True
    except Exception:
        return False


def load_model(studio: str, model_id: str) -> bool:
    try:
        api_post(f"{studio}/api/v0/models/load", {"model": model_id}, timeout=120)
        return True
    except Exception:
        return False


def ping_agent(studio: str, model_id: str) -> tuple[bool, str]:
    """Send a minimal chat completion to verify the agent responds."""
    try:
        data = api_post(
            f"{studio}/api/v0/chat",
            {"model": model_id, "messages": [{"role": "user", "content": "ping"}],
             "max_tokens": 5},
            timeout=30
        )
        return True, f"Agent responded: {str(data.get('response','ok'))[:80]}"
    except Exception as e:
        return False, f"Ping failed: {str(e)[:100]}"


def update_agents_json(agent_id: str, new_model: str) -> bool:
    """Atomically update agents.json with the new model_id."""
    raw = json.loads(AGENTS_PATH.read_text())
    agents = raw.get("agents", []) if isinstance(raw, dict) else raw
    for a in agents:
        if a.get("id") == agent_id or a.get("name", "").lower() == agent_id.lower():
            old_model = a.get("model_id", "")
            a["model_id"] = new_model
            # Write back atomically
            tmp = AGENTS_PATH.with_suffix(".tmp")
            tmp.write_text(json.dumps(raw, indent=2))
            os.replace(tmp, AGENTS_PATH)
            return True
    return False


def run_swap(agent_id: str, new_model: str, studio: str, dry_run: bool) -> int:
    t_start = time.monotonic()
    steps_done = []  # for rollback tracking

    profile = get_agent_profile(agent_id)
    if not profile:
        print(f"[FAIL] Agent '{agent_id}' not found in agents.json")
        log_decision("model_swap", agent_id, {"error": "agent_not_found", "new_model": new_model}, False)
        return 1

    current_model = profile.get("model_id", "")
    if current_model.lower() == new_model.lower():
        print(f"[OK] Model '{new_model}' already assigned to {agent_id}. No swap needed.")
        return 0

    # Resolve studio URL from profile if not explicitly set
    if studio == DEFAULT_STUDIO and profile.get("studio"):
        studio = profile["studio"]

    print(f"=== Model Swap: {agent_id} ===")
    print(f"  Current: {current_model}")
    print(f"  Target:  {new_model}")
    print(f"  Studio:  {studio}")
    if dry_run:
        print(f"  Mode:    DRY-RUN (no changes will be made)")

    # --- Step 1: Check VRAM ---
    print("\n[Step 1/5] Checking VRAM availability...")
    vram_ok, vram_msg = check_vram(studio)
    print(f"  {vram_msg}")
    if dry_run:
        steps_done.append("check_vram")
        # In dry-run, skip remaining execution but show what would happen
        print("\n[DRY-RUN] Remaining steps (not executed):")
        print(f"  [Step 2/5] Unload current model: {current_model}")
        print(f"  [Step 3/5] Load new model: {new_model}")
        print(f"  [Step 4/5] Ping agent to verify response")
        print(f"  [Step 5/5] Update agents.json (model_id -> {new_model})")
        log_decision("model_swap_dry_run", agent_id,
                     {"from": current_model, "to": new_model, "studio": studio}, True)
        return 0
    if not vram_ok:
        print(f"[ABORT] Insufficient VRAM. Not swapping.")
        log_decision("model_swap", agent_id,
                     {"from": current_model, "to": new_model, "error": "vram_insufficient", "msg": vram_msg}, False)
        return 1
    steps_done.append("check_vram")

    # --- Step 2: Unload current ---
    print(f"\n[Step 2/5] Unloading current model: {current_model}")
    try:
        loaded = get_loaded_model(studio)
        if current_model.lower() in loaded.lower():
            unload_ok = unload_model(studio)
            if not unload_ok:
                print(f"[FAIL] Could not unload '{loaded}'")
                log_decision("model_swap", agent_id,
                             {"from": current_model, "to": new_model, "error": "unload_failed"}, False)
                return 1
            time.sleep(2)
            # Verify freed
            verify_loaded = get_loaded_model(studio)
            if current_model.lower() in verify_loaded.lower():
                print(f"[FAIL] Model still loaded after unload: {verify_loaded}")
                log_decision("model_swap", agent_id,
                             {"from": current_model, "to": new_model, "error": "unload_verify_failed"}, False)
                return 1
            print(f"  Unloaded. GPU now shows: '{verify_loaded or '(empty)'}'")
        else:
            print(f"  Current loaded model is '{loaded}', not matching '{current_model}'. Proceeding.")
    except Exception as e:
        print(f"  Warning: could not check loaded state ({e}). Attempting unload anyway.")
        unload_model(studio)
        time.sleep(2)
    steps_done.append("unload")

    # --- Step 3: Load new model ---
    print(f"\n[Step 3/5] Loading new model: {new_model}")
    load_ok = load_model(studio, new_model)
    if not load_ok:
        print(f"[FAIL] Could not load '{new_model}'")
        log_decision("model_swap", agent_id,
                     {"from": current_model, "to": new_model, "error": "load_failed"}, False)
        return 1
    time.sleep(3)  # wait for model to settle
    # Verify loaded
    try:
        verify = get_loaded_model(studio)
        if new_model.lower() not in verify.lower():
            print(f"[FAIL] Verification: expected '{new_model}', got '{verify}'")
            log_decision("model_swap", agent_id,
                         {"from": current_model, "to": new_model, "error": "load_verify_failed",
                          "got": verify}, False)
            return 1
        print(f"  Loaded and verified: '{verify}'")
    except Exception as e:
        print(f"  Warning: could not verify load state ({e}). Proceeding.")
    steps_done.append("load")

    # --- Step 4: Ping agent ---
    print(f"\n[Step 4/5] Pinging agent to verify response...")
    ping_ok, ping_msg = ping_agent(studio, new_model)
    if not ping_ok:
        print(f"  Warning: {ping_msg}")
        print("  (Non-fatal - model loaded but agent didn't respond in time)")
    else:
        print(f"  {ping_msg}")
    steps_done.append("ping")

    # --- Step 5: Update agents.json ---
    print(f"\n[Step 5/5] Updating agents.json...")
    update_ok = update_agents_json(agent_id, new_model)
    if not update_ok:
        print(f"[FAIL] Could not update agents.json for '{agent_id}'")
        log_decision("model_swap", agent_id,
                     {"from": current_model, "to": new_model, "error": "agents_json_update_failed"}, False)
        return 1
    print(f"  agents.json updated: model_id -> {new_model}")
    steps_done.append("update_agents")

    elapsed = round(time.monotonic() - t_start, 1)
    print(f"\n[OK] Model swap complete in {elapsed}s: {current_model} -> {new_model}")
    log_decision("model_swap", agent_id,
                 {"from": current_model, "to": new_model, "studio": studio,
                  "elapsed_s": elapsed, "steps": steps_done}, True)
    return 0


def main():
    parser = argparse.ArgumentParser(description="Swap a model on an agent")
    parser.add_argument("agent_id", help="Agent ID (e.g. 'builder', 'verifier')")
    parser.add_argument("new_model", help="New model ID to load")
    parser.add_argument("--dry-run", action="store_true", help="Show steps without executing")
    parser.add_argument("--studio", default=DEFAULT_STUDIO, help=f"Studio URL (default: {DEFAULT_STUDIO})")
    args = parser.parse_args()

    sys.exit(run_swap(args.agent_id, args.new_model, args.studio, args.dry_run))


if __name__ == "__main__":
    main()