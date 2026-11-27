"""context_bundle.py - build the single GET-able context + API-inputs file (2026-11-27).

User directive: "build the context and api inputs as a gettable file from any of the hosts,
and they can also request data."

One self-describing JSON document (context-bundle.json at project root) carrying everything a
client or agent on ANY fleet host needs to work against the portal:
  * context    - M-CODE map, module pointer indexes, hot notes, live goal state, round topic
  * api_inputs - every route from memory/portal/api-index.md PLUS input specs DERIVED FROM THE
                 LIVE SOURCE (body.get("key") per POST branch in agent_portal.py) plus the GEV
                 MCP tool schemas (the real-world data API)
  * fleet      - hosts, studio URLs, bundle URLs (:8199 on every host), models, GEV status
  * how_to_use - exactly how to GET this file and REQUEST DATA from any host

Served three ways (same bytes):
  1. White portal:   GET http://<white>:8099/api/context-bundle   (hub; regenerates if stale)
  2. Every host:     GET http://<host>:8199/context-bundle.json   (bundle_host.py, stdlib-only,
                     kept fresh by the 5-min SMB mirror pushing this file to C:\Projects\AgentPortal)
  3. On disk:        C:\Projects\AgentPortal\context-bundle.json on every host (SMB-mirrored)

Data requests: POST /api/data-request on White (hub, whole workspace + sandbox) or
POST :8199/data-request on any host (that host's own mirrored copy). See how_to_use in the bundle.

Everything here is best-effort with short timeouts; a dead GEV or unreachable host degrades to
honest {up:false} fields and NEVER raises into the caller (portal thread + mirror both call it).
"""
import json, os, re, time, hashlib

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # memory/portal -> root
BUNDLE_NAME = "context-bundle.json"
BUNDLE_PATH = os.path.join(HERE, BUNDLE_NAME)
MAX_AGE_S = 300          # portal regenerates on demand past this
REBUILD_EVERY_S = 600    # portal background thread cadence (mirror pushes within ~5 min after)

# ---------------------------------------------------------------- M-CODE + memory index

def _mcode_map():
    """Parse the MEMORY.md MCODE:BEGIN table -> {code: folder} (the SSOT legend)."""
    out = {}
    try:
        t = open(os.path.join(HERE, "MEMORY.md"), encoding="utf-8", errors="replace").read()
        m = re.search(r"<!-- MCODE:BEGIN -->\s*(.*?)\s*<!-- MCODE:END -->", t, re.S)
        if m:
            for tok in re.split(r"[,\n]", m.group(1)):
                if "|" in tok:
                    k, f = tok.split("|", 1)
                    out[k.strip()] = f.strip()
    except Exception:
        pass
    return out


def _module_pointers(mcode, per_folder=8):
    """For each top-level module: first N arrow lines of F/INDEX.md (the pointer index)."""
    out = {}
    for code, folder in mcode.items():
        if len(code) > 1 and code[1].islower():      # subfolder keys - skip, parents cover them
            continue
        idx = os.path.join(HERE, *folder.split("/"), "INDEX.md")
        ptrs = []
        try:
            for line in open(idx, encoding="utf-8", errors="replace"):
                m = re.match(r"^\s*->\s+(\S+)\s*(.*)$", line)
                if m:
                    ptrs.append({"path": m.group(1), "summary": m.group(2).strip()[:120]})
                if len(ptrs) >= per_folder:
                    break
        except Exception:
            pass
        out[code] = {"folder": folder, "pointers": ptrs}
    return out


def _hot_notes():
    """The Hot Notes bullets from MEMORY.md (the live working memory)."""
    notes = []
    try:
        t = open(os.path.join(HERE, "MEMORY.md"), encoding="utf-8", errors="replace").read()
        m = re.search(r"## Hot Notes\s*\n(.*?)(\n## |\Z)", t, re.S)
        if m:
            for line in m.group(1).splitlines():
                s = line.strip()
                if s.startswith("-"):
                    notes.append(s.lstrip("-").strip()[:300])
    except Exception:
        pass
    return notes


def _goal_block():
    try:
        t = open(os.path.join(HERE, "MEMORY.md"), encoding="utf-8", errors="replace").read()
        m = re.search(r"## GOAL[^\n]*\n(.*?)(\n## |\Z)", t, re.S)
        return (m.group(1).strip()[:1200] if m else "")
    except Exception:
        return ""


def _open_goals(per_agent=8):
    """Open goal titles per lane via the same parser /api/goals uses (goal_ledger.parse_agent_file)."""
    out = {}
    try:
        import sys
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        import goal_ledger as gl
        gdir = os.path.join(HERE, "memory", "goals")
        for f in sorted(os.listdir(gdir)):
            m = re.match(r"^([a-z]+)\.md$", f)
            if not m or f in ("testy.md",):
                continue
            try:
                items = gl.parse_agent_file(os.path.join(gdir, f))
            except Exception:
                continue
            op = [g for g in items if g.get("status") != "reached"]
            if op:
                out[m.group(1)] = {"open": len(op),
                                   "titles": [str(g.get("text"))[:200] for g in op[:per_agent]]}
    except Exception:
        pass
    return out


def _round_topic():
    try:
        d = json.load(open(os.path.join(HERE, "memory", "goals", "round_topic.json"), encoding="utf-8"))
        return {"current": (d.get("current") or None), "queue": (d.get("queue") or [])[:5]}
    except Exception:
        return {"current": None, "queue": []}


# ---------------------------------------------------------------- API inputs (code-derived)

def _api_routes_from_index():
    """Parse memory/portal/api-index.md -> [{method, path, purpose, memory_link}] (the documented SSOT)."""
    routes = []
    try:
        t = open(os.path.join(HERE, "memory", "portal", "api-index.md"), encoding="utf-8", errors="replace").read()
        for line in t.splitlines():
            m = re.match(r"^#\s+(GET|POST|PUT|DELETE)\s+(\S+)\s+(.*)$", line.strip())
            if not m:
                continue
            method, path, rest = m.group(1), m.group(2), m.group(3)
            # trailing M-CODE token (single letter/letter+digit, whitespace-separated) = memory link
            lm = re.search(r"\s+([A-Z][a-z]?\d*)\s*$", rest)
            link = lm.group(1) if lm else None
            purpose = (rest[:lm.start()] if lm else rest).strip()
            routes.append({"method": method, "path": path, "purpose": purpose[:160], "memory_link": link})
    except Exception:
        pass
    return routes


def _post_bodies_from_source():
    """Derive POST input specs from agent_portal.py itself: for each `if/elif p == "/api/x"` branch
    inside _do_POST, collect the body.get("key") reads in that branch. Faithful to live code -
    this is what 'API inputs' means here (what each endpoint actually accepts)."""
    specs = {}
    try:
        t = open(os.path.join(HERE, "agent_portal.py"), encoding="utf-8").read()
        i0 = t.find("def _do_POST(")
        if i0 < 0:
            return specs
        seg = t[i0:t.find("def do_PUT(", i0)]
        lines = seg.splitlines()
        branch_re = re.compile(r"^(\s*)(?:if|elif)\s+p(?:\.startswith)?\s*==?\s*[\"'](/api/[^\"']+)[\"']")
        branches = []   # (indent, path, start_line)
        for i, l in enumerate(lines):
            m = branch_re.match(l)
            if m:
                branches.append((len(m.group(1)), m.group(2), i))
        for bi, (ind, path, start) in enumerate(branches):
            end = len(lines)
            for j in range(start + 1, len(lines)):
                m2 = branch_re.match(lines[j])
                if m2 and len(m2.group(1)) <= ind:
                    end = j
                    break
            keys = []
            for l in lines[start:end]:
                for km in re.finditer(r'body\.get\([\"\']([^\"\']+)[\"\'](?:,\s*([^)]+))?\)', l):
                    k = km.group(1)
                    if k not in [x[0] for x in keys]:
                        dflt = (km.group(2) or "").strip()
                        keys.append((k, dflt[:40]))
            if keys:
                specs[path] = {"fields": [{"name": k, "default": d} for k, d in keys]}
    except Exception:
        pass
    return specs


def _gev_tools():
    """Live GEV MCP tool schemas (the real-world data API inputs); cached fallback if the globe is down."""
    cache = os.path.join(HERE, "memory", "world", "gev-tools-cache.json")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "cb_gev", os.path.join(HERE, "memory", "archivist", "gev_bridge.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        tools = mod.tools()
        try:
            os.makedirs(os.path.dirname(cache), exist_ok=True)
            with open(cache, "w", encoding="utf-8") as f:
                json.dump(tools, f, ensure_ascii=False)
        except Exception:
            pass
        return {"live": True, "tools": tools}
    except Exception:
        try:
            d = json.load(open(cache, encoding="utf-8"))
            return {"live": False, "cached_at": os.path.getmtime(cache), "tools": d}
        except Exception:
            return {"live": False, "tools": []}


# ---------------------------------------------------------------- fleet + GEV status

def _fleet():
    hosts = [{"name": "White", "ip": "127.0.0.1", "studio": "http://127.0.0.1:8888",
              "bundle_url": "http://127.0.0.1:8199/context-bundle.json",
              "portal": "http://127.0.0.1:8099"}]
    try:
        cfg = json.load(open(os.path.join(HERE, "memory_mirror_hosts.json"), encoding="utf-8"))
        for h in cfg.get("hosts", []):
            hosts.append({"name": h["name"], "ip": h["ip"],
                          "studio": "http://%s:8888" % h["ip"],
                          "bundle_url": "http://%s:8199/context-bundle.json" % h["ip"],
                          "mirror_status": h.get("status")})
    except Exception:
        pass
    # models per host (best-effort, 2.5s each; honest 'unknown' on failure)
    try:
        import urllib.request
        agents = json.load(open(os.path.join(HERE, "agents.json"), encoding="utf-8"))
        agents = agents if isinstance(agents, list) else agents.get("agents", [])
        keys = {}
        for a in agents:
            u = (a.get("studio") or "").rstrip("/")
            k = a.get("api_key") or ""
            if u and not u.startswith("http://127.0.0.1") and k:
                keys[u] = k
        for h in hosts:
            base = h["studio"]
            try:
                req = urllib.request.Request(base + "/v1/models",
                                             headers={"Authorization": "Bearer " + keys.get(base, "")})
                d = json.load(urllib.request.urlopen(req, timeout=2.5))
                h["models"] = [m.get("id") for m in d.get("data", [])][:10]
            except Exception:
                h["models"] = None   # unreachable or keyed - not an error state
    except Exception:
        pass
    return hosts


def _gev_status():
    try:
        import urllib.request
        up = urllib.request.urlopen("http://localhost:4173", timeout=2.5).status == 200
    except Exception:
        up = False
    return {"up": up, "url": "http://localhost:4173", "bridge": "POST /api/gev {op: ping|tools|call|query|annotate}"}


def _git_sha():
    try:
        import subprocess
        r = subprocess.run([os.path.join(HERE, "mingit", "cmd", "git.exe"), "rev-parse", "--short", "HEAD"],
                           cwd=HERE, capture_output=True, text=True, timeout=10, creationflags=0x08000000)
        return (r.stdout or "").strip() or None
    except Exception:
        return None


def _level_state():
    try:
        d = json.load(open(os.path.join(HERE, "memory", "levels.json"), encoding="utf-8"))
        return {"level": d.get("level", 0), "cycles": len(d.get("history") or [])}
    except Exception:
        return {"level": None, "cycles": None}


# ---------------------------------------------------------------- assembly

def build():
    mcode = _mcode_map()
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return {
        "meta": {
            "name": "agent-portal-context-bundle",
            "version": 1,
            "generated_at": ts,
            "git_sha": _git_sha(),
            "fleet_level": _level_state(),
            "canonical_host": "White",
            "note": ("One file = all context + all API inputs. GET-able from ANY host: "
                     "http://<host>:8199/context-bundle.json (or /api/context-bundle on White's portal). "
                     "Request data back via POST /data-request - see how_to_use."),
        },
        "how_to_use": {
            "get_this_file": [
                "http://127.0.0.1:8099/api/context-bundle   (White portal, hub)",
                "http://<host-ip>:8199/context-bundle.json  (any host: White/Red/Pale/Black via bundle_host.py)",
                "C:\\Projects\\AgentPortal\\context-bundle.json  (on every host's disk, SMB-mirrored)",
            ],
            "request_data": {
                "endpoint_hub": "POST http://127.0.0.1:8099/api/data-request",
                "endpoint_any_host": "POST http://<host-ip>:8199/data-request",
                "body": {"from": "who is asking (agent/host name, optional)",
                         "wants": ["{\"path\": \"memory/goals/designer.md\"}  -> file content (capped)",
                                   "{\"query\": \"stealth revenue\"}            -> memory-tree search hits"],
                         "max_bytes": "per-file cap, default 200000"},
                "semantics": ("Each host serves its OWN mirrored copy of the project; White's hub serves the "
                              "canonical workspace + agent sandbox. Responses include per-item ok/error so one "
                              "dead want never kills the batch."),
            },
            "api_inputs_below": "routes = documented index (SSOT memory/portal/api-index.md); post_bodies = derived from live agent_portal.py source; gev_tools = live MCP schemas of the real-world data layer",
        },
        "context": {
            "mcode_map": mcode,
            "modules": _module_pointers(mcode),
            "hot_notes": _hot_notes(),
            "goal_block": _goal_block(),
            "round_topic": _round_topic(),
            "open_goals": _open_goals(),
        },
        "api_inputs": {
            "routes": _api_routes_from_index(),
            "post_bodies": _post_bodies_from_source(),
            "gev_tools": _gev_tools(),
        },
        "fleet": {"hosts": _fleet(), "gev": _gev_status()},
    }


def write_if_stale(max_age_s=MAX_AGE_S, force=False):
    """Regenerate context-bundle.json when older than max_age_s (or forced). Returns (path, age_s, rebuilt)."""
    age = None
    try:
        age = time.time() - os.path.getmtime(BUNDLE_PATH)
    except OSError:
        pass
    rebuilt = False
    if force or age is None or age > max_age_s:
        try:
            d = build()
            tmp = BUNDLE_PATH + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False)
            os.replace(tmp, BUNDLE_PATH)
            rebuilt = True
            age = 0.0
        except Exception:
            pass   # serve whatever stale copy exists; a bundle failure must never break the caller
    try:
        age = time.time() - os.path.getmtime(BUNDLE_PATH)
    except OSError:
        age = None
    return BUNDLE_PATH, age, rebuilt


def sha12():
    """Short content hash for freshness checks (same idiom as index.html pinning)."""
    try:
        return hashlib.sha256(open(BUNDLE_PATH, "rb").read()).hexdigest()[:12]
    except Exception:
        return None


if __name__ == "__main__":
    p, age, rebuilt = write_if_stale(force=True)
    d = json.load(open(p, encoding="utf-8"))
    print("wrote", p, "rebuilt=%s" % rebuilt,
          "routes=%d post_specs=%d mcode_keys=%d gev_tools=%d hosts=%d" % (
              len(d["api_inputs"]["routes"]), len(d["api_inputs"]["post_bodies"]),
              len(d["context"]["mcode_map"]), len(d["api_inputs"]["gev_tools"].get("tools", [])),
              len(d["fleet"]["hosts"])))
