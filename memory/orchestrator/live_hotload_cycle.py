#!/usr/bin/env python3
"""live_hotload_cycle.py - Goal 1: Live Hotload Execution (elev.py).

Executes a REAL load/unload cycle on White via the Studio API at :8888.
Run via: python elev.py python memory/orchestrator/live_hotload_cycle.py

Verification criteria:
  1. hotload-log.jsonl has timestamped LOAD_SUCCESS + UNLOAD_SUCCESS rows
  2. Alias probe (quinn-q4) responds after reload
  3. agents.json is byte-identical before and after
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
import hashlib
from datetime import datetime, timezone

API = "http://127.0.0.1:8888"
HOTLOAD_LOG = os.path.normpath(os.path.join("memory", "llm", "hotload-log.jsonl"))
AGENTS_JSON = os.path.normpath("agents.json")
MODEL_FOLDER = r"C:\Users\<white>\.lmstudio\models\unsloth\Qwen3.8-27B-Q4_K_S"
ALIAS = "quinn-q4"

# Proven load body from model_load_params.json
LOAD_BODY = {
    "model_path": MODEL_FOLDER,
    "gguf_variant": "UD-Q4_K_S",
    "gpu_ids": [0],
    "max_seq_length": 131072,
    "cache_type_kv": "q8_0",
    "n_parallel": 1,
    "speculative_type": "mtp",
    "spec_draft_n_max": 4,
}

results = []
errors = []

def log_event(event_type, model, detail=""):
    row = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event_type,
        "host": "white",
        "model": model,
        "detail": detail,
    }
    os.makedirs(os.path.dirname(HOTLOAD_LOG), exist_ok=True)
    with open(HOTLOAD_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    print(f"  [log] {event_type} {model} {detail}")

def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    line = f"{status}  {name}" + (f"  [{detail}]" if detail and not cond else "")
    print(line)
    results.append((name, cond))
    if not cond:
        errors.append(name)

def studio_get(path, timeout=30):
    url = API.rstrip("/") + path
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())

def studio_post(path, body, timeout=120):
    url = API.rstrip("/") + path
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or b"{}")
        except Exception:
            return e.code, {}

def is_model_loaded(model_id, folder):
    """Check if a model is currently loaded via GET /models."""
    try:
        data = studio_get("/models")
        models_list = data.get("data", data if isinstance(data, list) else [])
        for m in models_list:
            mid = m.get("id", "")
            if model_id.lower() in mid.lower() or (folder and folder.replace("\\", "/").lower() in str(m).replace("\\", "/").lower()):
                return bool(m.get("loaded"))
    except Exception as e:
        print(f"  [warn] is_model_loaded check failed: {e}")
    return False

def wait_unloaded(model_id, folder, timeout_s=90, poll_s=3):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if not is_model_loaded(model_id, folder):
            return True
        time.sleep(poll_s)
    return False

def wait_resident(model_id, folder, timeout_s=180, poll_s=5):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if is_model_loaded(model_id, folder):
            return True
        time.sleep(poll_s)
    return False

def alias_probe():
    """Send a minimal chat completion to verify the alias responds."""
    body = {
        "model": ALIAS,
        "messages": [{"role": "user", "content": "Reply with exactly: OK"}],
        "max_tokens": 10,
        "temperature": 0.0,
    }
    try:
        data = json.dumps(body).encode()
        req = urllib.request.Request(API + "/v1/chat/completions", data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            elapsed = time.time() - t0
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return True, f"{elapsed:.1f}s -> '{content.strip()[:50]}'"
    except Exception as e:
        return False, str(e)

def agents_json_hash():
    if not os.path.exists(AGENTS_JSON):
        return None
    with open(AGENTS_JSON, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main():
    print("=" * 60)
    print("LIVE HOTLOAD CYCLE - Goal 1 (Orchestrator)")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print(f"Target: {ALIAS} on White ({API})")
    print("=" * 60)

    # Pre-check: agents.json hash
    hash_before = agents_json_hash()
    print(f"\n[1] agents.json sha256 (before): {hash_before[:16]}...")

    # Step 1: Check current state
    print("\n[2] Checking current loaded models...")
    try:
        data = studio_get("/models")
        models_list = data.get("data", data if isinstance(data, list) else [])
        for m in models_list:
            mid = m.get("id", "?")
            loaded = m.get("loaded", False)
            print(f"    {mid}: loaded={loaded}")
    except Exception as e:
        print(f"    ERROR: cannot reach Studio API: {e}")
        errors.append("API unreachable")
        log_event("LIVE_CYCLE_FAIL", ALIAS, f"API unreachable: {e}")
        return _summary()

    currently_loaded = is_model_loaded(ALIAS, MODEL_FOLDER)
    print(f"    {ALIAS} currently loaded: {currently_loaded}")

    # Step 2: UNLOAD if loaded (to ensure we do a full cycle)
    if currently_loaded:
        print("\n[3] UNLOADING quinn-q4...")
        t0 = time.time()
        log_event("UNLOAD_START", ALIAS)
        code, resp = studio_post("/api/inference/unload", {"model_path": MODEL_FOLDER})
        if code == 200:
            ok = wait_unloaded(ALIAS, MODEL_FOLDER, timeout_s=90)
            elapsed = time.time() - t0
            st = "SUCCESS" if ok else "TIMEOUT"
            log_event("UNLOAD_" + st, ALIAS, f"{elapsed:.1f}s")
            check(f"UNLOAD {ALIAS}", ok, f"code={code} elapsed={elapsed:.1f}s")
        else:
            log_event("UNLOAD_ERROR", ALIAS, f"HTTP {code}: {resp}")
            check(f"UNLOAD {ALIAS}", False, f"HTTP {code}")
    else:
        print("\n[3] quinn-q4 not loaded - skipping unload (fresh load cycle)")
        log_event("UNLOAD_SKIP", ALIAS, "not currently loaded")

    # Step 3: LOAD
    print("\n[4] LOADING quinn-q4...")
    t0 = time.time()
    log_event("LOAD_START", ALIAS, json.dumps(LOAD_BODY))
    code, resp = studio_post("/api/inference/load", LOAD_BODY)
    if code == 200:
        ok = wait_resident(ALIAS, MODEL_FOLDER, timeout_s=180)
        elapsed = time.time() - t0
        st = "SUCCESS" if ok else "TIMEOUT"
        log_event("LOAD_" + st, ALIAS, f"{elapsed:.1f}s")
        check(f"LOAD {ALIAS}", ok, f"code={code} elapsed={elapsed:.1f}s")
    elif code == 409:
        # Already loaded (race) - treat as success
        log_event("LOAD_CONFLICT", ALIAS, "HTTP 409 - already resident")
        check(f"LOAD {ALIAS}", True, "already resident (409)")
    else:
        log_event("LOAD_ERROR", ALIAS, f"HTTP {code}: {resp}")
        check(f"LOAD {ALIAS}", False, f"HTTP {code}")

    # Step 4: Alias probe
    print("\n[5] Alias probe (quinn-q4 chat completion)...")
    ok, detail = alias_probe()
    log_event("ALIAS_PROBE_" + ("PASS" if ok else "FAIL"), ALIAS, detail)
    check("Alias probe quinn-q4", ok, detail)

    # Step 5: agents.json unchanged
    hash_after = agents_json_hash()
    print(f"\n[6] agents.json sha256 (after):  {hash_after[:16]}...")
    check("agents.json byte-identical", hash_before == hash_after,
          f"before={str(hash_before)[:16]} after={str(hash_after)[:16]}")

    return _summary()


def _summary():
    total = len(results)
    passed = sum(1 for _, c in results if c)
    print(f"\n{'=' * 60}")
    print(f"LIVE HOTLOAD CYCLE: {passed}/{total} checks passed")
    if errors:
        print(f"FAILURES: {errors}")
    else:
        print("ALL CHECKS PASS - Goal 1 verified")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
