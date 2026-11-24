# e2e_test.py — Agent Portal end-to-end verification (runs DETACHED via schtask PortalE2E).
# Why detached: this conversation itself runs on quinn-q4 and HOLDS the single inference
# slot for its whole turn (active-generations shows thread __LOCALID_0Ueu8kG during tool
# calls). Any chat probe fired from inside a turn queues behind itself -> deadlock.
# So: wait for idle, then drive the portal's /api/chat exactly like index.html does.
#
# Test A: solo quinn "Reply OK"   -> proves the 400 fix (portal now sends permission_mode=off
#          with enable_tools; before the fix Studio rejected every tool-bearing request).
# Test B: solo quinn web_search   -> proves real local tool execution + portal tool events.
import json, time, urllib.request, datetime

API    = "http://127.0.0.1:8888"
PORTAL = "http://127.0.0.1:8099"
LOG    = r"C:\Projects\AgentPortal\e2e_test.log"
RES    = r"C:\Projects\AgentPortal\e2e_result.json"

def log(msg):
    line = datetime.datetime.now().strftime("%H:%M:%S") + " " + str(msg)
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def active_count():
    try:
        with urllib.request.urlopen(API + "/api/inference/active-generations", timeout=10) as r:
            return json.loads(r.read().decode()).get("count", -1)
    except Exception as e:
        return f"err:{e}"

def portal_chat(agent_id, content, timeout=420):
    """POST /api/chat like index.html; returns (frames, full_text, tool_events, error)."""
    body = {"agent_id": agent_id, "mode": "solo", "kind": "prompt",
            "messages": [{"speaker": "user", "content": content}]}
    req = urllib.request.Request(PORTAL + "/api/chat",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    frames, full, tools, err = [], [], [], None
    with urllib.request.urlopen(req, timeout=timeout) as r:
        buf = b""
        for raw in r:
            buf += raw
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                line = line.strip()
                if not line.startswith(b"data:"):
                    continue
                p = line[5:].strip()
                if p == b"[DONE]":
                    return frames, full, tools, err
                try:
                    o = json.loads(p)
                except Exception:
                    continue
                frames.append(o)
                if o.get("error"):
                    err = o["error"]
                if o.get("content"):
                    full.append(o["content"])
                if o.get("tool"):
                    tools.append(o["tool"])
    return frames, full, tools, err

result = {"start": datetime.datetime.now().isoformat(), "tests": {}}

# ---- 0) wait for the inference slot to free (my turn must end first) ----
t0 = time.time()
while time.time() - t0 < 420:
    c = active_count()
    if c == 0:
        break
    log(f"waiting for idle, active-generations={c}")
    time.sleep(5)
result["idle_wait_s"] = round(time.time() - t0, 1)
log(f"idle after {result['idle_wait_s']}s (active={active_count()})")

# ---- A) 400-fix validation: plain solo prompt (portal still sends tool fields) ----
tA0 = time.time()
try:
    frames, full, tools, err = portal_chat("quinn", "Reply with exactly: OK")
    a = {"ok": (not err) and any("OK" in t.upper() for t in full),
         "secs": round(time.time() - tA0, 1), "error": err,
         "reply": "".join(full)[:200], "frames": len(frames)}
except Exception as e:
    a = {"ok": False, "secs": round(time.time() - tA0, 1), "exception": f"{type(e).__name__}: {e}"}
result["tests"]["A_validation_400_fix"] = a
log(f"TEST A: {json.dumps(a)[:300]}")

# ---- B) real tool execution: web_search through the portal ----
tB0 = time.time()
try:
    frames, full, tools, err = portal_chat(
        "quinn",
        "Use your web_search tool to search for 'top world news today'. "
        "Then reply with exactly one headline you found.")
    b = {"ok": (not err) and len(tools) >= 1 and len("".join(full).strip()) > 0,
         "secs": round(time.time() - tB0, 1), "error": err,
         "tool_events": len(tools),
         "tool_sample": json.dumps(tools[0])[:300] if tools else None,
         "reply": "".join(full)[:400], "frames": len(frames)}
except Exception as e:
    b = {"ok": False, "secs": round(time.time() - tB0, 1), "exception": f"{type(e).__name__}: {e}"}
result["tests"]["B_web_search_tool"] = b
log(f"TEST B: {json.dumps(b)[:400]}")

# ---- C) portal health after the run ----
try:
    with urllib.request.urlopen(PORTAL + "/api/memory", timeout=10) as r:
        result["portal_health"] = r.status
except Exception as e:
    result["portal_health"] = f"err:{e}"

result["end"] = datetime.datetime.now().isoformat()
result["verdict"] = "ALL_PASS" if (a.get("ok") and b.get("ok")) else "SEE_TESTS"
with open(RES, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=1)
log("DONE verdict=" + result["verdict"])
