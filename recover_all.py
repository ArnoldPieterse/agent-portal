# Provenance: header added 2026-11-15 by Orchestrator (Archivist goal 6 audit). Original: fleet-ops scripts (Arnold + agent legs); purpose in the docstring/comments below.
# recover_all.py — investigate Q4 wedge, then reload ALL models per memory/llm-instances.md recipe.
# Runs DETACHED (schtask RecoverAll). Waits for the current turn to finish before touching Q4,
# because this very conversation is served by Q4 (thread __LOCALID_0Ueu8kG bound to unsloth UD-Q4_K_S).
import json, time, urllib.request, urllib.error, subprocess, datetime, os

API   = "http://127.0.0.1:8888"
PORTAL= "http://127.0.0.1:8099"
def _resolve(base_dir, *names):
    """11-14: White folders may be pre- or post-rename (fleet convention = quant in name);
    prefer the new name, fall back to the old one so boot recovery works in either state."""
    for n in names:
        p = os.path.join(base_dir, n)
        if os.path.isdir(p):
            return p
    return os.path.join(base_dir, names[0])
Q4P   = _resolve(r"C:\Users\White\.lmstudio\models\unsloth", "Qwen3.8-27B-Q4_K_S", "Qwen3.8-27B-GGUF")
Q8P   = _resolve(r"C:\Users\White\.lmstudio\models\lmstudio-community", "Qwen3.8-27B-Q8_0", "Qwen3.8-27B-GGUF")
LOG   = r"C:\Projects\Workspace\recover_run.log"
RES   = r"C:\Projects\Workspace\recover_result.json"

result = {"start": datetime.datetime.now().isoformat(), "steps": {}}

def log(msg):
    line = datetime.datetime.now().strftime("%H:%M:%S") + " " + str(msg)
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def jreq(method, url, body=None, t=15):
    try:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method,
                                     headers={"Content-Type": "application/json"} if data else {})
        with urllib.request.urlopen(req, timeout=t) as r:
            raw = r.read().decode()
            try: return r.status, json.loads(raw), raw
            except Exception: return r.status, None, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode()[:500]
        try: return e.code, json.loads(raw), raw
        except Exception: return e.code, None, raw
    except Exception as e:
        return None, None, f"ERR {type(e).__name__}: {e}"

def vram():
    out = subprocess.run(["nvidia-smi","--query-gpu=index,memory.used","--format=csv,noheader,nounits"],
                         capture_output=True, text=True).stdout.strip()
    return [tuple(int(x) for x in l.split(",")) for l in out.splitlines()]

def servers():
    try:
        out = subprocess.run(["powershell","-NoProfile","-Command",
            "(Get-CimInstance Win32_Process -Filter \"Name='llama-server.exe'\") | ForEach-Object { $_.ProcessId.ToString() + ' :: ' + $_.CommandLine }"],
            capture_output=True, text=True, timeout=30).stdout.strip()
        return out[:3000]
    except Exception as e:
        return f"ERR {e}"

def active_count():
    s, d, raw = jreq("GET", API + "/api/inference/active-generations")
    return (d or {}).get("count", -1) if s == 200 else "err:" + str(raw)[:80]

def chat_probe(model, t=45):
    body = {"model": model, "messages": [{"role":"user","content":"Reply with the single word: pong"}],
            "max_tokens": 16, "temperature": 0, "stream": False}
    t0 = time.time()
    s, d, raw = jreq("POST", API + "/v1/chat/completions", body, t=t)
    dt = round(time.time() - t0, 1)
    if s == 200 and isinstance(d, dict) and d.get("choices"):
        m = d["choices"][0].get("message", {})
        txt = (m.get("content") or "") + ("|R:" if m.get("reasoning_content") else "")
        return {"ok": True, "secs": dt, "reply": txt[:80]}
    return {"ok": False, "secs": dt, "status": s, "raw": str(raw)[:300]}

# ---------- 0) wait for the current turn (this conversation runs on Q4) ----------
time.sleep(45)
t0 = time.time()
while time.time() - t0 < 300:
    c = active_count()
    if c == 0: break
    log(f"waiting for idle, active-generations={c}")
    time.sleep(5)
result["idle_wait_s"] = round(time.time() - t0, 1)
log(f"idle after {result['idle_wait_s']}s")

# ---------- 1) WEDGE INVESTIGATION (on the OLD Q4 instance, before reload) ----------
pre = {"active_generations": active_count(), "vram": vram(), "servers": servers()}
result["steps"]["pre_state"] = pre
probe1 = chat_probe("quinn-q4", t=45)
result["steps"]["wedge_probe_1"] = probe1
log(f"wedge probe 1 (quinn-q4): {json.dumps(probe1)[:200]}")
if not probe1["ok"]:
    cancel_s, cancel_d, cancel_raw = jreq("POST", API + "/api/inference/cancel", {}, t=15)
    result["steps"]["cancel_attempt"] = {"status": cancel_s, "body": str(cancel_d)[:200]}
    time.sleep(5)
    probe2 = chat_probe("quinn-q4", t=45)
    result["steps"]["wedge_probe_2_after_cancel"] = probe2
    log(f"wedge probe 2 (after cancel): {json.dumps(probe2)[:200]}")
result["wedge_detected"] = not probe1["ok"]

# ---------- 2) reload Q8 on GPU1 (alongside; does not touch Q4) ----------
q8_body = {"model_path": Q8P, "gguf_variant": "Q8_0", "gpu_ids": [1],
           "max_seq_length": 32768, "cache_type_kv": "q8_0", "n_parallel": 1,
           "speculative_type": "auto", "alongside": True, "force_reload": True}
s, d, raw = jreq("POST", API + "/api/inference/load", q8_body, t=900)
result["steps"]["load_q8"] = {"status": s, "body": str(raw)[:300]}
log(f"load Q8 -> {s}")
t0 = time.time(); ok8 = False
while time.time() - t0 < 420:
    v = vram()
    if len(v) > 1 and v[1][1] > 25000:
        ok8 = True; break
    time.sleep(6)
result["steps"]["q8_ready"] = {"ok": ok8, "wait_s": round(time.time()-t0,1), "vram": vram()}
log(f"Q8 ready={ok8} after {round(time.time()-t0,1)}s")

# ---------- 3) force-reload Q4 on GPU0 (fresh engine = clears any wedge) ----------
q4_body = {"model_path": Q4P, "gguf_variant": "UD-Q4_K_S", "gpu_ids": [0],
           "max_seq_length": 65536, "cache_type_kv": "q8_0", "n_parallel": 1,
           "speculative_type": "mtp", "spec_draft_n_max": 4,
           "llama_extra_args": ["--split-mode", "layer"], "force_reload": True}
s, d, raw = jreq("POST", API + "/api/inference/load", q4_body, t=900)
result["steps"]["load_q4"] = {"status": s, "body": str(raw)[:300]}
log(f"load Q4 -> {s}")
t0 = time.time(); ok4 = False
while time.time() - t0 < 420:
    v = vram()
    if len(v) > 0 and v[0][1] > 18000:
        ok4 = True; break
    time.sleep(6)
time.sleep(10)  # engine warmup
tail = {"ok": ok4, "wait_s": round(time.time()-t0,1), "vram": vram()}
result["steps"]["q4_ready"] = tail
log(f"Q4 ready={ok4} after {round(time.time()-t0,1)}s")

# ---------- 4) ground-truth verification (memory: nvidia-smi + cmdlines, never /v1/models alone) ----------
verify = {"vram": vram(), "servers": servers()}
s, d, raw = jreq("GET", API + "/v1/models")
try:
    verify["v1_models"] = [{"id": x["id"], "loaded": x.get("loaded"), "quant": x.get("quant"), "ctx": x.get("context_length")}
                           for x in d["data"]]
except Exception:
    verify["v1_models"] = str(raw)[:300]
result["verify"] = verify

def dual_ok():
    v = verify["vram"]
    sv = verify["servers"]
    # 11-14: accept pre- or post-rename folder names in the llama-server command lines
    q4_in  = ("unsloth\\Qwen3.8-27B-Q4_K_S" in sv) or ("unsloth\\Qwen3.8-27B-GGUF" in sv)
    q8_in  = ("lmstudio-community\\Qwen3.8-27B-Q8_0" in sv) or ("lmstudio-community\\Qwen3.8-27B-GGUF" in sv)
    return (len(v) >= 2 and v[0][1] > 18000 and v[1][1] > 25000 and q4_in and q8_in)
result["dual_ok"] = dual_ok()

# ---------- 5) functional probes via the SAME aliases the portal uses ----------
fp4 = chat_probe("quinn-q4", t=90)
result["steps"]["functional_quinn_q4"] = fp4
log(f"functional quinn-q4: {json.dumps(fp4)[:200]}")
fp8 = chat_probe("atlas-q8", t=90)
result["steps"]["functional_atlas_q8"] = fp8
log(f"functional atlas-q8: {json.dumps(fp8)[:200]}")

# ---------- 6) portal check (start it if down - post-reboot logon trigger) ----------
s, d, raw = jreq("GET", PORTAL + "/api/memory", t=10)
if s != 200:
    subprocess.run(["schtasks", "/run", "/tn", "PortalRun"], capture_output=True, text=True)
    time.sleep(8)
    s, d, raw = jreq("GET", PORTAL + "/api/memory", t=10)
result["portal_8099"] = {"status": s, "snippet": str(raw)[:150]}
log(f"portal :8099 -> {s}")

result["end"] = datetime.datetime.now().isoformat()
result["verdict"] = ("ALL_UP" if (dual_ok() and fp4["ok"] and fp8["ok"])
                     else "PARTIAL: see steps")
with open(RES, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=1)
log("DONE verdict=" + result["verdict"])
