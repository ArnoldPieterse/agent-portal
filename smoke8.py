"""Smoke all EIGHT agents through the portal /api/chat (solo mode), expect <TAG>-OK.
White: orchestrator (Q8_0) + researcher (Q4). Black .99: builder + verifier.
Pale .39: designer + archivist. Red .245: scribe + mechanic.
Serial only (smoke6 lesson: no parallel smokes; local agents also queue behind this
chat's slot, so run DETACHED after a turn ends - see serial_e2e_wait.py pattern).
Writes smoke8_result.json incrementally."""
import json, time, urllib.request, urllib.error

PB = "http://127.0.0.1:8099"
out = {'started': time.strftime('%H:%M:%S'), 'results': {}}

def save():
    json.dump(out, open('smoke8_result.json', 'w'), indent=1)

def portal_chat(agent_id, tag, timeout=420):
    body = {"agent_id": agent_id, "mode": "solo", "kind": "prompt",
            "messages": [{"speaker": "You", "content": f"Reply with exactly: {tag}-OK"}]}
    req = urllib.request.Request(PB + "/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time(); content = ""; meta = None
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for raw in resp:
                line = raw.decode().strip()
                if not line.startswith("data:"): continue
                p = line[5:].strip()
                if p == "[DONE]": break
                try: o = json.loads(p)
                except Exception: continue
                content += o.get("content") or ""
                if o.get("meta"): meta = o["meta"]
        return {"secs": round(time.time()-t0, 1), "status": 200,
                "text": content.strip()[:300], "ok": f"{tag}-OK" in content, "meta": meta}
    except urllib.error.HTTPError as e:
        return {"secs": round(time.time()-t0, 1), "status": e.code,
                "text": e.read().decode()[:300], "ok": False, "meta": None}

AGENTS = [("orchestrator", "ORCH"), ("researcher", "RES"),
          ("builder", "BUILDER"), ("verifier", "VERIFIER"),
          ("designer", "DESIGNER"), ("archivist", "ARCHIVIST"),
          ("scribe", "SCRIBE"), ("mechanic", "MECHANIC")]

for agent_id, tag in AGENTS:
    r = portal_chat(agent_id, tag)
    out['results'][agent_id] = r
    save()
    print(agent_id, r['status'], 'OK' if r['ok'] else 'FAIL', f"{r['secs']}s",
          repr(r['text'][:120]), flush=True)

out['finished'] = time.strftime('%H:%M:%S')
out['verdict'] = 'ALL_OK' if all(v['ok'] for v in out['results'].values()) else 'PARTIAL'
save()
print('DONE', out['verdict'])
