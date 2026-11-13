import json, time, urllib.request

BASE = "http://127.0.0.1:8099"

def log(*a):
    print(*a, flush=True)

def chat(agent_id, kind, messages):
    body = json.dumps({"agent_id": agent_id, "mode": "group", "kind": kind,
                       "messages": messages}).encode()
    req = urllib.request.Request(BASE + "/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time(); full = ""; meta = None; blocked = None
    with urllib.request.urlopen(req, timeout=900) as r:
        buf = b""
        for raw in r:
            buf += raw
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                line = line.strip()
                if not line.startswith(b"data:"): continue
                p = line[5:].strip()
                if p == b"[DONE]": break
                try: obj = json.loads(p)
                except Exception: continue
                if obj.get("content"): full += obj["content"]
                if obj.get("meta"): meta = obj["meta"]
                if obj.get("blocked"): blocked = obj["blocked"]
    return full, meta, blocked, time.time() - t0

log("== start ==")
agents = json.load(urllib.request.urlopen(BASE + "/api/agents", timeout=10))
lst = agents["agents"] if isinstance(agents, dict) else agents
cast = [a for a in lst if a.get("id") in ("atlas", "quinn")] or lst[:2]
for a in cast: log(f"  {a['id']} -> {a.get('name')} ({a.get('model_id')})")

PROMPT = ("Pick a topic and discuss it with each other. Keep it brief - two or three "
          "exchanges max, then end with [CONCLUDED] once you have agreed on the outcome.")
history = [{"speaker": "You", "content": PROMPT}]

for a in cast:
    full, meta, blocked, dt = chat(a["id"], "prompt", history)
    log(f"== [{a['name']}] prompt reply ({dt:.0f}s) meta={meta}")
    log("   " + (full[:400].replace("\n", "\n   ") if full else "(empty)"))
    if full: history.append({"speaker": a["name"], "content": full})

settled = set(); guard = 0; calls = 0; MAX_CALLS = 12; lastConcluded = False
while guard < 8 and calls < MAX_CALLS:
    mem = json.load(urllib.request.urlopen(BASE + "/api/memory", timeout=10))
    if mem["inter_agent_replies"] >= mem["limit"]:
        log(f"-- budget exhausted {mem['inter_agent_replies']}/{mem['limit']}"); break
    any_new = False; guard += 1; calls += 1
    for a in cast:
        if a["id"] in settled: continue
        full, meta, blocked, dt = chat(a["id"], "cross-talk", history)
        if blocked: log(f"-- [{a['name']}] BLOCKED: {blocked}"); break
        m_c = bool(meta and meta.get("concluded"))
        m_s = bool(meta and meta.get("silent"))
        log(f"== [{a['name']}] cross-talk #{guard} ({dt:.0f}s) silent={m_s} concluded={m_c} counter={(meta or {}).get('inter_agent_replies')}/{(meta or {}).get('limit')}")
        log("   " + (full[:400].replace("\n", "\n   ") if full else "(empty)"))
        if full: history.append({"speaker": a["name"], "content": full}); any_new = True
        else: settled.add(a["id"])
        if m_c: lastConcluded = True; break
    if lastConcluded or not any_new: break

mem = json.load(urllib.request.urlopen(BASE + "/api/memory", timeout=10))
log(f"== final ==  concluded={lastConcluded}  counter={mem['inter_agent_replies']}/{mem['limit']}")
log("== done ==")
