#!/usr/bin/env python3
"""fleet_reload.py - Per-host model reload after boot.

Called by boot_recovery.py once Studio :8888 is confirmed up.
Loads the correct models for this host in proven order (Q8 first, then Q4 force_reload).
Polls /api/inference/loaded-models until both are resident before declaring success.
Logs to memory/ops/boot-recovery-log.jsonl (same file as boot_recovery.py).

Host configs sourced from memory/llm/hosts.md (verified 2026-11-14).
"""
import json, time, datetime, urllib.request, sys, os, platform

STUDIO = "http://127.0.0.1:8888"
HOSTNAME = platform.node()
LOG_PATH = os.path.join("memory", "ops", "boot-recovery-log.jsonl")

# Per-host model configs (from memory/llm/hosts.md, verified 2026-11-14)
# Each entry: list of load bodies in ORDER (Q8 first per proven recipe).
# model_path is relative to the user's .lmstudio\models directory.
HOST_MODELS = {
    "white": [
        {"model_path": "C:\\Users\\White\\.lmstudio\\models\\lmstudio-community\\Qwen3.8-27B-Q8_0",
         "gguf_variant": "Q8_0", "gpu_ids": [1], "max_seq_length": 32768,
         "cache_type_kv": "q8_0", "n_parallel": 1, "alongside": True, "force_reload": False},
        {"model_path": "C:\\Users\\White\\.lmstudio\\models\\unsloth\\Qwen3.8-27B-Q4_K_S",
         "gguf_variant": "UD-Q4_K_S", "gpu_ids": [0], "max_seq_length": 131072,
         "cache_type_kv": "q8_0", "n_parallel": 1, "speculative_type": "mtp",
         "spec_draft_n_max": 4, "llama_extra_args": ["--split-mode", "layer"],
         "force_reload": True},
    ],
    "red": [
        {"model_path": "C:\\Users\\Red\\.lmstudio\\models\\lmstudio-community\\Qwen3.8-27B-Q8_0",
         "gguf_variant": "Q8_0", "gpu_ids": [1], "max_seq_length": 16384,
         "cache_type_kv": "q8_0", "n_parallel": 1, "alongside": True, "force_reload": False},
        {"model_path": "C:\\Users\\Red\\.lmstudio\\models\\unsloth\\Qwen3.8-27B-GGUF",
         "gguf_variant": "UD-Q4_K_XL", "gpu_ids": [0], "max_seq_length": 65536,
         "cache_type_kv": "q8_0", "n_parallel": 1, "force_reload": True},
    ],
    "pale": [
        {"model_path": "C:\\Users\\pale\\.lmstudio\\models\\lmstudio-community\\Qwen3.8-27B-Q8_0",
         "gguf_variant": "Q8_0", "gpu_ids": [1], "max_seq_length": 32768,
         "cache_type_kv": "q8_0", "n_parallel": 1, "alongside": True, "force_reload": False},
        {"model_path": "C:\\Users\\pale\\.lmstudio\\models\\unsloth\\Qwen3.8-27B-Q4_K_S",
         "gguf_variant": "UD-Q4_K_S", "gpu_ids": [0], "max_seq_length": 65536,
         "cache_type_kv": "q8_0", "n_parallel": 1, "force_reload": True},
    ],
    "black": [
        {"model_path": "C:\\Users\\black\\.lmstudio\\models\\lmstudio-community\\Qwen3.8-27B-Q8_0",
         "gguf_variant": "Q8_0", "gpu_ids": [1], "max_seq_length": 32768,
         "cache_type_kv": "q8_0", "n_parallel": 1, "alongside": True, "force_reload": False},
        {"model_path": "C:\\Users\\black\\.lmstudio\\models\\unsloth\\Qwen3.8-27B-Q4_K_S",
         "gguf_variant": "UD-Q4_K_S", "gpu_ids": [0], "max_seq_length": 65536,
         "cache_type_kv": "q8_0", "n_parallel": 1, "force_reload": True},
    ],
}

def log(event, **kw):
    entry = {"ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             "host": HOSTNAME, "event": event, **kw}
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"[{HOSTNAME}] {entry}", flush=True)

def api_post(path, body):
    """POST to Studio API with JSON body. Returns (status, response_text)."""
    req = urllib.request.Request(
        f"{STUDIO}{path}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode()[:500]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:500]
    except Exception as e:
        return -1, str(e)[:200]

def api_get(path):
    """GET from Studio API. Returns (status, response_text)."""
    try:
        with urllib.request.urlopen(f"{STUDIO}{path}", timeout=15) as r:
            return r.status, r.read().decode()[:2000]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:500]
    except Exception as e:
        return -1, str(e)[:200]

def wait_no_generations(timeout_s=300):
    """Wait until active-generations count is 0 (safe to reload)."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        status, body = api_get("/api/inference/active-generations")
        if status == 200:
            try:
                count = json.loads(body).get("count", 0)
                if count == 0:
                    log("no_active_generations")
                    return True
            except json.JSONDecodeError:
                pass
        time.sleep(10)
    log("TIMEOUT_WAITING_FOR_NO_GENERATIONS")
    return False

def poll_until_loaded(model_path, timeout_s=600):
    """Poll /api/inference/loaded-models until model_path appears as loaded.
    The load API 200 is an async ack - must poll for actual residency."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        status, body = api_get("/api/inference/loaded-models")
        if status == 200:
            try:
                models = json.loads(body)
                # Check if our model is in the loaded list
                for m in models if isinstance(models, list) else []:
                    mp = m.get("model_path", "") or m.get("path", "")
                    if model_path.lower() in mp.lower():
                        log("model_resident", model=os.path.basename(model_path))
                        return True
            except json.JSONDecodeError:
                pass
        time.sleep(10)
    log("TIMEOUT_MODEL_NOT_RESIDENT", model=model_path)
    return False

def get_host_key():
    """Map hostname to config key."""
    h = HOSTNAME.lower()
    for key in HOST_MODELS:
        if key in h or (key == "white" and ".179" in h):
            return key
    # Try IP-based mapping
    import socket
    try:
        ip = socket.gethostbyname(HOSTNAME)
        if ".245" in ip: return "red"
        if ".39" in ip: return "pale"
        if ".99" in ip: return "black"
    except Exception:
        pass
    return None

def main():
    host_key = get_host_key()
    if not host_key:
        log("UNKNOWN_HOST_FOR_RELOAD", hostname=HOSTNAME)
        sys.exit(1)
    
    log("reload_start", host_config=host_key, models=len(HOST_MODELS[host_key]))
    
    # Step 1: Wait for no active generations
    if not wait_no_generations():
        log("ABORT_ACTIVE_GENERATIONS")
        sys.exit(1)
    
    # Step 2: Load models in order (Q8 first per proven recipe)
    all_loaded = True
    for i, load_body in enumerate(HOST_MODELS[host_key]):
        variant = load_body.get("gguf_variant", "?")
        log("loading_model", index=i + 1, variant=variant,
            gpu=load_body.get("gpu_ids"), ctx=load_body.get("max_seq_length"))
        
        status, resp = api_post("/api/inference/load", load_body)
        if status != 200:
            log("LOAD_FAILED", variant=variant, status=status, resp=resp[:200])
            all_loaded = False
            continue
        log("load_ack_received", variant=variant)
        
        # Step 3: Poll until actually resident (async ack!) 
        if not poll_until_loaded(load_body["model_path"]):
            all_loaded = False
    
    # Final verdict
    if all_loaded:
        log("RELOAD_COMPLETE", host=host_key, models=len(HOST_MODELS[host_key]))
        print(f"\n[{HOSTNAME}] ALL MODELS LOADED ({host_key})")
    else:
        log("RELOAD_PARTIAL", host=host_key)
        print(f"\n[{HOSTNAME}] PARTIAL RELOAD - see boot-recovery-log.jsonl")
        sys.exit(1)

if __name__ == "__main__":
    main()