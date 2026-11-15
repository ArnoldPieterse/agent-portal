#!/usr/bin/env python3
"""Multi-agent chat portal, backed by the Unsloth Studio desktop instance.

The portal is a thin web UI + proxy. Every LLM call goes to the local
Unsloth Studio /v1/chat/completions endpoint (the full harness: reasoning,
skills, RAG, tool execution). Nothing here loads models directly.
"""
import hashlib, json, mimetypes, os, re, shutil, subprocess, sys, threading, time, urllib.request, urllib.error, urllib.parse, uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8099
STUDIO = "http://127.0.0.1:8888"   # local Studio (White); remote hosts override per-agent


def studio_base(agent):
    """Per-agent Studio base URL (multi-host routing). Empty/missing = local Studio."""
    return (agent or {}).get("studio") or STUDIO


def studio_headers(agent, extra=None):
    h = {"Content-Type": "application/json"}
    key = (agent or {}).get("api_key") or ""
    if key:
        h["Authorization"] = "Bearer " + key
    if extra:
        h.update(extra)
    return h


def rag_base(agent):
    """RAG search host. Per-agent `rag_studio` override for remote agents whose
    knowledge base lives on White (local Studio holds rag.db); empty = chat host."""
    return (agent or {}).get("rag_studio") or studio_base(agent)


def rag_headers(agent, extra=None):
    """Headers for RAG calls. `rag_api_key` overrides; the agent's own key applies
    only when RAG runs on the chat host (no rag_studio override)."""
    h = {"Content-Type": "application/json"}
    a = agent or {}
    key = a.get("rag_api_key") or ""
    if not key and not a.get("rag_studio"):
        key = a.get("api_key") or ""
    if key:
        h["Authorization"] = "Bearer " + key
    if extra:
        h.update(extra)
    return h
HERE = os.path.dirname(os.path.abspath(__file__))
AGENTS_FILE = os.path.join(HERE, "agents.json")
MEMORY_FILE = os.path.join(HERE, "memory.md")   # HOT shared file (state line + counter + hot notes)
MEMORY_DIR = os.path.join(HERE, "memory")      # modular memory tree: INDEX.md pointer map + topic modules
# 2026-11-15: human message queue + per-mode chat history + run state (refresh-safe portal).
# LOCAL-ONLY runtime state - the .gitignore allowlist keeps these out of the public repo.
USER_MSGS_FILE = os.path.join(HERE, "user_messages.json")      # ts + text + per-agent checked booleans
CHAT_HISTORY_FILES = {"group": os.path.join(HERE, "chat_history_group.json"),
                      "solo": os.path.join(HERE, "chat_history_solo.json")}
RUN_STATE_FILE = os.path.join(HERE, "run_state.json")
UMQ_MAX = 200           # queue cap (oldest entries drop first)
HIST_MAX = 200          # persisted history cap per mode
# 2026-11-11: agent tool calls execute in Studio's shared sandbox, NOT in HERE. Portal API requests
# pass no session_id (spec: session_id scopes the "tool execution sandbox"), so everything lands in
# the "_default" sandbox - that is where agents' built files actually live and must be servable from.
def _find_sandbox_dir():
    """The ~-based path breaks when the portal is launched from a shell whose USERPROFILE points
    elsewhere (2026-11-11: tool shell had USERPROFILE=C:\Projects\Workspace -> sandbox refs 404'd).
    Fall back to scanning the real user profiles for Studio's _default sandbox."""
    d = os.path.expanduser(os.path.join("~", ".unsloth", "studio", "sandbox", "_default"))
    if os.path.isdir(d):
        return d
    users = os.path.join(os.environ.get("SystemDrive", "C:") + "\\", "Users")
    if os.path.isdir(users):
        for u in sorted(os.listdir(users)):
            cand = os.path.join(users, u, ".unsloth", "studio", "sandbox", "_default")
            if os.path.isdir(cand):
                return cand
    return d

SANDBOX_DIR = _find_sandbox_dir()
UPLOAD_DIR = os.path.join(SANDBOX_DIR, "uploads")   # human uploads land in the shared agent folder
MAX_UPLOAD_BYTES = 4 * 1024 * 1024 * 1024            # 4 GB per file (streamed to disk, never buffered)

# ---------------------------------------------------------------- workspace <-> sandbox sync (two-way)
# Agent tools run in Studio's shared _default sandbox (SANDBOX_DIR), not HERE. Shared project
# state must exist THERE so agents can read it with their own python/terminal tools (2026-11-13:
# mount asymmetry). r29 (2026-11-13): the mirror is now TWO-WAY so agent work lands in HERE (and
# therefore in git) instead of being clobbered by the next push:
#   * Root docs - TODO.md, MEMORY.md: PUSH-ONLY from HERE. OPS r5 (2026-11-13): an LWW pull of
#     these let a stale whole-file rewrite in any seat (fresh mtime) clobber canonical at the next
#     turn boundary - the only remaining writer path after the SMB mirror was exonerated.
#   * memory/ leaves: last-writer-wins BOTH directions (mtime decides; 0.5 s tolerance).
#   * Code/config - the rest of the git-tracked allowlist: PUSH-ONLY from HERE (merge-queue rule:
#     sandbox edits to code are experiments until merged via upgrade-plan.md).
#   * Everything else in the sandbox: NEW-ONLY pull - a file absent from HERE is copied home,
#     an existing workspace file is NEVER overwritten. Junk exclusions keep agent experiments
#     (mingit copies, project clones, uploads) out of the workspace.
# mtime-guarded (copy2 preserves mtime -> steady state touches nothing); every error swallowed -
# a sync hiccup must never break chat.
SYNC_LWW = ["TODO.md", "MEMORY.md"]   # root docs: LWW push only (OPS r5); memory/ leaves stay LWW both ways
PUSH_FALLBACK_ALLOWLIST = ["TODO.md", "MEMORY.md", "agents.json", "agent_portal.py", "index.html"]
PULL_EXCLUDE_DIRS = {"mingit", "uploads", "__pycache__", ".unsloth_sandbox", "node_modules",
                     "agentportal_v1-git", "_boot2", "_bootstrap_test", "gapfix-test"}
PULL_EXCLUDE_FILES = {"mingit.zip"}
PULL_MAX_BYTES = 20 * 1024 * 1024     # size guard for new-only pulls


def _git_allowlist():
    """The git-tracked file set (curated .gitignore allowlist, ~43 files). Fallback list when
    the repo is missing so sync degrades gracefully."""
    try:
        import subprocess
        # 2026-11-15: portal runs under pythonw - CREATE_NO_WINDOW keeps child git consoles invisible (popup complaint)
        r = subprocess.run([GIT_EXE, "ls-files"], cwd=HERE, capture_output=True, text=True, timeout=15,
                           creationflags=0x08000000)
        out = [l.strip().replace("\\", "/") for l in (r.stdout or "").splitlines() if l.strip()]
        if out:
            return out
    except Exception:
        pass
    return list(PUSH_FALLBACK_ALLOWLIST)


def _same_file(a, b):
    """r16 structural fix (Builder 2026-11-13): byte-identical check (size + md5).
    Lets the sync no-op on identical content regardless of mtime noise - foreign-stamped
    copies, CRLF/LF rewrites, backup restores - so steady state touches nothing and the
    destination mtime is preserved. Any read error -> False (fall back to mtime LWW)."""
    try:
        sa, sb = os.stat(a), os.stat(b)
        if sa.st_size != sb.st_size:
            return False
        ha = hashlib.md5(open(a, 'rb').read()).hexdigest()
        hb = hashlib.md5(open(b, 'rb').read()).hexdigest()
        return ha == hb
    except OSError:
        return False


def _sync_workspace_to_sandbox():
    """Two-way sync HERE <-> SANDBOX_DIR (semantics in the header above).
    Returns (pushed, pulled) relative-path lists; both empty in steady state."""
    pushed, pulled = [], []
    try:
        if not os.path.isdir(SANDBOX_DIR):
            return pushed, pulled
        # 1) LWW push: TODO.md / MEMORY.md + the whole memory/ tree (HERE wins only when newer)
        jobs = []
        for rel in SYNC_LWW:
            sp = os.path.join(HERE, rel)
            if os.path.isfile(sp):
                jobs.append((sp, os.path.join(SANDBOX_DIR, rel)))
        if os.path.isdir(MEMORY_DIR):
            for root, dirs, files in os.walk(MEMORY_DIR):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for f in files:
                    if f.startswith("."):
                        continue
                    sp = os.path.join(root, f)
                    jobs.append((sp, os.path.join(SANDBOX_DIR, "memory", os.path.relpath(sp, MEMORY_DIR))))
        for src, dst in jobs:
            try:
                ss = os.stat(src)
                ds = os.stat(dst) if os.path.exists(dst) else None
                if ds is not None and _same_file(src, dst):
                    continue   # r16 structural fix: byte-identical -> no-op, preserve mtime
                if ds is None or ss.st_mtime > ds.st_mtime + 0.5:
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(src, dst)
                    pushed.append(os.path.relpath(src, HERE).replace(os.sep, "/"))
            except OSError:
                pass
        # 2) Push-only code/config: rest of the git allowlist (never pulled back - merge queue)
        for rel in _git_allowlist():
            if rel in SYNC_LWW or rel.startswith("memory/") or rel == ".gitignore":
                continue
            src = os.path.join(HERE, rel.replace("/", os.sep))
            dst = os.path.join(SANDBOX_DIR, rel.replace("/", os.sep))
            if not os.path.isfile(src):
                continue
            try:
                ss = os.stat(src)
                ds = os.stat(dst) if os.path.exists(dst) else None
                if ds is not None and _same_file(src, dst):
                    continue   # r16 structural fix: byte-identical -> no-op, preserve mtime
                if ds is None or ss.st_mtime > ds.st_mtime + 0.5:
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(src, dst)
                    pushed.append(rel)
            except OSError:
                pass
        # 3) Pull back to HERE: memory/ leaves ONLY. OPS r5 (2026-11-13): TODO.md / MEMORY.md are
        # PUSH-ONLY - a stale whole-file rewrite in any seat gets a fresh mtime and an LWW pull
        # would clobber canonical at the next turn boundary. memory/ leaves stay LWW (agent work).
        sb_mem = os.path.join(SANDBOX_DIR, "memory")
        if os.path.isdir(sb_mem):
            for root, dirs, files in os.walk(sb_mem):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for f in files:
                    if f.startswith("."):
                        continue
                    sp = os.path.join(root, f)
                    rel = "memory/" + os.path.relpath(sp, sb_mem).replace(os.sep, "/")
                    dst = os.path.join(HERE, rel.replace("/", os.sep))
                    try:
                        ss = os.stat(sp)
                        ds = os.stat(dst) if os.path.exists(dst) else None
                        if ds is not None and _same_file(sp, dst):
                            continue   # r16 structural fix: byte-identical -> no-op, preserve mtime
                        if ds is None or ss.st_mtime > ds.st_mtime + 0.5:
                            os.makedirs(os.path.dirname(dst), exist_ok=True)
                            shutil.copy2(sp, dst)
                            pulled.append(rel)
                    except OSError:
                        pass
        # 4) New-only pull: any other sandbox file absent from HERE comes home (junk excluded)
        for root, dirs, files in os.walk(SANDBOX_DIR):
            relroot = os.path.relpath(root, SANDBOX_DIR).replace(os.sep, "/")
            dirs[:] = [d for d in dirs if not d.startswith(".") and d.lower() not in PULL_EXCLUDE_DIRS]
            for f in files:
                if f.startswith(".") or f.lower() in PULL_EXCLUDE_FILES:
                    continue
                sp = os.path.join(root, f)
                rel = (relroot + "/" + f) if relroot != "." else f
                dst = os.path.join(HERE, rel.replace("/", os.sep))
                try:
                    if os.path.exists(dst):
                        continue   # NEW-ONLY: never overwrite an existing workspace file
                    if os.path.getsize(sp) > PULL_MAX_BYTES:
                        continue
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(sp, dst)
                    pulled.append(rel)
                except OSError:
                    pass
    except Exception:
        pass
    return pushed, pulled


def _auto_commit():
    """Post-turn drift guard (Builder goal #5, 2026-11-13): commit whatever the two-way sync just
    moved so repo lag stays <= 1 turn. No-op when the tree is clean; errors swallowed."""
    try:
        if not os.path.isdir(os.path.join(HERE, ".git")):
            return None
        st = _git(["status", "--porcelain"])
        if not st["ok"] or not st["out"].strip():
            return None
        _git(["add", "-A"])
        c = _git(["commit", "-m", "auto: post-turn sync %s" % time.strftime("%Y-%m-%d %H:%M:%S")])
        if c["ok"] and "nothing to commit" not in (c["out"] + c["err"]).lower():
            head = _git(["log", "--oneline", "-1"])
            if head["ok"]:
                return head["out"].split(" ", 1)[0]
    except Exception:
        pass
    return None

def _safe_upload_path(rel):
    """Resolve an upload target inside UPLOAD_DIR. Returns (abs_path, clean_rel) or None.
    Anything is accepted as long as it stays under uploads/ - traversal, absolute paths,
    drive letters and NUL bytes are rejected."""
    try:
        rel = urllib.parse.unquote((rel or "").replace("\\", "/"))
    except Exception:
        return None
    if "\0" in rel:
        return None
    if re.match(r"^[A-Za-z]:", rel.lstrip("/")):
        return None   # absolute Windows path - reject outright
    if rel.startswith("/"):
        return None   # absolute POSIX-style path - reject outright (no silent relativizing)
    rel = rel.lstrip("/")
    if rel == "uploads":
        return None   # bare prefix, no file name
    if not rel.startswith("uploads/"):
        rel = "uploads/" + rel
    parts = [p for p in rel.split("/") if p not in ("", ".")]
    if len(parts) < 2 or any(p == ".." for p in parts):
        return None
    base = os.path.realpath(UPLOAD_DIR)
    full = os.path.realpath(os.path.join(base, *parts[1:]))   # parts[0] is the 'uploads' prefix itself
    if full != base and not full.startswith(base + os.sep):
        return None
    return full, "uploads/" + "/".join(parts[1:])

XTALK_LIMIT = 6                                  # FINITE cap, used when infinite_budget is OFF (default: ON = unlimited).
RESET_PHRASE = "counter reset"
_lock = threading.RLock()  # reentrant: _bump_counter/_reset_counter hold it while calling _write_memory

# ---- Per-message memory cycle (2026-11-14) --------------------------------------
# Every /api/chat turn runs: READMEM -> ADDCONTEXT -> main reply (+tools) -> STOREMEM.
# ReadMem/StoreMem are cheap auxiliary LLM rounds (low reasoning, tiny budget) that must
# NEVER break the main turn - they degrade to a no-op on any failure.
MEM_CYCLE_DEFAULT = True        # per-agent "mem_cycle": ReadMem before, StoreMem after
FAST_FIRST_DEFAULT = True       # per-agent "fast_first_reply": first reply to a human...
FIRST_REPLY_MAX_MSGS = 8        #   ...uses a low context window (last N messages)
FIRST_REPLY_REASONING = "low"   #   ...and low reasoning when the agent setting is "default"
MEM_LOOKUP_MAX_TOKENS = 250     # ReadMem routing call budget
MEM_STORE_MAX_TOKENS = 200      # StoreMem call budget
HOT_NOTE_MAX = 10               # keep only the newest N hot notes in memory.md
HOT_NOTE_CHARS = 140            # hard cap per stored note

# ---- Activity timeline (2026-11-12) --------------------------------------------
# Per-session audit log: every /api/chat turn appends JSONL events to
# activity/<session>.jsonl (start / tool / end / blocked / error / aborted).
# Survives portal restarts; read back via GET /api/activity?session=<id>.
ACTIVITY_DIR = os.path.join(HERE, "activity")
_act_lock = threading.Lock()


def _safe_session(sid):
    """Filename-safe session id. Empty/None -> shared 'default' file (legacy callers)."""
    s = re.sub(r"[^A-Za-z0-9_-]", "-", str(sid or "").strip())[:64]
    return s or "default"


def _act_log(session, ev):
    """Append one event to the session JSONL. Logging must NEVER break a chat."""
    try:
        os.makedirs(ACTIVITY_DIR, exist_ok=True)
        line = json.dumps({"ts": round(time.time(), 3), **ev}, ensure_ascii=False)
        with _act_lock:
            with open(os.path.join(ACTIVITY_DIR, session + ".jsonl"), "a", encoding="utf-8") as f:
                f.write(line + "\n")
    except Exception:
        pass


def _tool_names(tool):
    """Tool names from a stream 'tool' frame (object or list of call deltas)."""
    names = []
    for it in (tool if isinstance(tool, list) else [tool]):
        if not isinstance(it, dict):
            continue
        fn = it.get("function") or {}
        nm = it.get("name") or fn.get("name")
        if nm:
            names.append(str(nm)[:60])
    return names


def load_activity(session=None):
    """session None -> recent-sessions index; else that session's event list."""
    os.makedirs(ACTIVITY_DIR, exist_ok=True)
    if not session:
        out = []
        for fn in os.listdir(ACTIVITY_DIR):
            if not fn.endswith(".jsonl"):
                continue
            try:
                n, last_ts = 0, 0.0
                with open(os.path.join(ACTIVITY_DIR, fn), encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        n += 1
                        try:
                            last_ts = max(last_ts, float(json.loads(line).get("ts", 0)))
                        except Exception:
                            pass
                out.append({"session": fn[:-6], "events": n, "last_ts": last_ts})
            except OSError:
                continue
        out.sort(key=lambda o: o["last_ts"], reverse=True)
        return {"sessions": out[:50]}
    sess = _safe_session(session)
    events = []
    try:
        with open(os.path.join(ACTIVITY_DIR, sess + ".jsonl"), encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except Exception:
                    pass
    except OSError:
        return {"session": sess, "events": []}
    return {"session": sess, "events": events[-2000:]}

_MEMORY_TEMPLATE = """<!-- state: {"inter_agent_replies": 0, "last_reset_by": "", "infinite_budget": true} -->
# Shared Group Memory

Global context shared by ALL agents in this project. Agent-to-agent replies in the
group chat are UNLIMITED by default (infinite budget ON); set infinite_budget to false
in the state line above to cap them at %d per prompt. The counter below tracks replies;
it resets with each new prompt, or immediately when a member explicitly says "%s".

## Counter
- inter_agent_replies_this_prompt: 0 / ∞
- last_reset_by: —

## Notes
(leave short shared notes here; visible to every agent)
""" % (XTALK_LIMIT, RESET_PHRASE)

_STATE_RE = re.compile(r"<!--\s*state:\s*(\{.*?\})\s*-->", re.S)

# Local tool suite the Studio harness exposes (run on the host, not in a sandbox).
LOCAL_TOOLS = ["web_search", "python", "terminal", "edit_file", "render_html"]
REASONING_LEVELS = ["default", "off", "minimal", "low", "medium", "high", "max", "xhigh"]


def _norm_tools(v):
    if isinstance(v, list):
        return [t for t in v if t in LOCAL_TOOLS]
    return []


def default_agent_fields():
    return {"temperature": 0.7, "max_tokens": 0, "reasoning": "default",
            "tools": [], "run_tools_locally": True, "max_tool_calls": 0,
            "rag": False, "rag_kb_id": "", "studio": "", "api_key": "",
            "rag_studio": "", "rag_api_key": "",
            "mem_cycle": True, "fast_first_reply": True}


def apply_agent_fields(agent, data):
    """Copy + normalize the editable profile fields from a request body."""
    for k in ("name", "emoji", "color", "persona", "blurb"):
        if k in data:
            agent[k] = (data[k] or "").strip() if isinstance(data[k], str) else data[k]
    if "model_id" in data:
        agent["model_id"] = data["model_id"] or ""
    if "temperature" in data:
        try:
            agent["temperature"] = float(data["temperature"])
        except (TypeError, ValueError):
            pass
    if "max_tokens" in data:
        try:
            agent["max_tokens"] = max(0, int(data["max_tokens"]))   # 0 = Studio decides
        except (TypeError, ValueError):
            pass
    if isinstance(data.get("reasoning"), str) and data["reasoning"] in REASONING_LEVELS:
        agent["reasoning"] = data["reasoning"]
    if "tools" in data:
        agent["tools"] = _norm_tools(data["tools"])
    if "run_tools_locally" in data:
        agent["run_tools_locally"] = bool(data["run_tools_locally"])
    if "max_tool_calls" in data:
        try:
            v = int(data["max_tool_calls"])
            agent["max_tool_calls"] = v if v > 0 else 0             # 0 = Studio decides
        except (TypeError, ValueError):
            pass
    if "rag" in data:
        agent["rag"] = bool(data["rag"])
    if "rag_kb_id" in data:
        agent["rag_kb_id"] = str(data["rag_kb_id"] or "")
    if "studio" in data:
        agent["studio"] = str(data["studio"] or "").strip()   # remote host base URL (multi-host)
    if "api_key" in data:
        agent["api_key"] = str(data["api_key"] or "")          # Bearer key for that host
    if "rag_studio" in data:
        agent["rag_studio"] = str(data["rag_studio"] or "").strip()  # RAG host override (empty = chat host)
    if "rag_api_key" in data:
        agent["rag_api_key"] = str(data["rag_api_key"] or "")      # Bearer key for the RAG host
    if "mem_cycle" in data:
        agent["mem_cycle"] = bool(data["mem_cycle"])
    if "fast_first_reply" in data:
        agent["fast_first_reply"] = bool(data["fast_first_reply"])


def studio_post(path, payload, timeout=30, agent=None):
    req = urllib.request.Request(studio_base(agent) + path, data=json.dumps(payload).encode(),
                                 headers=studio_headers(agent), method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def scan_remote_models(base_url, api_key="", timeout=20):
    """GET {base}/v1/models on a (possibly remote) Studio - the add-agent model scan.
    Returns (http_code, payload). 502 + error text when the host/key is unreachable.
    Kept separate from do_POST so it unit-tests without a live portal."""
    base = str(base_url or "").strip().rstrip("/")
    if not base:
        return 400, {"error": "base_url required", "data": []}
    if "://" not in base:                       # be lenient: host:port -> http://host:port
        base = "http://" + base
    h = {}
    key = str(api_key or "").strip()
    if key:
        h["Authorization"] = "Bearer " + key
    try:
        with urllib.request.urlopen(urllib.request.Request(base + "/v1/models", headers=h),
                                    timeout=timeout) as r:
            return 200, json.load(r)
    except Exception as e:
        return 502, {"error": str(e), "data": []}

# ---- Fleet Status panel (2026-11-13, 8-agent round-table decision) ----
FLEET_TTL = 15          # seconds; last_seen older than this => "unknown"
FLEET_PROBE_TIMEOUT = 2 # seconds per sub-probe; parallel probes keep a full snapshot < 5s
                        # even with all remotes down (a dead host fails its first sub-probe)
FLEET_MODELS_TTL = 30   # seconds; /v1/models refetch interval - the loaded-model list
                        # changes rarely, and Studio's /v1/models can stall >2s while a
                        # generation is active (observed 2026-11-15), so fetch on TTL and
                        # fall back to the last known list rather than failing the host.
_fleet_cache = {}       # base -> ts of last successful probe (stale aging)
_fleet_dead = {}        # base -> ts of last FAILED probe (negative cache: no re-probe within FLEET_TTL)
_fleet_models_cache = {}  # base -> (ts, [models]) - survives transient /v1/models stalls
_fleet_lock = threading.Lock()

def _fleet_probe(base, api_key="", timeout=3):
    """One lightweight per-host probe: active-generations + /v1/models (metadata only,
    no inference load; runs only when a human refreshes the panel). Short timeout so a
    dead host can't hang /api/fleet. Returns {generations, models} when the host's
    Studio answers its liveness endpoint, else None (= unknown)."""
    b = base.rstrip("/")
    h = {}
    if api_key:
        h["Authorization"] = "Bearer " + str(api_key)
    try:
        with urllib.request.urlopen(urllib.request.Request(b + "/api/inference/active-generations", headers=h), timeout=timeout) as r:
            gen = int(json.load(r).get("count", 0))
    except Exception:
        return None
    # AG answered => the host IS reachable; state derives from generations. The model
    # list is display-only: fetch on TTL, fall back to the last known list (or empty)
    # when /v1/models stalls - never demote a live host to unknown for it.
    now = time.time()
    cached = _fleet_models_cache.get(b)
    if cached and now - cached[0] < FLEET_MODELS_TTL:
        models = cached[1]
    else:
        code, payload = scan_remote_models(b, api_key, timeout=timeout)
        if code != 200:
            models = cached[1] if cached else []
        else:
            models = []
            for m in (payload or {}).get("data", []):
                mid = str(m.get("id", ""))
                if "loaded" in m and not m["loaded"]:
                    continue
                qm = re.search(r"(UD-)?(Q\d+[A-Z0-9_]*|F16|BF16)", mid)
                models.append({"id": mid, "quant": qm.group(2) if qm else ""})
            _fleet_models_cache[b] = (now, models)
    return {"generations": gen, "models": models}

def _fleet_snapshot():
    """GET /api/fleet: live view of every host in agents.json (+ local Studio).
    State definitions (locked in round-table): busy = >=1 active generation on that
    Studio; idle = reachable with none; unknown = probe failed (last_seen then ages
    from cache; client renders stale/unknown, never green/idle).
    Budget: probes run IN PARALLEL with FLEET_PROBE_TIMEOUT and dead hosts are
    negatively cached for FLEET_TTL, so a full snapshot stays inside the panel's 5s
    refresh window even with every remote powered down (verified 2026-11-15 by
    memory/verifier/fleet_crosscheck.py)."""
    hosts, order = {}, []
    for a in load_agents().get("agents", []):
        b = studio_base(a).rstrip("/")
        if b not in hosts:
            hosts[b] = {"key": a.get("api_key") or "", "agents": []}
            order.append(b)
        hosts[b]["agents"].append(a.get("name"))
    local = STUDIO.rstrip("/")
    if local not in hosts:
        hosts[local] = {"key": "", "agents": []}
        order.insert(0, local)
    now = time.time()

    def probe(b):
        with _fleet_lock:
            cached_dead = (now - _fleet_dead.get(b, 0)) < FLEET_TTL
        if cached_dead:
            return None
        res = _fleet_probe(b, hosts[b]["key"], timeout=FLEET_PROBE_TIMEOUT)
        with _fleet_lock:
            if res is not None:
                _fleet_cache[b] = time.time()
                _fleet_dead.pop(b, None)
            else:
                _fleet_dead[b] = time.time()
        return res

    results = {}
    with ThreadPoolExecutor(max_workers=max(1, len(order))) as ex:
        futs = {ex.submit(probe, b): b for b in order}
        for f in as_completed(futs):
            b = futs[f]
            try:
                results[b] = f.result()
            except Exception:
                results[b] = None

    rows = []
    for b in order:
        h = hosts[b]
        name = "White (local)" if b == local else b.split("//")[-1].split(":")[0]
        row = {"host": name, "base": b, "agents": h["agents"], "models": [],
               "generations": 0, "state": "unknown", "last_seen": None, "reason": ""}
        res = results.get(b)
        with _fleet_lock:
            if res is None:
                row["last_seen"] = _fleet_cache.get(b)
                row["reason"] = ("unreachable" if row["last_seen"] is None else
                                 "stale (%ds)" % int(now - row["last_seen"]))
        if res is not None:
            row.update(res)
            row["state"] = "busy" if res["generations"] > 0 else "idle"
            row["last_seen"] = now
        rows.append(row)
    return {"ts": now, "ttl": FLEET_TTL, "hosts": rows}


def _rag_search(agent, query):
    """Search the agent's RAG host for `query` and format the hits. Never raises -
    a RAG hiccup must not break a chat turn. Reused by ReadMem (memory cycle)."""
    q = (query or "").strip()
    if not q:
        return ""
    try:
        payload = {"query": q[:600], "top_k": 4}
        kb = agent.get("rag_kb_id") or ""
        if kb:
            payload["kb_id"] = kb
        req = urllib.request.Request(rag_base(agent) + "/api/rag/search",
                                     data=json.dumps(payload).encode(),
                                     headers=rag_headers(agent), method="POST")
        with urllib.request.urlopen(req, timeout=25) as r:
            res = json.load(r)
    except Exception:
        return ""
    hits = (res.get("results") or res.get("hits") or res.get("chunks") or []) \
        if isinstance(res, dict) else (res if isinstance(res, list) else [])
    blocks = []
    for h in hits[:4]:
        if isinstance(h, dict):
            txt = (h.get("text") or h.get("content") or h.get("snippet") or "").strip()
            src = (h.get("source") or h.get("document") or h.get("title") or "")
        else:
            txt, src = str(h).strip(), ""
        if txt:
            blocks.append("- " + ((src + ": ") if src else "") + txt[:700])
    if not blocks:
        return ""
    return ("RETRIEVED CONTEXT (from your RAG knowledge base; use when relevant):\n"
            + "\n".join(blocks))


def rag_prefetch(agent, messages):
    """If the agent has RAG on, pull relevant docs and fold them into the system
    prompt. Never raises - a RAG hiccup must not break a chat turn."""
    if not agent.get("rag"):
        return ""
    q = ""
    for m in reversed(messages or []):
        c = (m.get("content") or "").strip()
        if c and (m.get("speaker") or "").strip().lower() == "you":
            q = c
            break
    if not q:
        for m in reversed(messages or []):
            c = (m.get("content") or "").strip()
            if c:
                q = c
                break
    return _rag_search(agent, q)


def load_agents():
    with _lock:
        if os.path.exists(AGENTS_FILE):
            try:
                return json.load(open(AGENTS_FILE, encoding="utf-8"))
            except Exception:
                pass
    seed = {"agents": [
        {"id": "a-nova", "name": "Nova", "emoji": "\U0001F680", "color": "#3ddc84",
         "model_id": "unsloth/Qwen3.5-9B-GGUF", "temperature": 0.7, "max_tokens": 0,
         "reasoning": "default", "tools": [], "run_tools_locally": True, "max_tool_calls": 0,
         "rag": False, "rag_kb_id": "",
         "blurb": "Product-minded helper; concise and practical.",
         "persona": "You are Nova, a product-minded assistant. Be concise, concrete and practical. Prefer short paragraphs and bullet points."},
        {"id": "a-iris", "name": "Iris", "emoji": "\U0001F3AF", "color": "#b98cff",
         "model_id": "unsloth/gpt-oss-20b-gguf", "temperature": 0.9, "max_tokens": 0,
         "reasoning": "default", "tools": [], "run_tools_locally": True, "max_tool_calls": 0,
         "rag": False, "rag_kb_id": "",
         "blurb": "Creative writer; vivid and playful.",
         "persona": "You are Iris, a creative writer. Be vivid, playful and imaginative. Vary sentence rhythm and use concrete imagery."},
    ]}
    with _lock:
        json.dump(seed, open(AGENTS_FILE, "w", encoding="utf-8"), indent=2)
    return seed


def save_agents(data):
    with _lock:
        json.dump(data, open(AGENTS_FILE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


def get_agent(aid):
    for a in load_agents()["agents"]:
        if a["id"] == aid:
            return a
    return None


def build_system_prompt(agent, mode, all_agents, rag_context="", shared_memory="",
                        kind="prompt", lookup_context=""):
    parts = [agent.get("persona", "").strip()]
    if mode == "group":
        others = [f"- {a['name']}: {a.get('blurb') or a.get('persona','')[:120]}"
                  for a in all_agents if a["id"] != agent["id"]]
        lines = ["You are one of several AI agents sharing this group chat.",
                 "Other agents present:"] + others + ["Rules:"]
        if kind == "prompt":
            # First phase: the human's new message is addressed to the WHOLE group, so
            # every agent in the cast is expected to answer. (Previously the cross-talk
            # silence rules leaked here and Quinn went [SILENT] on ordinary greetings.)
            lines += [
              "- A new human message was just sent to the WHOLE group; other agents may have answered already.",
              "- Give your own brief response from your perspective (2-4 sentences). Do NOT reply [SILENT]",
              "  just because another agent already replied - only stay silent if the message clearly targets that other agent exclusively.",
            ]
        else:
            lines += [
              "- Reply only when directly addressed, or when you can add real value to the latest message.",
              "- If you have nothing meaningful to add to the latest message, reply with exactly [SILENT] - an empty"
              "  reply is never acceptable; the single token [SILENT] IS your silence.",
              "- When another agent just answered well, stay brief or do not repeat them.",
              "- Satisfaction check: when the discussion has reached a natural conclusion (you agree, or both",
              "  sides have fully stated their positions and nothing new remains), start your reply with",
              "  [CONCLUDED] followed by ONE sentence summarizing the outcome - this ends the round for everyone.",
            ]
        lines += [
             "- You MAY respond to another agent's message (challenge it, build on it),",
             f"  but the group allows at most {XTALK_LIMIT} agent-to-agent replies per human prompt;",
             f'  a member saying "{RESET_PHRASE}" resets that counter.',
             "- You MUST respond when another agent addresses you by name or asks you a question directly.",
             "- Private messages: write [DM @Name] ... to send text that ONLY that agent can see "
             "(everyone else sees a lock chip). Use for direct questions or sensitive hand-offs; "
             "text outside the markers stays public.",
             "- Project memory is modular: memory/INDEX.md is the pointer map. With python/terminal tools",
             "  (if enabled), grep it and read only the module you need - never paste whole modules into chat.",
             "- Keep replies short (2-4 sentences) unless asked to expand.",
             "- Address other agents by name when replying to them."]
        parts.append("\n".join(lines))
    if agent.get("tools"):
        # 2026-11-10: group test "build a calculator app" - both agents CLAIMED builds ("Built and
        # rendered above") but never called a tool; no file existed on disk. Tool discipline rule.
        # 2026-11-11: tools actually run in Studio's shared sandbox (SANDBOX_DIR), not the project
        # workspace; agents must report RELATIVE paths so the portal can turn them into links.
        parts.append(
            "TOOLS: you have local tools (" + ", ".join(agent["tools"]) + ") that run on this host."
            " When the human asks you to build, create, or modify a file/app/snippet, DO IT with your"
            " tools - write real files into your working directory. Never say something is 'built',"
            " 'rendered', or 'done' unless a tool call in THIS reply succeeded; if a tool fails, say"
            " exactly what failed and what is still missing."
            " Your tool working directory is a shared agent folder: the human reaches your files"
            " through the portal by RELATIVE path (e.g. calculator-app/index.html). When reporting"
            " created files, use exactly that relative form as shown in your tool results - never"
            " invent drive letters or absolute paths. If you ever reported an absolute path or a"
            " drive letter (e.g. Z:\\...), it was wrong: restate that file by its relative path from"
            " your working directory.")
    if shared_memory:
        parts.append("SHARED GROUP MEMORY (global file memory.md, visible to all agents):\n"
                     + shared_memory.strip())
    if rag_context:
        parts.append(rag_context)
    if lookup_context:   # ReadMem output (2026-11-14): unlabelled, so solo/DM stays clean
        parts.append(lookup_context)
    return "\n".join(parts)


# ---------------------------------------------------------------- private messaging
# [DM @Name] ... opens a private segment visible ONLY to that agent (and its sender).
# Privacy is enforced HERE at prompt-build time: every /api/chat request gets the viewer's
# own redacted view of the thread, so remote agents on other hosts never see foreign DMs.

def parse_dm_segments(text):
    """Split a reply into [(kind, target, body)]: ("public", None, str) and ("dm", target_lower, str).
    A [DM @Name] marker opens a private segment running to the next marker or end of text;
    text before the first marker is public. Marker syntax is case-insensitive; empty segments
    are dropped. No markers -> single public segment (or [])."""
    t = (text or "").strip("\n")
    if not t.strip():
        return []
    marks = [(m.start(), m.end(), m.group(1).strip().lstrip("@").strip().lower())
             for m in re.finditer(r"\[DM\b\s*@?\s*([^\]\n]+?)\s*\]", t, re.I)]
    if not marks:
        return [("public", None, t)]
    segs = []
    prev = 0
    for i, (s, e, target) in enumerate(marks):
        pub = t[prev:s].strip()
        if pub:
            segs.append(("public", None, pub))
        end = marks[i + 1][0] if i + 1 < len(marks) else len(t)
        body = t[e:end].strip()
        if body.strip():
            segs.append(("dm", target, body))
        prev = end
    return segs


def render_dm_view(segs, viewer_name, sender_name):
    """Render parsed segments as the text a given agent should see: public text untouched,
    DMs addressed to the viewer in full (labelled private), everything else a lock chip."""
    vn = (viewer_name or "").lower()
    out = []
    for kind, target, body in segs:
        if kind == "public":
            out.append(body)
        elif target == vn:
            out.append("[Private message from %s]: %s" % (sender_name, body))
        else:
            out.append("\U0001F512 [private message to %s]" % target)
    return "\n".join(out).strip()


def to_openai_messages(agent, messages, mode, all_agents, rag_context="", shared_memory="",
                       kind="prompt", lookup_context=""):
    msgs = [{"role": "system",
             "content": build_system_prompt(agent, mode, all_agents, rag_context,
                                            shared_memory, kind, lookup_context)}]
    def _human(m):
        spk = (m.get("speaker") or "").strip()
        # Leniency: raw API clients send role=="user" without a speaker field;
        # the browser always sends speaker "You", so behavior is unchanged there.
        return spk.lower() == "you" or (not spk and (m.get("role") or "").lower() == "user")

    last_user = -1
    for i, m in enumerate(messages):
        if _human(m):
            last_user = i
    for i, m in enumerate(messages):
        who = (m.get("speaker") or "").strip()
        content = (m.get("content") or "").strip()
        if not content:
            continue
        if _human(m):
            shown = content
            if mode == "group":
                # Human-typed [DM @Name]: same per-viewer redaction as agent DMs - each
                # agent sees public text + DMs addressed to them only; others see a lock
                # chip. Unknown targets fail-open (no redaction) so content is never lost.
                segs = parse_dm_segments(content)
                dms = [t for k, t, b in segs if k == "dm"]
                if dms:
                    known = {a["name"].lower() for a in all_agents}
                    if all(t in known for t in dms):
                        shown = render_dm_view(segs, agent["name"], who or "You")
            msgs.append({"role": "user", "content": shown})
        else:
            if i > last_user:
                # Own past replies stay as assistant turns (continuity).
                # In group mode, OTHER agents' words must be user-role: if a
                # foreign reply lands as the final assistant turn, the model
                # sees no open user prompt and emits nothing (empty bubble).
                own = (mode != "group") or (who.lower() == agent["name"].lower())
                role = "assistant" if own else "user"
                prefix = "" if own else f"[{who}]: "
                shown = content
                if not own and mode == "group":
                    # DM redaction: the viewer sees public text + DMs addressed to them only.
                    # Unknown targets (not in the roster) disable redaction for this message -
                    # a [DM @Nobody] is just text, and hiding it would lose content for everyone.
                    segs = parse_dm_segments(content)
                    dms = [t for k, t, b in segs if k == "dm"]
                    if dms:
                        known = {a["name"].lower() for a in all_agents}
                        if all(t in known for t in dms):
                            shown = render_dm_view(segs, agent["name"], who)
                msgs.append({"role": role, "content": prefix + shown})
    return msgs


# ---------------------------------------------------------------- shared memory

# ---------------------------------------------------------------- user message queue (2026-11-15)
# Human messages sent while the group is working land in USER_MSGS_FILE instead of being
# dropped. Every group prompt build (prompt phase AND cross-talk rounds) injects this
# agent's pending in-scope entries into its system prompt and marks them seen for that
# agent once the request reaches Studio. @Name entries are private: only the named agent
# sees/checks them. The frontend polls /api/user-messages for the spinner state.
_umq_lock = threading.Lock()

def _umq_read():
    try:
        with open(USER_MSGS_FILE, encoding="utf-8") as fh:
            d = json.load(fh)
        if isinstance(d, dict) and isinstance(d.get("messages"), list):
            return d
    except Exception:
        pass
    return {"messages": []}

def _umq_write(d):
    tmp = USER_MSGS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False)
    os.replace(tmp, USER_MSGS_FILE)

def _umq_scope(m, all_names):
    """Agents an entry is addressed to (empty mentions = broadcast). Unknown names drop out."""
    names = m.get("mentions") or list(all_names)
    return [n for n in names if n in all_names]

def umq_add(text, mentions=None):
    text = (text or "").strip()[:20000]
    if not text:
        return None
    with _umq_lock:
        d = _umq_read()
        entry = {"id": "um-%s-%s" % (time.strftime("%Y%m%d-%H%M%S"), uuid.uuid4().hex[:6]),
                 "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                 "text": text,
                 "mentions": [str(x).strip() for x in (mentions or []) if str(x).strip()],
                 "checked": {}}
        d["messages"].append(entry)
        while len(d["messages"]) > UMQ_MAX:
            d["messages"].pop(0)
        _umq_write(d)
    return entry

def umq_pending_for(name, all_names):
    """Entries addressed to `name` that it has not seen yet."""
    with _umq_lock:
        d = _umq_read()
        out = []
        for m in d["messages"]:
            if name not in _umq_scope(m, all_names):
                continue
            if (m.get("checked") or {}).get(name):
                continue
            out.append(m)
    return out

def umq_check(ids, name, all_names=None):
    """Mark entries seen. name='*' marks every in-scope agent (frontend delivery pass)."""
    ids = [i for i in (ids or []) if isinstance(i, str)]
    if not ids:
        return 0
    with _umq_lock:
        d = _umq_read()
        n = 0
        for m in d["messages"]:
            if m.get("id") not in ids:
                continue
            if name == "*":
                if all_names:
                    targets = _umq_scope(m, all_names)
                else:
                    targets = m.get("mentions") or list((m.get("checked") or {}).keys())
            else:
                targets = [name]
            for t in targets:
                if not (m.get("checked") or {}).get(t):
                    m.setdefault("checked", {})[t] = True
                    n += 1
        if n:
            _umq_write(d)
    return n

def umq_view(all_names):
    """Latest entries + derived `processed` (every in-scope agent has seen it)."""
    with _umq_lock:
        d = _umq_read()
        out = []
        for m in d["messages"][-50:]:
            scope = _umq_scope(m, all_names)
            chk = m.get("checked") or {}
            mm = dict(m)
            mm["processed"] = (not scope) or all(chk.get(n2) for n2 in scope)
            out.append(mm)
    return out

# ---------------------------------------------------------------- chat history + run state (2026-11-15)
# Per-mode history persisted server-side so a browser refresh does not wipe the conversation;
# run_state.json carries a heartbeat while a run is busy so a reload can offer resume.
def _load_history(mode):
    path = CHAT_HISTORY_FILES.get(mode)
    if not path:
        return []
    try:
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        h = d.get("history") if isinstance(d, dict) else d
        if isinstance(h, list):
            return [x for x in h if isinstance(x, dict) and x.get("speaker")]
    except Exception:
        pass
    return []

def _save_history(mode, history):
    path = CHAT_HISTORY_FILES.get(mode)
    if not path:
        return False
    try:
        clean = []
        for x in (history or [])[-HIST_MAX:]:
            if isinstance(x, dict) and x.get("speaker"):
                clean.append({"speaker": str(x["speaker"])[:100],
                              "content": str(x.get("content", ""))[:20000]})
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"history": clean}, fh, ensure_ascii=False)
        os.replace(tmp, path)
        return True
    except Exception:
        return False

def _load_run_state():
    try:
        with open(RUN_STATE_FILE, encoding="utf-8") as fh:
            d = json.load(fh)
        if isinstance(d, dict):
            return d
    except Exception:
        pass
    return {"busy": False}

def _save_run_state(d):
    try:
        tmp = RUN_STATE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(d if isinstance(d, dict) else {"busy": bool(d)}, fh)
        os.replace(tmp, RUN_STATE_FILE)
    except Exception:
        pass

def load_memory():
    """Return (file_text, state) for the global memory.md. Creates it if missing."""
    with _lock:
        try:
            text = open(MEMORY_FILE, encoding="utf-8").read().strip()
        except Exception:
            text = ""
    st = {"inter_agent_replies": 0, "last_reset_by": "", "infinite_budget": True}
    m = _STATE_RE.search(text)
    if m:
        try:
            d = json.loads(m.group(1))
            st["inter_agent_replies"] = max(0, int(d.get("inter_agent_replies", 0)))
            st["last_reset_by"] = str(d.get("last_reset_by") or "")[:60]
            if "infinite_budget" in d:   # key absent (old files) = ON: unlimited by default
                st["infinite_budget"] = bool(d["infinite_budget"])
        except Exception:
            pass
    if not text:
        _write_memory(_MEMORY_TEMPLATE, st)
        return _MEMORY_TEMPLATE, st
    return text, st


def _write_memory(text, st):
    """Persist counter state: rewrite the state line + Counter section, keep the rest."""
    inf = bool(st.get("infinite_budget", True))
    state_line = "<!-- state: %s -->" % json.dumps(
        {"inter_agent_replies": st["inter_agent_replies"],
         "last_reset_by": st["last_reset_by"],
         "infinite_budget": inf}, ensure_ascii=False)
    if _STATE_RE.search(text):
        text = _STATE_RE.sub(lambda _: state_line, text, count=1)
    else:
        text = state_line + "\n" + text
    cap = "∞" if inf else XTALK_LIMIT
    block = ("## Counter\n"
             f"- inter_agent_replies_this_prompt: {st['inter_agent_replies']} / {cap}\n"
             f"- last_reset_by: {st['last_reset_by'] or '—'}\n")
    if "## Counter" in text:
        # `\n?` tolerates a final counter line without trailing newline (load strips it).
        text = re.sub(r"## Counter\n(?:- .+\n?)*", block, text, count=1)
    else:
        text = text.rstrip() + "\n\n" + block
    with _lock:
        open(MEMORY_FILE, "w", encoding="utf-8").write(text)


def _read_state_unlocked():
    """Parse the state line from memory.md. Caller must hold _lock."""
    text = ""
    try:
        text = open(MEMORY_FILE, encoding="utf-8").read().strip()
    except Exception:
        pass
    st = {"inter_agent_replies": 0, "last_reset_by": "", "infinite_budget": True}
    m = _STATE_RE.search(text)
    if m:
        try:
            d = json.loads(m.group(1))
            st["inter_agent_replies"] = max(0, int(d.get("inter_agent_replies", 0)))
            st["last_reset_by"] = str(d.get("last_reset_by") or "")[:60]
            if "infinite_budget" in d:   # key absent (old files) = ON: unlimited by default
                st["infinite_budget"] = bool(d["infinite_budget"])
        except Exception:
            pass
    return text, st


def _reset_counter():
    """Atomically zero the shared counter (new human prompt). Returns fresh state.
    Idempotent, so all agents of a PARALLEL prompt phase can fire it at once.
    Preserves infinite_budget - a reset must not silently re-cap the budget."""
    with _lock:
        text, st = _read_state_unlocked()
        st["inter_agent_replies"] = 0
        st["last_reset_by"] = ""
        _write_memory(text, st)
        return st


def _bump_counter(agent_name, kind, text):
    """Atomic read-modify-write of the shared counter after a group reply.
    The whole RMW happens inside ONE lock hold, so simultaneous replies from
    parallel agent streams can never lose an increment (old code read N in two
    threads and both wrote N+1). Returns the new state."""
    with _lock:
        text_file, st = _read_state_unlocked()
        if RESET_PHRASE in text.lower():
            st["inter_agent_replies"] = 0
            st["last_reset_by"] = agent_name[:60]
        elif kind == "cross-talk":
            st["inter_agent_replies"] += 1
        _write_memory(text_file, st)
        return st


def _shared_memory_block(st):
    """Compact view of the shared counter from memory.md, injected into every
    agent's prompt so all agents see the same state."""
    inf = bool(st.get("infinite_budget", True))
    lines = ["SHARED GROUP MEMORY (global file memory.md - visible to ALL agents):",
             f"- inter_agent_replies_this_prompt: {st['inter_agent_replies']} / {'∞ (unlimited)' if inf else XTALK_LIMIT}"]
    if st.get("last_reset_by"):
        lines.append(f"- last_reset_by: {st['last_reset_by']}")
    if inf:
        lines.append('Rule: agent-to-agent replies are UNLIMITED this prompt (infinite budget ON). '
                     'End the discussion when it is settled - reply [CONCLUDED] once the task is done, '
                     'or [SILENT] when you have nothing new to add.')
    else:
        lines.append('Rule: at most %d agent-to-agent replies per human prompt; a member saying "%s" resets the counter.'
                     % (XTALK_LIMIT, RESET_PHRASE))
    idx = _index_block()
    if idx:
        lines.append("MEMORY MAP (pointer index - open a module only when you need its detail):")
        lines.append(idx)
    lp = _live_plan_block()
    if lp:   # STEP 4: live goal + project state, so agents don't need file access for the plan
        lines.append(lp)
    return "\n".join(lines)


def _index_block():
    """Compact pointer map injected into group prompts instead of full notes."""
    try:
        t = open(os.path.join(MEMORY_DIR, "INDEX.md"), encoding="utf-8").read().strip()
        return t[:1600]
    except Exception:
        return ""


def _live_plan_block():
    """Live plan injected into group prompts (file-access STEP 4, approved 2026-11-13):
    the top section of TODO.md (the live goal) + MEMORY.md's GOAL line, so every agent sees
    what the project is currently doing even when its host's sandbox mirror lags. Both reads
    are capped for prompt budget; any failure -> "" (a missing plan must never break chat)."""
    out = []
    try:
        t = open(os.path.join(HERE, "TODO.md"), encoding="utf-8").read()
        m = re.search(r"^## .+?(?=^## |\Z)", t, re.M | re.S)
        if m:
            out.append("LIVE PLAN (top of TODO.md - what this project is working on right now):"
                       "\n" + m.group(0).strip()[:1200])
    except Exception:
        pass
    try:
        t = open(os.path.join(HERE, "MEMORY.md"), encoding="utf-8").read()
        m = re.search(r"^## GOAL.*?(?=^## |\Z)", t, re.M | re.S)
        if m:
            out.append("PROJECT STATE (MEMORY.md goal line):"
                       "\n" + m.group(0).strip()[:600])
    except Exception:
        pass
    return "\n\n".join(out)


def _ack_nudge(agent, messages, kind="cross-talk", all_agents=None):
    """Deterministic ack nudge (not model judgment).
    prompt:     fires when the HUMAN named this agent in their latest message.
    cross-talk: fires when another agent named this agent since the last human message,
                or sent them a [DM @Name] private message. DMs to OTHER agents are
                redacted before the name scan, so a foreign DM's content can't nudge you."""
    name = re.escape(agent["name"])
    msgs = messages or []
    users = [i for i, m in enumerate(msgs) if (m.get("speaker") or "").strip().lower() == "you"]
    if kind == "prompt":
        if users and re.search(rf"\b{name}\b", msgs[users[-1]].get("content") or "", re.I):
            return "NOTE: The human addressed you by name in their latest message - respond."
        return ""
    start = users[-1] + 1 if users else 0
    for m in reversed(msgs[start:]):
        who = (m.get("speaker") or "").strip()
        if not who or who.lower() == agent["name"].lower():
            continue
        c = m.get("content") or ""
        segs = parse_dm_segments(c)
        dms = [t for k, t, b in segs if k == "dm"]
        if dms and agent["name"].lower() in dms:
            return ("NOTE: %s sent you a PRIVATE message - respond briefly to it; its content "
                    "is visible only to the two of you." % who)
        if dms and all_agents is not None:
            known = {a["name"].lower() for a in all_agents}
            if all(t in known for t in dms):
                c = render_dm_view(segs, agent["name"], who)   # redact foreign DMs before the name scan
        if re.search(rf"\b{name}\b", c, re.I):
            return ("NOTE: %s addressed you by name in their latest message - respond briefly "
                    "unless you have nothing to add ([SILENT])." % who)
    return ""


def _safe_memory_file(rel):
    """Resolve a relative path inside MEMORY_DIR. Returns abs path or None (no traversal)."""
    rel = (rel or "").replace("\\", "/").lstrip("/")
    if not rel:
        return None
    base = os.path.realpath(MEMORY_DIR)
    full = os.path.realpath(os.path.join(base, rel))
    if full != base and not full.startswith(base + os.sep):
        return None
    return full if os.path.isfile(full) else None


def _safe_workspace_file(rel):
    """Resolve a relative path inside HERE or the Studio agent sandbox (SANDBOX_DIR). Returns abs
    path or None (no traversal). Used by /api/file and /api/file/raw so agents' replies can link to
    files they created - those land in the sandbox, not HERE (2026-11-11)."""
    rel = (rel or "").replace("\\", "/").lstrip("/")
    if not rel or "\0" in rel:
        return None
    for base in (os.path.realpath(HERE), os.path.realpath(SANDBOX_DIR)):
        full = os.path.realpath(os.path.join(base, rel))
        if full != base and not full.startswith(base + os.sep):
            continue
        if os.path.exists(full):  # files AND folders (folder refs get a listing peek)
            return full
    return None


# ---------------------------------------------------------------- per-message memory cycle (2026-11-14)

def _aux_chat(agent, system, user, max_tokens):
    """One NON-streaming auxiliary LLM round on the agent's own Studio host
    (low reasoning, tiny budget, short timeout). Returns content; "" on ANY failure."""
    try:
        body = {"model": agent["model_id"],
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user}],
                "max_tokens": max_tokens,
                "temperature": 0.0,
                "stream": False,
                "enable_thinking": True,
                "reasoning_effort": FIRST_REPLY_REASONING}
        req = urllib.request.Request(studio_base(agent) + "/v1/chat/completions",
                                     data=json.dumps(body).encode(),
                                     headers=studio_headers(agent))
        with urllib.request.urlopen(req, timeout=30) as r:
            res = json.load(r)
        return ((res.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    except Exception:
        return ""


def _mem_lookup_round(agent, messages):
    """READMEM: one cheap aux round BEFORE the main reply. A router call sees the incoming
    message + memory map + current hot notes and emits ONE search query (or NONE); the fetch
    reuses _rag_search. Current hot notes are always included in the output so STOREMEM's
    notes feed back into later rounds (closing the loop). Returns a context block or ""; any
    failure degrades to "" - ReadMem must never break or hang the main turn."""
    try:
        latest = ""
        for m in reversed(messages or []):
            c = (m.get("content") or "").strip()
            if c:
                latest = c[:600]
                break
        if not latest:
            return ""
        idx = _index_block()[:800]
        notes = _hot_notes_block()[:600]
        parts = []
        if notes:
            parts.append("HOT NOTES (shared memory.md, newest last):\n" + notes)
        sysp = ("You are the memory-lookup router for agent %s. Decide whether the incoming "
                "message needs anything MORE from project memory than the hot notes shown. "
                "Reply with EXACTLY ONE line: a short search query of at most 8 words, or "
                'NONE if the hot notes and map already cover it.' % agent.get("name", "?"))
        user = "MEMORY MAP:\n" + (idx or "(empty)")
        if notes:
            user += "\n\nHOT NOTES:\n" + notes
        user += "\n\nINCOMING MESSAGE:\n" + latest
        out = _aux_chat(agent, sysp, user, MEM_LOOKUP_MAX_TOKENS)
        q = " ".join(out.split())[:120]
        if q and not q.upper().startswith("NONE"):
            ctx = _rag_search(agent, q)   # ReadMem reuses the RAG fetch path
            if ctx:
                parts.append(ctx.replace(
                    "RETRIEVED CONTEXT (from your RAG knowledge base; use when relevant):",
                    'LOOKED-UP MEMORY (query: "%s"): ' % q[:80]))
        return "\n\n".join(parts)
    except Exception:
        return ""


def _mem_store_round(agent, messages, reply):
    """STOREMEM: one cheap aux round AFTER the main reply. Distills at most ONE durable note
    (<= HOT_NOTE_CHARS chars) about what just happened; "" when nothing is worth storing or
    on any failure."""
    try:
        tail = []
        for m in (messages or [])[-6:]:
            c = (m.get("content") or "").strip()
            if c:
                tail.append("%s: %s" % ((m.get("speaker") or "?")[:20], c[:300]))
        sysp = ("You are the memory keeper for agent %s. From this exchange, decide whether "
                "there is ONE fact worth remembering for future rounds (a decision made, a "
                "task completed, an open question, a correction). Reply with EXACTLY ONE line: "
                "the note in at most 140 characters, no preamble - or NONE if nothing is "
                "durable enough to store." % agent.get("name", "?"))
        user = ("\n".join(tail) if tail else "(no earlier messages)") + \
               "\n\nYOUR REPLY:\n" + (reply or "")[:600]
        out = _aux_chat(agent, sysp, user, MEM_STORE_MAX_TOKENS)
        note = " ".join(out.split())
        if not note or note.upper().startswith("NONE"):
            return ""
        return note[:HOT_NOTE_CHARS]
    except Exception:
        return ""


def _hot_notes_block():
    """The '## Hot Notes' section of memory.md (newest last), or "" if absent."""
    with _lock:
        text, _st = _read_state_unlocked()
    m = re.search(r"## Hot Notes\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1).strip() if m else ""


def _append_hot_note(note):
    """Atomically append one hot note to memory.md: dedupe (case-insensitive), keep only the
    newest HOT_NOTE_MAX, rewrite via _write_memory so the state line + Counter stay intact.
    Returns True if stored, False on duplicate/empty. Never raises."""
    body = " ".join((note or "").split()).lstrip("-").strip()[:HOT_NOTE_CHARS]
    if not body:
        return False
    with _lock:
        text, st = _read_state_unlocked()
        m = re.search(r"## Hot Notes\n(.*?)(?=^## |\Z)", text, re.M | re.S)
        existing = [l.strip() for l in (m.group(1).splitlines() if m else [])
                    if l.strip().startswith("- ")]
        if any(e.lstrip("-").strip().lower() == body.lower() for e in existing):
            return False   # duplicate - skip
        notes = existing + ["- " + body]
        if len(notes) > HOT_NOTE_MAX:
            notes = notes[-HOT_NOTE_MAX:]   # keep the newest
        block = "## Hot Notes\n" + "\n".join(notes) + "\n"
        if m:
            text = text[:m.start()] + block + text[m.end():]
        else:
            # First-time insert: place BEFORE '## Counter' (not at the file end), so entries
            # appended later by agents can't land inside/after the notes section.
            cm = re.search(r"^## Counter\n", text, re.M)
            if cm:
                text = text[:cm.start()] + block + "\n" + text[cm.start():]
            else:
                text = text.rstrip() + "\n\n" + block
        _write_memory(text, st)
        return True


def _group_round_summary(agent, messages, all_agents):
    """CROSS-TALK ORIENTATION (2026-11-14): one line per OTHER agent - what they last said
    since the human's latest message (private-to-you DMs flagged, foreign content excluded) -
    so each cross-talk round starts knowing where everyone stands. Group mode only."""
    msgs = messages or []
    users = [i for i, m in enumerate(msgs) if (m.get("speaker") or "").strip().lower() == "you"]
    start = users[-1] + 1 if users else 0
    lines = ["GROUP ROSTER - where each agent stands RIGHT NOW (summary before your round):"]
    for a in all_agents:
        if a["id"] == agent.get("id"):
            continue
        name = a.get("name", "?")
        said = ""
        for m in reversed(msgs[start:]):
            who = (m.get("speaker") or "").strip()
            if not who or who.lower() != name.lower():
                continue
            c = (m.get("content") or "").strip()
            if not c:
                continue
            segs = parse_dm_segments(c)
            pub = " ".join(b for k, _t, b in segs if k == "public").strip()
            said = (pub or "(private message to you)")[:150]
            break
        blurb = (a.get("blurb") or "")[:60]
        lines.append("- %s (%s) just said: %s" % (name, blurb,
                     ('"%s"' % said) if said else "no words yet this round"))
    return "\n".join(lines)


def stream_chat(wfile, agent, messages, mode, kind="prompt", session=None):
    # Activity timeline: one JSONL event per phase into activity/<session>.jsonl.
    session = _safe_session(session)
    who = agent.get("name", "?")[:60]
    t0 = time.time()
    _act_log(session, {"agent": who, "event": "start", "kind": kind, "mode": mode})
    all_agents = load_agents()["agents"]
    _, mem_st = load_memory() if mode == "group" else (None, None)
    if mode == "group" and kind == "prompt":
        # A new human prompt starts a fresh agent-to-agent budget. Atomic:
        # every agent of the parallel prompt phase fires this at once (idempotent zero).
        if mem_st["inter_agent_replies"] or mem_st.get("last_reset_by"):
            mem_st = _reset_counter()
    mem_block = _shared_memory_block(mem_st) if mode == "group" else ""
    if mode == "group":
        nudge = _ack_nudge(agent, messages, kind, all_agents)
        if nudge:
            mem_block = (mem_block + "\n" if mem_block else "") + nudge
        if kind == "cross-talk":
            # CROSS-TALK ORIENTATION: one line per other agent on where they stand, so each
            # round starts with the group's current state instead of a blank slate.
            roster = _group_round_summary(agent, messages, all_agents)
            if roster:
                mem_block = (mem_block + "\n" if mem_block else "") + roster
    # USER MESSAGE QUEUE (2026-11-15): human messages sent while the group was working.
    # Injected into THIS agent's prompt now; marked seen for it once the request reaches Studio.
    umq_ids = []
    if mode == "group":
        pend = umq_pending_for(who, [a.get("name", "") for a in all_agents])
        if pend:
            ul = ["USER MESSAGE QUEUE (user_messages.json - human messages that arrived while the group was working; they ARE part of this turn):"]
            for m in pend:
                tag = "PRIVATE, addressed only to you" if m.get("mentions") else "broadcast to all agents"
                ul.append("- [%s] %s (%s) You: %s" % (m["id"], m["ts"], tag, m["text"][:4000]))
            ul.append("Rule: act on them in your reply. Private entries are for you alone - do not quote them publicly unless asked.")
            mem_block = (mem_block + "\n\n" if mem_block else "") + "\n".join(ul)
            umq_ids = [m["id"] for m in pend]
        gb = _agent_goals_block(who)   # goal-drift fix: every group turn sees this agent's open goals
        if gb:
            mem_block = (mem_block + "\n\n" if mem_block else "") + gb
    # Blocked cross-talk rounds skip ReadMem entirely (checked BEFORE any aux round).
    if kind == "cross-talk" and not mem_st.get("infinite_budget", True) \
            and mem_st["inter_agent_replies"] >= XTALK_LIMIT:
        wfile.write(b"data: " + json.dumps(
            {"blocked": f"agent-to-agent reply limit reached ({mem_st['inter_agent_replies']}/{XTALK_LIMIT})"}
        ).encode() + b"\n\n")
        _act_log(session, {"agent": who, "event": "blocked",
                           "detail": f"agent-to-agent limit {mem_st['inter_agent_replies']}/{XTALK_LIMIT}"})
        wfile.write(b"data: [DONE]\n\n")
        wfile.flush()
        return
    # READMEM (2026-11-14): cheap aux round fetches memory context for THIS message.
    mem_cycle = bool(agent.get("mem_cycle", MEM_CYCLE_DEFAULT))
    lookup_ctx = ""
    if mem_cycle:
        t_rm = time.time()
        lookup_ctx = _mem_lookup_round(agent, messages)
        _act_log(session, {"agent": who, "event": "readmem",
                           "dur": round(time.time() - t_rm, 2), "chars": len(lookup_ctx)})
    # FAST FIRST REPLY: the first reply to a human uses a low context window (last N
    # messages) and low reasoning when the agent's setting is left at "default".
    fast_first = kind == "prompt" and bool(agent.get("fast_first_reply", FAST_FIRST_DEFAULT))
    msgs_llm = (messages[-FIRST_REPLY_MAX_MSGS:]
                if fast_first and len(messages or []) > FIRST_REPLY_MAX_MSGS else (messages or []))
    rag_context = rag_prefetch(agent, msgs_llm)
    body = {"model": agent["model_id"],
            "messages": to_openai_messages(agent, msgs_llm, mode, all_agents,
                                           rag_context, mem_block, kind, lookup_ctx),
            "stream": True,
            "temperature": float(agent.get("temperature", 0.7))}
    mt = int(agent.get("max_tokens") or 0)
    if mt > 0:
        body["max_tokens"] = mt
    eff = agent.get("reasoning", "default")
    if fast_first and eff == "default":
        eff = FIRST_REPLY_REASONING
    if eff == "off":
        body["enable_thinking"] = False
    elif eff != "default":
        body["enable_thinking"] = True
        body["reasoning_effort"] = eff
    tools = agent.get("tools") or []
    if tools:
        # enable_tools=true is REQUIRED: without it Studio never injects the tool
        # system-prompt block into the chat template, so the model has no idea it
        # can call tools (diagnosed 2026-11-10: web_search "false" claim + hung probe).
        body["enable_tools"] = True
        # permission_mode="off" is REQUIRED alongside enable_tools for local tool
        # execution without the X-Unsloth-Events confirm flow; without it Studio
        # rejects the request with HTTP 400 (param=confirm_tool_calls, found 2026-11-10).
        body["permission_mode"] = "off"
        body["enabled_tools"] = tools
        body["run_tools_locally"] = bool(agent.get("run_tools_locally", True))
        mtc = int(agent.get("max_tool_calls") or 0)
        if mtc > 0:
            body["max_tool_calls_per_message"] = mtc
    req = urllib.request.Request(studio_base(agent) + "/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers=studio_headers(agent))
    try:
        resp = urllib.request.urlopen(req, timeout=600)
        if umq_ids:  # request reached Studio => queued messages are now in this context
            umq_check(umq_ids, who)
    except Exception as e:
        _act_log(session, {"agent": who, "event": "error", "error": str(e)[:300]})
        wfile.write(b"data: " + json.dumps({"error": str(e)}).encode() + b"\n\n")
        wfile.write(b"data: [DONE]\n\n")
        return
    buf = b""
    full = ""
    seen_tools = set()
    try:
        for raw in resp:
            buf += raw
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                line = line.strip()
                if not line.startswith(b"data:"):
                    continue
                payload = line[5:].strip()
                if payload == b"[DONE]":
                    break
                try:
                    obj = json.loads(payload)
                except Exception:
                    continue
                delta = ""
                ch = obj.get("choices") or [{}]
                d = (ch[0] or {}).get("delta") or {}
                if d.get("content"):
                    delta += d["content"]
                    full += delta
                think = d.get("reasoning_content") or d.get("reasoning") or ""
                tool = d.get("tool_calls") or d.get("tools") or obj.get("tool_call")
                if tool:
                    for nm in _tool_names(tool):
                        if nm not in seen_tools:
                            seen_tools.add(nm)
                            _act_log(session, {"agent": who, "event": "tool", "tool": nm})
                if delta or think or tool:
                    wfile.write(b"data: " + json.dumps(
                        {"content": delta, "thinking": think, "tool": tool},
                        ensure_ascii=False).encode() + b"\n\n")
                    wfile.flush()
    except OSError:
        # Browser aborted the stream (■ Stop / tab closed): stop forwarding AND kill the
        # upstream request so Studio stops generating instead of burning GPU on a dead stream.
        _act_log(session, {"agent": who, "event": "aborted"})
        return
    finally:
        resp.close()
    # STOREMEM (2026-11-14): cheap aux round distills at most one hot note from the reply.
    if mem_cycle and full.strip():
        _txt, is_silent, _ = _effective_reply(full)
        if not is_silent:
            t_sm = time.time()
            note = _mem_store_round(agent, messages, full)
            stored = bool(note) and _append_hot_note(note)
            _act_log(session, {"agent": who, "event": "storemem",
                               "dur": round(time.time() - t_sm, 2),
                               "stored": bool(stored), "note": note[:HOT_NOTE_CHARS]})
    silent, concluded = _finish_chat(wfile, agent, mode, kind, full)
    _act_log(session, {"agent": who, "event": "end", "dur": round(time.time() - t0, 2),
                       "chars": len(full), "silent": bool(silent), "concluded": bool(concluded)})


def _effective_reply(full):
    """Parse leading control markers. Returns (text, is_silent, concluded)."""
    t = (full or "").strip()
    low = t.lower()
    if low.startswith("[silent]"):
        rest = t[len("[silent]"):].lstrip(" :-").strip()
        return rest, not rest, False
    if low.startswith("[concluded]"):
        rest = t[len("[concluded]"):].lstrip(" :-").strip()
        return (rest or "(concluded)"), False, True
    return t, False, False


def _finish_chat(wfile, agent, mode, kind, full):
    """Update the shared counter in memory.md after a group reply, then close.

    Emits ONE authoritative meta frame per group reply. The `silent` flag is the
    single source of truth for [SILENT] detection (Python _effective_reply), so the
    frontend no longer needs its own regex to agree - it just trusts this flag."""
    is_silent = concluded = False
    if mode == "group" and full.strip():
        text, is_silent, concluded = _effective_reply(full)
        if kind != "cross-talk":
            concluded = False   # a conclusion only means something mid-debate
        st_now = None
        if not is_silent:
            # Atomic RMW - parallel streams can finish simultaneously (see _bump_counter).
            st_now = _bump_counter(agent.get("name", "?")[:60], kind, text)
        meta = {"silent": is_silent}
        if concluded:
            meta["concluded"] = True
        if st_now is not None:
            meta["inter_agent_replies"] = st_now["inter_agent_replies"]
            meta["limit"] = None if st_now.get("infinite_budget", True) else XTALK_LIMIT  # null = ∞
        wfile.write(b"data: " + json.dumps({"meta": meta}, ensure_ascii=False).encode() + b"\n\n")
    wfile.write(b"data: [DONE]\n\n")
    wfile.flush()
    return is_silent, concluded


# ---- Group run engine (2026-11-15): backend-owned group orchestration ----
# The cross-talk / auto-nudge loop used to live in the browser (index.html send()); a hard
# refresh killed every in-flight stream and lost the whole run. Now a daemon thread owns
# each group run: state persists in group_run.json, every SSE frame is journaled into
# runs/<run_id>.journal, and ANY client (including one that just reloaded) replays from
# seq 0 via /api/run-events and keeps watching live. Queued human messages ride the UMQ
# (user_messages.json) and are injected by stream_chat itself - refresh-proof.

GROUP_RUN_FILE = os.path.join(HERE, "group_run.json")
RUNS_DIR = os.path.join(HERE, "runs")
RUN_MAX_EVENTS = 4000      # per-run journal cap (a full run is normally a few hundred)
RUN_KEEP = 5               # keep the N newest journals on disk
NUDGE_MAX_RUN = 3          # auto-continue passes (mirrors the old frontend cap)
XTALK_GUARD_RUN = 8        # max cross-talk rounds per pass
MAX_CALLS_RUN = 16         # max agent calls per pass

_group_run_lock = threading.Lock()
_history_lock = threading.Lock()
_journal_lock = threading.Lock()
_active_run_id = None      # at most one live group run
_run_stops = {}            # run_id -> threading.Event (■ Stop)
_run_seq = {}              # run_id -> next seq


class _RunStopped(OSError):
    """Raised by the run sink when ■ Stop is requested. stream_chat's existing
    `except OSError` branch catches it, so a stopped turn tears down cleanly."""


def _load_group_run():
    try:
        with open(GROUP_RUN_FILE, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _save_group_run(run):
    tmp = GROUP_RUN_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(run, f, ensure_ascii=False)
    os.replace(tmp, GROUP_RUN_FILE)


def _append_history(mode, entries):
    """Append messages to the mode history (backend-owned group runs). Atomic RMW."""
    if not entries or mode not in CHAT_HISTORY_FILES:
        return
    with _history_lock:
        h = _load_history(mode)
        h.extend(entries)
        _save_history(mode, h)


def _run_event(run_id, obj):
    """Journal one seq-numbered event into the run's JSONL log (the replay source)."""
    with _journal_lock:
        nxt = _run_seq.get(run_id)
        if nxt is None:  # first event for this run in this process: resume from disk
            nxt = 1
            try:
                with open(os.path.join(RUNS_DIR, run_id + ".journal"), encoding="utf-8") as f:
                    last = None
                    for ln in f:
                        last = ln
                if last:
                    nxt = int(json.loads(last).get("seq", 0)) + 1
            except Exception:
                pass
        if nxt > RUN_MAX_EVENTS:
            return
        _run_seq[run_id] = nxt + 1
        line = json.dumps({"seq": nxt, **obj}, ensure_ascii=False) + "\n"
        try:
            os.makedirs(RUNS_DIR, exist_ok=True)
            with open(os.path.join(RUNS_DIR, run_id + ".journal"), "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass


class _FrameSink:
    """File-like stand-in for wfile: journals the SSE frames of one backend turn.

    stream_chat only needs .write/.flush, so the ENTIRE turn pipeline (counter bump,
    UMQ injection, ReadMem/StoreMem aux rounds, activity log) runs unchanged."""

    def __init__(self, on_frame=None, stop_event=None):
        self.on_frame = on_frame
        self.stop_event = stop_event
        self.buf = b""
        self.content = ""
        self.meta = {}
        self.error = None
        self.blocked = None

    def write(self, data):
        if self.stop_event is not None and self.stop_event.is_set():
            raise _RunStopped("run stopped")
        self.buf += data
        while b"\n\n" in self.buf:
            chunk, self.buf = self.buf.split(b"\n\n", 1)
            line = chunk.strip()
            if not line.startswith(b"data:"):
                continue
            payload = line[5:].strip()
            if payload == b"[DONE]":
                continue
            try:
                obj = json.loads(payload)
            except Exception:
                continue
            if obj.get("content"):
                self.content += obj["content"]
            if "meta" in obj:
                self.meta = obj["meta"]
            if obj.get("error"):
                self.error = str(obj["error"])[:300]
            if obj.get("blocked"):
                self.blocked = str(obj["blocked"])[:300]
            if self.on_frame:
                try:
                    self.on_frame(obj)
                except Exception:
                    pass
        return len(data)

    def flush(self):
        pass


def run_turn_captured(agent, messages, mode, kind, session, on_frame=None, stop_event=None):
    """Run one agent turn exactly like /api/chat but capture the SSE frames instead of
    streaming them to a browser. Returns the sink (.content/.meta/.error/.blocked)."""
    sink = _FrameSink(on_frame, stop_event)
    stream_chat(sink, agent, messages, mode, kind, session)
    return sink


def _parallel_turns(run_id, names, kind, hist, stop_event):
    """Fire one turn per agent in parallel (same semantics as the old frontend Promise.all).
    Returns result dicts in `names` order: {name, full, silent, concluded, error, blocked}."""
    agents_by_name = {a.get("name", "?"): a for a in load_agents()["agents"]}
    out = [None] * len(names)

    def work(i, nm):
        ag = agents_by_name.get(nm)
        if not ag:
            return
        _run_event(run_id, {"agent": nm, "kind": kind, "turn": True})  # frontend opens a bubble here
        sink = run_turn_captured(ag, hist, "group", kind, run_id,
                                 on_frame=lambda o: _run_event(
                                     run_id, {"agent": nm, "kind": kind, "frame": o}),
                                 stop_event=stop_event)
        if sink.content.strip():
            _, is_silent, concluded = _effective_reply(sink.content)
        else:
            is_silent, concluded = False, False
        out[i] = {"name": nm, "full": sink.content, "silent": bool(is_silent),
                  "concluded": bool(concluded), "error": sink.error, "blocked": sink.blocked}

    threads = [threading.Thread(target=work, args=(i, nm), daemon=True)
               for i, nm in enumerate(names)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    for r in out:  # terminal event per turn - the frontend finalizes each bubble on this
        if r:
            _run_event(run_id, {"agent": r["name"], "kind": kind, "done": True})
    return out


def _group_run_worker(run_id):
    """Backend port of the frontend group loop: parallel prompt phase -> cross-talk rounds
    (settled / budget / guard caps) -> auto-nudge passes -> verdict. Every frame is journaled;
    state survives tab refreshes, and a portal restart marks the run interrupted."""
    global _active_run_id
    run = _load_group_run()
    stop_event = _run_stops.get(run_id) or threading.Event()
    agents_by_name = {a.get("name", "?"): a for a in load_agents()["agents"]}
    cast = [n for n in (run.get("cast") or []) if n in agents_by_name]
    settled, no_output = set(), []
    last_concluded = pass_any = truncated = False
    nudges = 0
    verdict = None

    def expand_mentions(text):
        nonlocal cast
        for nm in agents_by_name:
            if nm not in cast and re.search(r"@" + re.escape(nm), text or "", re.I):
                cast.append(nm)
                run["cast"] = list(cast)
                _save_group_run(run)

    try:
        while True:
            if stop_event.is_set():
                verdict = {"note": "\u25a0 Stopped by user \u2014 round closed as concluded.", "cls": "ok"}
                break
            if nudges > 0:
                nt = ("\u21bb AUTO-CONTINUE %d/%d: the previous pass ended without [CONCLUDED]. Keep going: "
                      "finish in-flight work, then either reply [CONCLUDED] when the task is done or go "
                      "[SILENT] if there is nothing left to do.") % (nudges, NUDGE_MAX_RUN)
                _append_history("group", [{"speaker": "You", "content": nt}])
                _run_event(run_id, {"run": "nudge", "text": nt})
            hist = _load_history("group")
            run["phase"] = "prompt"
            _save_group_run(run)
            _run_event(run_id, {"run": "phase", "phase": "prompt"})
            results = [r for r in _parallel_turns(run_id, cast, "prompt", hist, stop_event) if r]
            entries = []
            for r in results:
                if r["blocked"] or r["error"]:
                    continue
                if r["full"].strip() and not r["silent"]:
                    entries.append({"speaker": r["name"], "content": r["full"]})
                    pass_any = True
                    if re.search(r"stopped before completing its tool calls", r["full"], re.I):
                        truncated = True
                else:
                    no_output.append(r["name"])
            _append_history("group", entries)
            for r in results:  # @-mention expansion (same rule as the old frontend loop)
                expand_mentions(r["full"])
            guard = calls = 0
            while (not stop_event.is_set() and guard < XTALK_GUARD_RUN and calls < MAX_CALLS_RUN):
                _, st = load_memory()
                if not st.get("infinite_budget", True) and st["inter_agent_replies"] >= XTALK_LIMIT:
                    break
                active = [nm for nm in cast if nm not in settled]
                if not active:
                    break
                calls += len(active)
                hist = _load_history("group")
                run["phase"] = "cross-talk"
                _save_group_run(run)
                _run_event(run_id, {"run": "phase", "phase": "cross-talk"})
                results = [r for r in _parallel_turns(run_id, active, "cross-talk", hist, stop_event) if r]
                any_new = False
                for r in results:
                    if r["blocked"]:
                        continue
                    if r["full"].strip() and not r["silent"]:
                        _append_history("group", [{"speaker": r["name"], "content": r["full"]}])
                        any_new = True
                        pass_any = True
                        if r["concluded"]:
                            last_concluded = True
                        expand_mentions(r["full"])
                    else:
                        settled.add(r["name"])
                        if not r["full"].strip():
                            no_output.append(r["name"])
                guard += 1
                if last_concluded or not any_new:
                    break
            run["settled"] = sorted(settled)
            _save_group_run(run)
            if last_concluded:
                verdict = {"note": "\u2713 Concluded \u2014 task complete.", "cls": "ok"}
                break
            if pass_any and nudges < NUDGE_MAX_RUN:  # task incomplete -> AUTO-NUDGE next pass
                nudges += 1
                run["nudges"] = nudges
                _save_group_run(run)
                continue
            _, st = load_memory()
            spent = ("\u26a0 Auto-continue limit reached (%d/%d) \u2014 " % (nudges, NUDGE_MAX_RUN)) \
                if nudges >= NUDGE_MAX_RUN else ""
            if not st.get("infinite_budget", True) and st["inter_agent_replies"] >= XTALK_LIMIT:
                verdict = {"note": spent + "\u23f8 Agent-to-agent budget exhausted (%d/%d) with NO conclusion \u2014 task not confirmed complete. Send a follow-up to continue." % (st["inter_agent_replies"], XTALK_LIMIT), "cls": "warn"}
            elif truncated:
                verdict = {"note": (spent or "") + "\u26a0 Round ended with NO conclusion and truncated tool calls \u2014 the task is incomplete.", "cls": "warn"}
            else:
                tail = (" \u2014 %s produced no output" % ", ".join(sorted(set(no_output)))) if no_output else ""
                verdict = {"note": (spent or "\u2014 ") + "Round ended with NO conclusion. Task state unconfirmed%s. Send a follow-up to continue." % tail, "cls": "dim"}
            break
    except Exception as e:
        verdict = {"note": "Run error: %s" % str(e)[:200], "cls": "warn"}
        run["error"] = str(e)[:300]
    finally:
        run["status"] = "stopped" if stop_event.is_set() else ("concluded" if last_concluded else "done")
        run["verdict"] = verdict
        run["ended"] = time.time()
        _save_group_run(run)
        _run_event(run_id, {"run": "end", "status": run["status"], "verdict": verdict})
        try:
            _sync_workspace_to_sandbox()
            _auto_commit()
        except Exception:
            pass
        _active_run_id = None


def start_group_run(text):
    """Create + launch a backend-owned group run. Returns (run, error)."""
    global _active_run_id
    with _group_run_lock:
        if _active_run_id:
            return None, "a group run is already in progress (%s)" % _active_run_id
        agents = load_agents()["agents"]
        names = [a.get("name", "") for a in agents]
        mentioned = [n for n in names if re.search(r"@" + re.escape(n), text or "", re.I)]
        rid = "g-%x-%s" % (int(time.time() * 1000), os.urandom(3).hex())
        hist = _load_history("group")
        run = {"id": rid, "status": "running", "prompt": text[:4000], "cast": (mentioned or names),
               "settled": [], "nudges": 0, "phase": "prompt",
               "started": time.time(), "ended": None, "verdict": None, "error": None,
               "hist_start": len(hist)}
        _save_group_run(run)
        _append_history("group", [{"speaker": "You", "content": text}])
        _run_stops[rid] = threading.Event()
        _active_run_id = rid
    _run_event(rid, {"run": "start", "prompt": text[:4000]})
    _save_run_state({"busy": True, "mode": "group", "phase": "prompt",
                     "ts": int(time.time() * 1000), "run_id": rid})
    threading.Thread(target=_group_run_worker, args=(rid,), daemon=True).start()
    return run, None


def _agent_goals_block(name):
    """One short nudge per agent: its own open goals from memory/goals/<slug>.md, so group
    turns push toward progress instead of re-verification (2026-11-15 goal-drift fix)."""
    try:
        with open(os.path.join(HERE, "memory", "goals", name.lower() + ".md"), encoding="utf-8") as f:
            txt = f.read(4000)
        items = []
        for ln in txt.splitlines():
            m = re.match(r"^\s*\d+[.)]\s+(.*)", ln) or re.match(r"^\s*[-*]\s*\[ \]\s*(.*)", ln)
            if not m:
                continue
            it = m.group(1).strip()
            if not it or "[x]" in ln.lower():
                continue
            items.append(it[:200])
            if len(items) >= 5:
                break
        if not items:
            return ""
        return ("YOUR OPEN GOALS (memory/goals/%s.md \u2014 make progress on these; verify evidence on disk before claiming any done):\n%s"
                % (name.lower(), "\n".join(items))[:900])
    except Exception:
        return ""


def _reap_stale_group_run():
    """Portal restarted mid-run: the worker thread is gone. Mark the run interrupted so the
    UI shows what happened; queued UMQ messages survive and ride the next run."""
    try:
        run = _load_group_run()
        if run.get("id") and run.get("status") == "running":
            run["status"] = "interrupted"
            run["verdict"] = {"note": "\u26a0 Portal restarted mid-run \u2014 this run was interrupted. Queued messages were kept; send a follow-up to continue.", "cls": "warn"}
            run["ended"] = time.time()
            _save_group_run(run)
            _run_event(run["id"], {"run": "end", "status": "interrupted", "verdict": run["verdict"]})
    except Exception:
        pass


def _prune_run_journals():
    try:
        os.makedirs(RUNS_DIR, exist_ok=True)
        files = sorted((f for f in os.listdir(RUNS_DIR) if f.endswith(".journal")), reverse=True)
        for f in files[RUN_KEEP:]:
            os.remove(os.path.join(RUNS_DIR, f))
    except Exception:
        pass


_reap_stale_group_run()


def _clear_stale_busy():
    """A dead process leaves run_state.json with busy:true. If no group run is live, that flag
    is a lie - clear it so a fresh tab never thinks the portal is mid-run."""
    try:
        st = _load_run_state() or {}
        run = _load_group_run()
        if st.get("busy") and not (run.get("id") and run.get("status") == "running"):
            st["busy"] = False
            _save_run_state(st)
    except Exception:
        pass


_clear_stale_busy()
_prune_run_journals()

# ---- Ops (2026-11-13): TODO pruning + local git repo management ----
TODO_FILE = os.path.join(HERE, "TODO.md")
DONE_FILE = os.path.join(HERE, "TODO_completed.md")
DONE_PART_DIR = os.path.join(HERE, "todo_done_parts")
DONE_MAX_LINES = 240   # completed file splits into numbered parts above this
DONE_PART_SIZE = 200   # lines moved per split (oldest first)
GIT_EXE = os.path.join(HERE, "mingit", "cmd", "git.exe")
PORTAL_START = time.time()   # process start - ground truth for the Ops panel uptime tile


def _ops_snapshot():
    """Ops panel host tiles (2026-11-15): disk usage of the workspace drive +
    portal uptime since this process started. Cross-checkable against
    Win32_LogicalDisk / Win32_Process CreationDate."""
    try:
        drive = os.environ.get("SystemDrive", "C:")
        du = shutil.disk_usage(drive)
        disk = {"drive": drive,
                "total_gb": round(du.total / 2 ** 30, 1),
                "free_gb": round(du.free / 2 ** 30, 1),
                "used_gb": round((du.total - du.free) / 2 ** 30, 1)}
    except Exception as e:
        disk = {"error": str(e)}
    up = int(time.time() - PORTAL_START)
    hh, rem = divmod(up, 3600); mm, ss = divmod(rem, 60)
    return {"ok": True, "pid": os.getpid(),
            "uptime_s": up, "uptime_hm": "%dh %02dm %02ds" % (hh, mm, ss),
            "started": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(PORTAL_START)),
            "disk": disk}


def _goals_snapshot():
    """Goal Velocity dashboard (2026-11-15, Designer; Researcher evidence-gated v2).
    Counts a goal DONE only when an acceptance/evidence marker is present. Delegates to
    goal_ledger.parse_agent_file (single source of truth) so the portal can NEVER diverge
    from the evidence-honest ledger: closure is evidence-gated, a literal '[x]' substring
    in a goal's DESCRIPTION no longer counts, and an em-dash '— recorded' note IS counted.
    Import is location-independent: memory/researcher/goal_ledger.py first (the strict,
    verified variant), then portal-root goal_ledger.py only as last resort (its EVIDENCE_PAT
    is loose - it matches '[x]' itself - so it must never be preferred). Response schema
    unchanged. blocked = not-done item mentioning 'blocked'. Per-agent counts + fleet %."""
    gdir = os.path.join(HERE, "memory", "goals")
    try:
        names = {(a.get("name") or "").lower() for a in load_agents().get("agents", [])}
    except Exception:
        names = set()
    parse = None
    import importlib.util as _ilu
    for _cand in (os.path.join(HERE, "memory", "researcher", "goal_ledger.py"),):
        try:
            _spec = _ilu.spec_from_file_location("_gl_strict", _cand)
            _mod = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_mod)
            parse = _mod.parse_agent_file
            break
        except Exception:
            continue
    if parse is None:
        try:
            import goal_ledger as _gl
            parse = _gl.parse_agent_file
        except Exception:
            return {"ok": False, "error": "goal_ledger module not found (memory/researcher or portal root)", "agents": []}
    agents = []
    try:
        for fn in sorted(os.listdir(gdir)):
            if not fn.endswith(".md") or fn[:-3] == "INDEX":
                continue
            if names and fn[:-3].lower() not in names:
                continue  # skip summary/dated rollup files (all-goals-*, *-agent-goals, etc.)
            goals = parse(os.path.join(gdir, fn))
            done = sum(1 for g in goals if g["status"] == "reached")
            not_done = [g["text"] for g in goals if g["status"] != "reached"]
            blocked = sum(1 for t in not_done if "blocked" in t.lower())
            agents.append({"agent": fn[:-3], "total": len(goals), "done": done,
                           "open": len(not_done), "blocked": blocked})
    except Exception as e:
        return {"ok": False, "error": str(e), "agents": []}
    total = sum(a["total"] for a in agents)
    done_all = sum(a["done"] for a in agents)
    return {"ok": True, "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "fleet_pct": round(100.0 * done_all / total, 1) if total else 0.0,
            "fleet_done": done_all, "fleet_total": total, "agents": agents}


_EVOLUTION = None


def _evolution_mod():
    """Load the evolution engine (portal-root evolution.py) once. EVOLUTION_HOME is pinned
    to HERE/evolution via setdefault, so the island never depends on the portal's launch cwd;
    a pre-set env var still wins (scratch-island tests)."""
    global _EVOLUTION
    if _EVOLUTION is None:
        os.environ.setdefault("EVOLUTION_HOME", os.path.join(HERE, "evolution"))
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("_evolution_engine", os.path.join(HERE, "evolution.py"))
        _mod = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_mod)
        _EVOLUTION = _mod
    return _EVOLUTION


def _evolution_snapshot():
    """Evolution layer island state (CHG-0002, gen 1): population table + graveyard as JSON.
    Thin read over evolution.py - same counts as `python evolution.py stats`."""
    try:
        ev = _evolution_mod()
    except Exception as e:
        return {"ok": False, "error": "evolution engine not loadable: %s" % e}
    data = ev.load_pop()
    grave = ev.load_grave()
    ch = data["changes"]
    living = [c for c in ch if c["status"] == "living"]
    cand = [c for c in ch if c["status"] == "candidate"]
    dead_all = len(grave["deaths"])
    born_total = len(ch) + dead_all
    gens = [c["generation"] for c in ch] + [c["generation"] for c in grave["deaths"]]
    return {"ok": True,
            "island": data["meta"].get("island"),
            "started": data["meta"].get("started"),
            "cap": data["meta"].get("max_population", ev.MAX_POPULATION),
            "living": len(living), "candidates": len(cand), "dead": dead_all,
            "born_total": born_total,
            "survival_pct": round(100.0 * len(living) / born_total, 1) if born_total else 0.0,
            "max_generation": max(gens) if gens else 0,
            "changes": sorted(ch, key=lambda x: x["id"]),
            "graveyard": grave["deaths"]}


def _run_index_check():
    """Pre-prune ritual (Archivist goal 2): run memory/archivist/index_check.py so
    every prune commit is index-clean. Returns (rc, output). rc: 0=clean,
    1=dangling INDEX pointers (hard fail - block), 2=orphans only (soft - accepted
    noise per archivist ruling 2026-11-15, proceed with warning), >=3=tool error
    (fail-closed - block)."""
    script = os.path.join(HERE, "memory", "archivist", "index_check.py")
    try:
        # 2026-11-15: CREATE_NO_WINDOW - child python console must not pop up (portal runs under pythonw)
        r = subprocess.run([sys.executable, script], capture_output=True,
                           text=True, timeout=120, creationflags=0x08000000)
        out = (r.stdout or "") + (("\n[stderr] " + r.stderr) if r.stderr else "")
        return r.returncode, out
    except Exception as e:
        return 3, "index_check failed to run: %s" % e


def _prune_todo():
    """Move TODO.md sections whose items are ALL [x] (and at least one [x]) into
    TODO_completed.md. When the completed file outgrows DONE_MAX_LINES, its oldest
    DONE_PART_SIZE lines are split off into todo_done_parts/TODO_done_part_NNN.md.
    Sections with any open item stay put. Idempotent; returns a summary."""
    lines = open(TODO_FILE, encoding="utf-8").read().splitlines()
    pre, secs, cur = [], [], None
    for ln in lines:
        if ln.startswith("## "):
            if cur is not None:
                secs.append(cur)
            cur = [ln]
        elif cur is not None:
            cur.append(ln)
        else:
            pre.append(ln)
    if cur is not None:
        secs.append(cur)

    def counts(sec):
        d = sum(1 for l in sec if re.match(r"^\s*-\s*\[x\]", l, re.I))
        o = sum(1 for l in sec if re.match(r"^\s*-\s*\[ \]", l, re.I))
        return d, o

    moved, kept, n_items = [], [], 0
    for sec in secs:
        d, o = counts(sec)
        if d > 0 and o == 0:
            moved.append(sec)
            n_items += d
        else:
            kept.append(sec)
    if not moved:
        return {"ok": True, "moved_sections": 0, "moved_items": 0,
                "note": "no fully-completed sections to prune"}

    stamp = time.strftime("%Y-%m-%d %H:%M")
    block = ["", "<!-- pruned from TODO.md on %s -->" % stamp]
    for sec in moved:
        block.append("")
        block.extend(sec)
    dlines = open(DONE_FILE, encoding="utf-8").read().splitlines() if os.path.exists(DONE_FILE) \
        else ["# TODO — completed items (pruned from TODO.md)"]
    dlines += block
    chunks = 0
    while len(dlines) > DONE_MAX_LINES:
        if not os.path.isdir(DONE_PART_DIR):
            os.makedirs(DONE_PART_DIR, exist_ok=True)
        n = (len([f for f in os.listdir(DONE_PART_DIR) if f.endswith(".md")]) + 1)
        part = os.path.join(DONE_PART_DIR, "TODO_done_part_%03d.md" % n)
        head, rest = dlines[:1], dlines[1:]
        take, rest = rest[:DONE_PART_SIZE], rest[DONE_PART_SIZE:]
        open(part, "w", encoding="utf-8").write(
            "\n".join(["# TODO completed — part %03d (oldest first)" % n] + take) + "\n")
        dlines = head + rest
        chunks += 1
    open(DONE_FILE, "w", encoding="utf-8").write("\n".join(dlines).rstrip() + "\n")
    new_todo = list(pre)
    for sec in kept:
        new_todo.extend(sec)
    open(TODO_FILE, "w", encoding="utf-8").write("\n".join(new_todo).rstrip() + "\n")
    return {"ok": True, "moved_sections": len(moved), "moved_items": n_items,
            "completed_lines": len(dlines), "chunks_split": chunks}


def _git(args, timeout=90):
    import subprocess
    try:
        # 2026-11-15: CREATE_NO_WINDOW - child git console must not pop up (portal runs under pythonw)
        r = subprocess.run([GIT_EXE] + args, cwd=HERE, capture_output=True, text=True, timeout=timeout,
                           creationflags=0x08000000)
        return {"ok": r.returncode == 0, "out": (r.stdout or "").strip()[:8000],
                "err": (r.stderr or "").strip()[:2000]}
    except Exception as e:
        return {"ok": False, "out": "", "err": str(e)[:300]}


def _git_status():
    if not os.path.isdir(os.path.join(HERE, ".git")):
        return {"repo": False, "note": "run POST /api/git {action:'init'} first"}
    st = _git(["status", "--short"])
    lg = _git(["log", "--oneline", "-12"])
    changed = len([l for l in st["out"].splitlines() if l.strip()])
    return {"repo": True, "changed": changed, "status": st["out"], "log": lg["out"]}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _html(self, path):
        try:
            data = open(os.path.join(HERE, "index.html"), "rb").read()
        except Exception as e:
            return self._json(500, {"error": str(e)})
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _proxy_get(self, path):
        # Global proxy stays on LOCAL Studio (model picker); per-agent routing is studio_base().
        try:
            with urllib.request.urlopen(STUDIO + path, timeout=15) as r:
                return json.load(r)
        except Exception as e:
            return {"error": str(e), "data": []}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _evolution_mutate(self, body):
        """POST /api/evolution/accept {id, note} | /api/evolution/reject {id, cause, note}.
        Thin wrappers over evolution.cmd_accept / cmd_reject (CHG-0002, gen 1). Engine
        rejections arrive as SystemExit and map to 409; the response carries the resulting
        change record plus fresh island counts."""
        action = self.path.split("?")[0].rsplit("/", 1)[-1]
        cid = (body.get("id") or "").strip()
        if not re.match(r"^CHG-\d{4}$", cid):
            return self._json(400, {"error": "id must look like CHG-0001"})
        ev = _evolution_mod()
        import types as _t
        ns = _t.SimpleNamespace(id=cid, note=(body.get("note") or ""), cause=(body.get("cause") or ""))
        try:
            if action == "accept":
                ev.cmd_accept(ns)
            else:
                ev.cmd_reject(ns)
        except SystemExit as e:
            msg = e.code if isinstance(e.code, str) else str(e)
            return self._json(409, {"error": msg, "id": cid})
        snap = _evolution_snapshot()
        rec = next((c for c in snap.get("changes", []) if c["id"] == cid), None)
        if rec is None:
            rec = next((d for d in snap.get("graveyard", []) if d["id"] == cid), None)
        return self._json(200, {"ok": True, "action": action, "change": rec,
                                "living": snap.get("living"),
                                "candidates": snap.get("candidates"),
                                "dead": snap.get("dead")})

    def _stream_run_events(self):
        """SSE: replay the journaled events of a group run from ?cursor=, then live-tail
        until the run's terminal 'end' event. This is what makes hard-refreshes harmless -
        a reloaded tab re-attaches and sees exactly where the backend left off."""
        q = urllib.parse.parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
        rid = (q.get("run") or [""])[0]
        try:
            cursor = int((q.get("cursor") or ["0"])[0])
        except ValueError:
            cursor = 0
        run = _load_group_run()
        if not rid or run.get("id") != rid:
            return self._json(404, {"error": "unknown run"})
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        path = os.path.join(RUNS_DIR, rid + ".journal")
        state = {"pos": 0, "fh": None, "sent_end": False}
        deadline = time.time() + 3600 * 2

        def drain():
            data = state["fh"].read()
            if not data:
                return
            i = data.rfind(b"\n")
            full, rest = (data[:i + 1], data[i + 1:]) if i >= 0 else (b"", data)
            for line in full.splitlines():
                try:
                    ev = json.loads(line)
                except Exception:
                    continue
                if int(ev.get("seq", 0)) <= cursor:
                    continue
                self.wfile.write(b"data: " + line + b"\n\n")
                self.wfile.flush()
                if ev.get("run") == "end":
                    state["sent_end"] = True
            state["pos"] += len(full)

        try:
            while not state["sent_end"] and time.time() < deadline:
                if state["fh"] is None:
                    if os.path.exists(path):
                        state["fh"] = open(path, "rb")
                    else:
                        st = _load_group_run()
                        if st.get("status") != "running":
                            break
                        time.sleep(0.25)
                        continue
                drain()
                time.sleep(0.25)
            if state["fh"] is not None:
                state["fh"].close()
        except OSError:
            pass  # client gone (refresh / tab closed) - the run keeps going on the backend

    def do_GET(self):
        p = self.path.split("?")[0]
        if p in ("/", "/index.html"):
            return self._html("index.html")
        if p == "/api/agents":
            return self._json(200, load_agents())
        elif p == "/api/user-messages":
            return self._json(200, {"ok": True, "messages": umq_view([a["name"] for a in load_agents()["agents"]])})
        elif p == "/api/history":
            q = urllib.parse.parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
            m2 = (q.get("mode") or ["group"])[0]
            return self._json(200, {"ok": True, "history": _load_history(m2) if m2 in CHAT_HISTORY_FILES else []})
        elif p == "/api/run-state":
            base = dict(_load_run_state() or {})
            run = _load_group_run()
            if run.get("id"):
                if run.get("status") == "running":
                    base.update({"busy": True, "mode": "group", "phase": run.get("phase", ""),
                                 "run_id": run["id"], "cast": run.get("cast", []),
                                 "settled": run.get("settled", []), "nudges": run.get("nudges", 0),
                                 "hist_start": run.get("hist_start"),
                                 "prompt": (run.get("prompt") or "")[:300]})
                else:
                    base.update({"busy": False, "mode": "group", "run_id": run["id"],
                                 "status": run["status"], "verdict": run.get("verdict"),
                                 "hist_start": run.get("hist_start")})
            return self._json(200, base)
        elif p == "/api/run-events":
            return self._stream_run_events()
        elif p == "/api/models":
            return self._json(200, self._proxy_get("/v1/models"))
        elif p == "/api/status":
            return self._json(200, self._proxy_get("/api/inference/status"))
        elif p == "/api/fleet":
            # Fleet Status panel (2026-11-13): per-host models + busy/idle/unknown.
            # On-demand probes only (no background timer); dead host => unknown, no hang.
            return self._json(200, _fleet_snapshot())
        elif p == "/api/git":
            # Local git repo status + recent log (Ops panel, 2026-11-13).
            return self._json(200, _git_status())
        elif p == "/api/ops":
            # Ops panel host tiles (2026-11-15): disk usage + portal uptime.
            return self._json(200, _ops_snapshot())
        elif p == "/api/goals":
            # Goal Velocity dashboard (2026-11-15, Designer): per-agent goal progress.
            return self._json(200, _goals_snapshot())
        elif p == "/api/provenance":
            # Goal provenance report (2026-11-15, Builder).
            try:
                with open(os.path.join(HERE, "memory", "archivist", "goal_provenance_report.json"), encoding="utf-8") as f:
                    return self._json(200, {"ok": True, **json.load(f)})
            except Exception as e:
                return self._json(200, {"ok": False, "error": str(e)})
            # Goal Velocity dashboard (2026-11-15, Designer): per-agent goal progress.
            return self._json(200, _goals_snapshot())
        elif p == "/api/evolution/stats":
            # Evolution layer island (CHG-0002, gen 1): population table + graveyard JSON.
            return self._json(200, _evolution_snapshot())
        elif p == "/api/knowledge-bases":
            return self._json(200, self._proxy_get("/api/rag/knowledge-bases"))
        elif p == "/api/tools":
            return self._json(200, {"local_tools": LOCAL_TOOLS, "reasoning_levels": REASONING_LEVELS})
        elif p == "/api/memory":
            text, st = load_memory()
            inf = bool(st.get("infinite_budget", True))
            return self._json(200, {"text": text, "limit": None if inf else XTALK_LIMIT,
                                    "infinite_budget": inf,
                                    "inter_agent_replies": st["inter_agent_replies"],
                                    "last_reset_by": st["last_reset_by"]})
        elif p == "/api/memory/file":
            rel = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("path", [""])[0]
            full = _safe_memory_file(rel)
            if not full:
                return self._json(400, {"error": "path must stay inside memory/"})
            try:
                text = open(full, encoding="utf-8").read()[:65536]
                return self._json(200, {"path": rel.replace("\\", "/"), "text": text})
            except Exception as e:
                return self._json(404, {"error": str(e)})
        elif p == "/api/activity":
            # Activity timeline (2026-11-12): no session param -> recent-sessions index;
            # ?session=<id> -> that session's event list (start/tool/end/blocked/error/aborted).
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            return self._json(200, load_activity(q.get("session", [""])[0] or None))
        elif p == "/api/manifest":
            # Ground truth for the file-link layer (2026-11-12, spec memory/portal/file-links.md):
            # bounded walk of HERE + SANDBOX_DIR -> relative path + mtime ONLY. Skips dotfiles
            # and noise dirs; per-entry try/except so a mid-write file is OMITTED, never an error
            # (Quinn's hole #2). Capped for safety - the shared folder is small by design.
            files = {}
            skip_dirs = {"__pycache__", ".unsloth-tmp", "unsloth-tmp", "AppData", "Microsoft", "Python"}
            for root in (HERE, SANDBOX_DIR):
                if not root:
                    continue
                base = os.path.realpath(root)
                if not os.path.isdir(base):
                    continue
                try:
                    for dirpath, dirnames, filenames in os.walk(base):
                        dirnames[:] = [d for d in dirnames
                                       if not d.startswith(".") and d not in skip_dirs]
                        for fn in filenames:
                            if fn.startswith("."):
                                continue
                            fp = os.path.join(dirpath, fn)
                            try:
                                mt = os.stat(fp).st_mtime
                            except OSError:
                                continue  # gone mid-walk (mid-write etc.) -> omit, never error
                            rel = os.path.relpath(fp, base).replace("\\", "/")
                            if root == HERE or rel not in files:  # HERE wins on collision
                                files[rel] = mt
                except OSError:
                    continue
            out = [{"path": k, "mtime": round(v, 1)} for k, v in sorted(files.items())][:4000]
            return self._json(200, {"count": len(out), "files": out})
        elif p == "/api/uploads":
            # List what humans have uploaded (uploads/ in the shared agent folder).
            out = []
            if os.path.isdir(UPLOAD_DIR):
                up_base = os.path.realpath(UPLOAD_DIR)
                for root, dirs, files in os.walk(up_base):
                    dirs[:] = sorted(dirs)
                    for f in sorted(files):
                        fp = os.path.join(root, f)
                        try:
                            stt = os.stat(fp)
                        except OSError:
                            continue
                        rel = os.path.relpath(fp, os.path.dirname(up_base)).replace("\\", "/")
                        out.append({"path": rel, "size": stt.st_size, "mtime": round(stt.st_mtime, 1)})
            return self._json(200, {"count": len(out), "files": out[:2000]})
        elif p == "/api/file":
            # Existence check + first lines for the hover-peek popover. Frontend probes
            # path-like tokens from agent replies; only 200s become links.
            rel = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("path", [""])[0]
            full = _safe_workspace_file(rel)
            if not full:
                return self._json(404, {"error": "file not found in workspace"})
            try:
                if os.path.isdir(full):  # folder reference: peek shows a directory listing
                    entries = sorted(os.listdir(full))[:40]
                    ls = []
                    for e in entries:
                        fp = os.path.join(full, e)
                        sz = os.path.getsize(fp) if os.path.isfile(fp) else None
                        ls.append("  " + e + "/" if sz is None else "  %-32s %8.1f KB" % (e, sz / 1024))
                    fname = os.path.basename(full) or rel.strip("/")
                    out = {"path": rel.replace("\\", "/"), "name": fname + " (folder)", "size": None,
                           "head": "<folder> %s (%d entries)\n%s" % (fname, len(entries), "\n".join(ls))}
                    return self._json(200, out)
                stt = os.stat(full)
                # echo the REQUESTED rel path: the frontend matches this exact string in reply text
                # (relpath-from-HERE broke sandbox files -> '../../Users/...' never matched, no link)
                out = {"path": rel.replace("\\", "/"),
                       "name": os.path.basename(full), "size": stt.st_size}
                with open(full, "rb") as f:
                    head_b = f.read(8192)
                if b"\x00" in head_b:  # binary (image etc.): no text preview
                    out["binary"] = True
                else:
                    lines = head_b.decode("utf-8", "replace").splitlines()
                    out["head"] = "\n".join(lines[:40])
                    if len(lines) > 40 or len(head_b) == 8192:
                        out["truncated"] = True
                return self._json(200, out)
            except Exception as e:
                return self._json(404, {"error": str(e)})
        elif p == "/api/file/raw":
            # Open the file in a new tab (click target for .flink). Same traversal guard.
            rel = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("path", [""])[0]
            full = _safe_workspace_file(rel)
            if not full:
                return self._json(404, {"error": "file not found in workspace"})
            try:
                if os.path.isdir(full):  # folder link click: plain-text listing in the new tab
                    entries = sorted(os.listdir(full))[:200]
                    ls = []
                    for e in entries:
                        fp = os.path.join(full, e)
                        sz = os.path.getsize(fp) if os.path.isfile(fp) else None
                        ls.append(e + ("/" if sz is None else "  (%.1f KB)" % (sz / 1024)))
                    data = ((rel.strip("/") or "/") + " - folder, " + str(len(entries)) + " entries\n\n"
                            + "\n".join(ls)).encode()
                else:
                    data = open(full, "rb").read()
                if len(data) > 32 * 1024 * 1024:
                    return self._json(413, {"error": "file too large to open in browser"})
                # Serve the REAL file type: .html must render as a website, not show source.
                # (old code forced every text/* to text/plain -> HTML pages displayed raw)
                ctype, _ = mimetypes.guess_type(full)
                if ctype is None:
                    ctype = "text/plain; charset=utf-8"
                elif ";" not in ctype and (
                        ctype.startswith("text/") or ctype == "application/json"):
                    ctype += "; charset=utf-8"
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except Exception as e:
                return self._json(500, {"error": str(e)})
        else:
            self._json(404, {"error": "not found"})

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n).decode() or "{}") if n else {}

    def _upload(self):
        """Raw binary upload: body = file bytes, X-Rel-Path header = target path (lands under
        uploads/ in the shared agent folder). Streamed to disk in 1 MiB chunks. Returns the
        portal-relative path so replies can link it exactly like agent-built files."""
        resolved = _safe_upload_path(self.headers.get("X-Rel-Path", ""))
        if not resolved:
            return self._json(400, {"error": "bad or unsafe path (relative paths only; lands in uploads/)"})
        full, rel_clean = resolved
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0:
            return self._json(400, {"error": "empty body"})
        if n > MAX_UPLOAD_BYTES:
            return self._json(413, {"error": "file too large (max %d GB)" % (MAX_UPLOAD_BYTES // (1024 ** 3))})
        try:
            os.makedirs(os.path.dirname(full), exist_ok=True)
            written = 0
            with open(full, "wb") as out:
                while written < n:
                    chunk = self.rfile.read(min(1024 * 1024, n - written))
                    if not chunk:
                        break
                    out.write(chunk)
                    written += len(chunk)
        except Exception as e:
            return self._json(500, {"error": f"write failed: {e}"})
        return self._json(201, {"ok": True, "path": rel_clean.replace("\\", "/"), "size": written})

    def do_POST(self):
        p = self.path.split("?")[0]
        if p == "/api/upload":
            return self._upload()
        try:
            body = self._body()
        except Exception as e:
            return self._json(400, {"error": f"bad json: {e}"})
        if p == "/api/user-messages":
            entry = umq_add(body.get("text"), body.get("mentions"))
            if not entry:
                return self._json(400, {"error": "text required"})
            return self._json(200, {"ok": True, "message": entry})
        elif p == "/api/user-messages/check":
            names = [a["name"] for a in load_agents()["agents"]]
            mid = body.get("id") or ""
            n = umq_check([mid] if isinstance(mid, str) and mid else [],
                          (body.get("agent") or "").strip() or "*", names)
            return self._json(200, {"ok": True, "checked": n})
        elif p == "/api/history":
            m2 = (body.get("mode") or "").strip()
            if m2 not in CHAT_HISTORY_FILES:
                return self._json(400, {"error": "mode must be 'group' or 'solo'"})
            if m2 == "group":
                # 2026-11-15: group history is backend-owned (the run engine appends to it);
                # client pushes are ignored so a stale tab can never clobber a live run.
                return self._json(200, {"ok": True, "ignored": "group history is backend-owned"})
            _save_history(m2, body.get("history"))
            return self._json(200, {"ok": True})
        elif p == "/api/run-state":
            _save_run_state({"busy": bool(body.get("busy")),
                             "mode": str(body.get("mode") or "")[:16],
                             "phase": str(body.get("phase") or "")[:40],
                             "ts": int(body.get("ts") or 0)})
            return self._json(200, {"ok": True})
        elif p == "/api/group-run":
            text = (body.get("text") or "").strip()
            if not text:
                return self._json(400, {"error": "text required"})
            run, err = start_group_run(text)
            if err:
                return self._json(409, {"error": err})
            return self._json(200, {"ok": True, "run_id": run["id"], "cast": run["cast"]})
        elif p == "/api/run-stop":
            rid = (body.get("run_id") or "").strip()
            ev = _run_stops.get(rid)
            if not ev:
                return self._json(404, {"error": "no such run"})
            ev.set()
            return self._json(200, {"ok": True})
        elif p == "/api/chat":
            _sync_workspace_to_sandbox()   # two-way: push shared state, pull agent work home (LWW + new-only)
            aid = body.get("agent_id") or ""
            mode = body.get("mode", "solo")
            agent = get_agent(aid)
            if not agent:
                return self._json(404, {"error": "unknown agent"})
            kind = body.get("kind") or "prompt"
            if kind not in ("prompt", "cross-talk"):
                kind = "prompt"
            messages = body.get("messages") or []
            msgs = [{"speaker": m.get("speaker"), "content": (m.get("content") or "")[:20000]}
                    for m in messages[-60:]]
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            try:
                stream_chat(self.wfile, agent, msgs, mode, kind, body.get("session"))
            except OSError:   # client gone (■ Stop / tab closed) - nothing left to deliver
                pass
            _sync_workspace_to_sandbox()   # same-turn sandbox work lands in HERE before the commit
            _auto_commit()                 # post-turn auto-commit: repo drift <= 1 turn (Builder goal #5)
        elif p == "/api/memory":
            action = body.get("action") or ""
            if action == "budget":
                # Toggle the infinite budget; persists in memory.md's state line.
                text, st = load_memory()
                st["infinite_budget"] = bool(body.get("infinite", True))
                _write_memory(text, st)
                return self._json(200, {"ok": True, "infinite_budget": st["infinite_budget"],
                                        "limit": None if st["infinite_budget"] else XTALK_LIMIT,
                                        "inter_agent_replies": st["inter_agent_replies"]})
            if action != "reset":
                return self._json(400, {"error": "unknown action (use 'reset' or 'budget')"})
            text, st = load_memory()
            st["inter_agent_replies"] = 0
            st["last_reset_by"] = ""
            _write_memory(text, st)
            return self._json(200, {"ok": True,
                                    "infinite_budget": bool(st.get("infinite_budget", True)),
                                    "limit": None if st.get("infinite_budget", True) else XTALK_LIMIT,
                                    "inter_agent_replies": 0, "last_reset_by": ""})
        elif p == "/api/scan-models":
            # Add-agent UI: probe a (remote) Studio with its Bearer key and list models.
            code, payload = scan_remote_models(body.get("base_url"), body.get("api_key"))
            return self._json(code, payload)
        elif p == "/api/todo/prune":
            # Ops: move fully-completed TODO sections into TODO_completed.md (chunk-splitting).
            try:
                _sync_workspace_to_sandbox()   # two-way sync first: agent TODO/MEMORY edits land before pruning
                rc, ic_out = _run_index_check()  # pre-prune ritual: every prune commit is index-clean
                if rc == 1 or rc >= 3:
                    why = ("DANGLING INDEX pointers found - repair the INDEX.md target(s) and retry"
                           if rc == 1 else "index_check itself failed (fail-closed)")
                    return self._json(409, {"ok": False,
                                             "error": "prune blocked: %s (index_check rc=%d)" % (why, rc),
                                             "index_check": ic_out[-2000:]})
                res = _prune_todo()
                res["index_check"] = {"rc": rc,
                                      "note": "clean" if rc == 0
                                      else "orphans only - accepted noise, prune proceeded (soft)",
                                      "output_tail": ic_out[-800:]}
                _auto_commit()                 # prune result is shared state - commit it (drift <= 1 turn)
                return self._json(200, res)
            except Exception as e:
                return self._json(500, {"error": str(e)})
        elif p == "/api/git":
            # Ops: local git management (commit / init) for the project workspace.
            action = (body.get("action") or "").strip()
            if action == "init":
                _git(["init"])
                _git(["config", "user.name", "Agent Portal"])
                _git(["config", "user.email", "portal@agent-portal.local"])
                return self._json(200, {"ok": True, "status": _git_status()})
            if action == "commit":
                msg = (body.get("message") or "").strip()[:300]
                if not msg:
                    return self._json(400, {"error": "message required"})
                _git(["add", "-A"])
                c = _git(["commit", "-m", msg])
                combined = (c["out"] + c["err"]).lower()
                return self._json(200, {"ok": True,
                                        "committed": c["ok"] and "nothing to commit" not in combined,
                                        "note": "nothing to commit" if "nothing to commit" in combined else "",
                                        "out": c["out"], "err": c["err"],
                                        "status": _git_status()})
            return self._json(400, {"error": "unknown action (use 'commit' or 'init')"})
        elif p == "/api/agents":
            name = (body.get("name") or "").strip()
            if not name:
                return self._json(400, {"error": "name required"})
            aid = body.get("id") or ("a-" + uuid.uuid4().hex[:6])
            data = load_agents()
            agent = {"id": aid, "name": name, "emoji": "\U0001F916", "color": "#3ddc84"}
            agent.update(default_agent_fields())
            apply_agent_fields(agent, body)
            data["agents"].append(agent)
            save_agents(data)
            self._json(200, {"ok": True, "agent": agent})
        elif p in ("/api/evolution/accept", "/api/evolution/reject"):
            # Evolution layer (CHG-0002, gen 1): thin wrappers over evolution.cmd_accept/reject.
            return self._evolution_mutate(body)
        else:
            self._json(404, {"error": "not found"})

    def do_PUT(self):
        p = self.path.split("?")[0]
        m = re.match(r"^/api/agents/(.+)$", p)
        if not m:
            return self._json(404, {"error": "not found"})
        aid = m.group(1)
        try:
            data = self._body()
        except Exception as e:
            return self._json(400, {"error": f"bad json: {e}"})
        agents = load_agents()["agents"]
        hit = False
        for a in agents:
            if a["id"] == aid:
                apply_agent_fields(a, data)
                hit = True
        if not hit:
            return self._json(404, {"error": "unknown agent"})
        save_agents({"agents": agents})
        self._json(200, {"ok": True})

    def do_DELETE(self):
        m = re.match(r"^/api/agents/(.+)$", self.path.split("?")[0])
        if not m:
            return self._json(404, {"error": "not found"})
        aid = m.group(1)
        agents = load_agents()["agents"]
        left = [a for a in agents if a["id"] != aid]
        if len(left) == len(agents):
            return self._json(404, {"error": "unknown agent"})
        save_agents({"agents": left})
        self._json(200, {"ok": True})


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Agent portal -> http://127.0.0.1:{PORT}  (backed by Studio at {STUDIO})")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
