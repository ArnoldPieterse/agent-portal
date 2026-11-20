"""
model_reload.py - One-command single-agent model reload (Runbook step B)
Part of Mechanic Goal 10: Runbook Automation (top-5)

Usage: python memory/mechanic/model_reload.py <agent_name> [--model MODEL_ID]

Idempotent: if the target model is already loaded for that agent, no-op.
Logs to memory/mechanic/runbook-executions.jsonl. Runtime <60s.
"""
import json, sys, time, pathlib, urllib.request
from datetime import datetime, timezone

STUDIO_URL = "http://127.0.0.1:8888"
AGENTS_PATH = pathlib.Path("agents.json")
LOG_PATH = pathlib.Path("memory/mechanic/runbook-executions.jsonl")


def log_entry(action: str, ok: bool, detail: str):
    entry = {"ts": datetime.now(timezone.utc).isoformat(), "script": "model_reload.py", "action": action, "ok": ok, "detail": detail[:200]}
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def api_get(path: str, timeout: float = 10.0):
    req = urllib.request.Request(f"{STUDIO_URL}{path}")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def api_post(path: str, data: dict, timeout: float = 30.0):
    body = json.dumps(data).encode()
    req = urllib.request.Request(f"{STUDIO_URL}{path}", data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def get_current_model() -> str:
    data = api_get("/api/v0/models/loaded")
    return data.get("model", "")


def load_model(model_id: str) -> bool:
    try:
        api_post("/api/v0/models/load", {"model": model_id})
        return True
    except Exception:
        return False


def unload_model() -> bool:
    try:
        api_post("/api/v0/models/unload", {})
        return True
    except Exception:
        return False


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0

    agent_name = sys.argv[1].lower()
    t_start = time.monotonic()

    # Look up target model from agents.json
    agents = json.loads(AGENTS_PATH.read_text())
    profile = agents.get(agent_name)
    if not profile:
        log_entry("unknown_agent", False, f"agent '{agent_name}' not in agents.json")
        print(f"[FAIL] Agent '{agent_name}' not found in agents.json")
        return 1

    target_model = profile.get("model_id", "")
    # Override with --model if provided
    if "--model" in sys.argv:
        idx = sys.argv.index("--model") + 1
        if idx < len(sys.argv):
            target_model = sys.argv[idx]

    if not target_model:
        log_entry("no_model_id", False, f"agent '{agent_name}' has no model_id")
        print(f"[FAIL] No model_id for agent '{agent_name}'")
        return 1

    # Check current state
    try:
        current = get_current_model()
    except Exception as e:
        log_entry("studio_unreachable", False, str(e)[:100])
        print(f"[FAIL] Studio unreachable: {e}")
        return 1

    if target_model.lower() in current.lower():
        elapsed = round(time.monotonic() - t_start, 2)
        log_entry("already_loaded", True, f"model '{target_model}' already loaded for {agent_name} ({elapsed}s)")
        print(f"[OK] Model '{target_model}' already loaded. No action needed.")
        return 0

    # Unload current, load target
    if current:
        unload_ok = unload_model()
        if not unload_ok:
            log_entry("unload_failed", False, f"could not unload '{current}'")
            print(f"[FAIL] Could not unload current model '{current}'")
            return 1
        time.sleep(2)

    load_ok = load_model(target_model)
    if not load_ok:
        log_entry("load_failed", False, f"could not load '{target_model}'")
        print(f"[FAIL] Could not load model '{target_model}'")
        return 1

    # Verify
    time.sleep(3)
    try:
        verify = get_current_model()
        if target_model.lower() in verify.lower():
            elapsed = round(time.monotonic() - t_start, 1)
            log_entry("reload_ok", True, f"{agent_name}: {current} -> {target_model} ({elapsed}s)")
            print(f"[OK] Model reloaded: {current} -> {target_model} ({elapsed}s)")
            return 0
        else:
            log_entry("verify_failed", False, f"expected '{target_model}', got '{verify}'")
            print(f"[FAIL] Verification failed: expected '{target_model}', got '{verify}'")
            return 1
    except Exception as e:
        log_entry("verify_error", False, str(e)[:100])
        print(f"[FAIL] Verification error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())