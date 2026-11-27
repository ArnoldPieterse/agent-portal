"""GEV MCP bridge (2026-11-27, Phase 8 step 55).

Spawns GEV's stdio MCP server (node server/mcp/stdio.js --api-base http://localhost:4173)
and speaks newline-delimited JSON-RPC 2.0 to it. Resident process with auto-respawn;
the portal exposes POST /api/gev {op: ping|tools|call, name, arguments}.

Gotchas fixed during bring-up:
- stderr must go to a FILE, not an unread PIPE (node blocks on full pipe -> hang).
- _ensure() must NOT take the lock itself: callers already hold it and threading.Lock
  is not reentrant (self-deadlock on the first tools/call).
"""
import json, os, subprocess, threading, time

GEV_ROOT = r"C:\Projects\gods-eye-view"
NODE = r"C:\Program Files\nodejs\node.exe"
API_BASE = "http://localhost:4173"
_lock = threading.Lock()
_proc = None
_idc = [0]


def _spawn():
    errlog = open(os.path.join(r"C:\Projects\AgentPortal", "_gev_mcp.log"), "ab")
    return subprocess.Popen(
        [NODE, os.path.join(GEV_ROOT, "server", "mcp", "stdio.js"), "--api-base", API_BASE],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errlog,
        cwd=GEV_ROOT, creationflags=0x8 | 0x200)


def _rpc(proc, method, params=None, notify=False, timeout=60):
    msg = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    if not notify:
        _idc[0] += 1
        msg["id"] = _idc[0]
    proc.stdin.write((json.dumps(msg) + "\n").encode())
    proc.stdin.flush()
    if notify:
        return None
    t0 = time.time()
    while time.time() - t0 < timeout:
        l = proc.stdout.readline()
        if not l:
            raise RuntimeError("gev mcp server closed stdout")
        try:
            r = json.loads(l)
        except Exception:
            continue
        if r.get("id") == msg["id"]:
            return r
    raise TimeoutError("gev mcp %s timed out after %ds" % (method, timeout))


def _ensure():
    """Caller must hold _lock."""
    global _proc
    if _proc is None or _proc.poll() is not None:
        try:
            if _proc is not None:
                _proc.kill()
        except Exception:
            pass
        _proc = _spawn()
        _rpc(_proc, "initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                   "clientInfo": {"name": "agent-portal", "version": "1.0"}})
        _rpc(_proc, "notifications/initialized", notify=True)
    return _proc


def tools():
    with _lock:
        r = _rpc(_ensure(), "tools/list")
    out = []
    for t in (r.get("result") or {}).get("tools", []):
        out.append({"name": t.get("name"),
                    "description": (t.get("description") or "")[:300],
                    "inputSchema": t.get("inputSchema")})
    return out


def call(name, arguments=None, timeout=90):
    with _lock:
        r = _rpc(_ensure(), "tools/call", {"name": name, "arguments": arguments or {}}, timeout=timeout)
    res = r.get("result") or {}
    content = res.get("content") or []
    text = "\n".join(c.get("text", "") for c in content if isinstance(c, dict))
    return {"ok": not res.get("isError"), "text": text[:20000], "raw_len": len(text)}


def ping():
    try:
        import urllib.request
        return urllib.request.urlopen(API_BASE, timeout=3).status == 200
    except Exception:
        return False
