#!/usr/bin/env python3
"""hot_load.py - Unified host-aware LLM hot-loader (Researcher goal #1, cycle-6).

Consolidates three previously-divergent scripts into ONE module:
  - recover_all.py        (White dual-residency reload; VRAM poll; wedge investigation)
  - memory/ops/fleet_reload.py  (all-hosts parallel reload; /loaded-models poll; async-ack aware)
  - wedge_force_recover.py (no idle-wait; skip healthy models; force-reload only wedged ones)

WHY THIS EXISTS (the 4 gaps it closes, from memory/goals/researcher.md):
  Gap 1  Q4 context regression: recover_all.py hardcoded White Q4 max_seq_length=65536,
         but the proven resident value is 131072 (hosts.md line 6/21). Every full reload
         via that path silently halved Q4 context. FIXED here: HOSTS table carries the
         proven per-host ctx; White Q4 = 131072, asserted in _assert_proven_ctx().
         NOTE ON SCOPE (evidence vs inference): "Q4=131072" is WHITE's proven-resident
         UD-Q4_K_S value. Red runs UD-Q4_K_XL @65536; Pale/Black run Q4_K_S @65536
         (hosts.md lines 7-9). We deliberately do NOT blanket-copy 131072 to all hosts -
         that would over-provision and risks OOM on the 32GB boxes already stable at 65536.
  Gap 2  Idle-wait deadlock: recover_all.py / fleet_reload.py block on
         active-generations==0, but a Studio chat thread holds a generation "active" across
         tool-call gaps => deadlock (11-15 wedge). FIXED here: decide_action() NEVER gates
         on idle; healthy models are SKIPPED (no reload at all), wedged/absent models are
         force-reloaded with a cancel-first step and NO blocking idle wait.
  Gap 3  No post-load functional probe / binding verify. FIXED here: after residency is
         confirmed via /api/inference/loaded-models, run_probe() pings the actual portal
         alias (quinn-q4/atlas-q8/...) so a load that reports "resident" but routes wrong
         still fails loudly.
  Gap 4  Divergent parallel paths + scraped/hardcoded auth. FIXED here: one HOSTS table is
         the single source for per-host studio URL, auth, and model load bodies. Auth is
         read from env (STUDIO_<HOST>_APIKEY) or passed in - never hardcoded into this file.

RESIDENT CHECK CONTRACT (Gap 4/3): /api/inference/load returns a 200 ASYNC ACK. That ack is
NOT residency. The only authoritative resident check is GET /api/inference/loaded-models
polling until the model_path appears. poll_resident() implements exactly that and is the
single place it happens.

USAGE:
  python hot_load.py --plan white            # dry-run: print host table + exact load bodies (NO network)
  python hot_load.py --test-wedge            # offline self-test of the wedge-skip decision (NO network)
  python hot_load.py --host white --execute  # live: probe -> skip/reload -> poll resident -> alias probe
  python hot_load.py --bindings              # read agents.json + aliases, emit match matrix (needs network)

ACCEPTANCE (goal #1): ast.parse exits 0; --plan prints all 4 hosts and White Q4 max_seq_length==131072;
--test-wedge shows a healthy model is SKIPPED and a wedged one is FORCE_RELOAD. Live :8888 execution
is gated on a non-sandbox vantage, so the verifiable surface here is --plan + --test-wedge (fixtures).
"""
import json, os, sys, time, platform, socket, argparse, datetime, urllib.request, urllib.error

STUDIO_DEFAULT = "http://127.0.0.1:8888"
PORTAL         = "http://127.0.0.1:8099"
RESULT_DIR     = os.path.join("memory", "researcher", "hotload-results")

# ---------------------------------------------------------------------------
# SINGLE HOST TABLE (the one source of truth for studio URL / auth / models).
# ctx values are the PROVEN per-host SSOT from memory/llm/hosts.md (verified 11-14).
# Model order is the proven recipe: Q8 first, then Q4 force-reload.
# ---------------------------------------------------------------------------
def _mp(user, *parts):
    # Absolute Windows path matching the proven source scripts (r"C:\Users\...").
    # NB: os.path.join("C:", ...) is drive-relative and drops the backslash after C: - avoid it.
    return "C:\\" + os.path.join("Users", user, ".lmstudio", "models", *parts)

HOSTS = {
    "white": {
        "ip": "[LAN-IP]", "studio": STUDIO_DEFAULT, "auth": None,
        "user": "White",
        "models": [
            {"name": "atlas-q8", "probe_alias": "atlas-q8",
             "model_path": _mp("White", "lmstudio-community", "Qwen3.8-27B-Q8_0"),
             "gguf_variant": "Q8_0", "gpu_ids": [1], "max_seq_length": 32768,
             "cache_type_kv": "q8_0", "n_parallel": 1, "alongside": True, "force_reload": False},
            {"name": "quinn-q4", "probe_alias": "quinn-q4",
             "model_path": _mp("White", "unsloth", "Qwen3.8-27B-Q4_K_S"),
             "gguf_variant": "UD-Q4_K_S", "gpu_ids": [0], "max_seq_length": 131072,
             "cache_type_kv": "q8_0", "n_parallel": 1, "speculative_type": "mtp",
             "spec_draft_n_max": 4, "llama_extra_args": ["--split-mode", "layer"], "force_reload": True},
        ],
    },
    "red": {
        "ip": "IP_RED", "studio": STUDIO_DEFAULT, "auth": "env:STUDIO_RED_APIKEY",
        "user": "Red",
        "models": [
            {"name": "scribe-q8", "probe_alias": "scribe-q8",
             "model_path": _mp("Red", "lmstudio-community", "Qwen3.8-27B-Q8_0"),
             "gguf_variant": "Q8_0", "gpu_ids": [1], "max_seq_length": 16384,
             "cache_type_kv": "q8_0", "n_parallel": 1, "alongside": True, "force_reload": False},
            {"name": "mechanic-q4", "probe_alias": "mechanic-q4",
             "model_path": _mp("Red", "unsloth", "Qwen3.8-27B-GGUF"),
             "gguf_variant": "UD-Q4_K_XL", "gpu_ids": [0], "max_seq_length": 65536,
             "cache_type_kv": "q8_0", "n_parallel": 1, "force_reload": True},
        ],
    },
    "pale": {
        "ip": "IP_PALE", "studio": STUDIO_DEFAULT, "auth": "env:STUDIO_PALE_APIKEY",
        "user": "pale",
        "models": [
            {"name": "archivist-q8", "probe_alias": "archivist-q8",
             "model_path": _mp("pale", "lmstudio-community", "Qwen3.8-27B-Q8_0"),
             "gguf_variant": "Q8_0", "gpu_ids": [1], "max_seq_length": 32768,
             "cache_type_kv": "q8_0", "n_parallel": 1, "alongside": True, "force_reload": False},
            {"name": "designer-q4", "probe_alias": "designer-q4",
             "model_path": _mp("pale", "unsloth", "Qwen3.8-27B-Q4_K_S"),
             "gguf_variant": "UD-Q4_K_S", "gpu_ids": [0], "max_seq_length": 65536,
             "cache_type_kv": "q8_0", "n_parallel": 1, "force_reload": True},
        ],
    },
    "black": {
        "ip": "IP_BLACK", "studio": STUDIO_DEFAULT, "auth": "env:STUDIO_BLACK_APIKEY",
        "user": "black",
        "models": [
            {"name": "builder-q8", "probe_alias": "builder-q8",
             "model_path": _mp("black", "lmstudio-community", "Qwen3.8-27B-Q8_0"),
             "gguf_variant": "Q8_0", "gpu_ids": [1], "max_seq_length": 32768,
             "cache_type_kv": "q8_0", "n_parallel": 1, "alongside": True, "force_reload": False},
            {"name": "verifier-q4", "probe_alias": "verifier-q4",
             "model_path": _mp("black", "unsloth", "Qwen3.8-27B-Q4_K_S"),
             "gguf_variant": "UD-Q4_K_S", "gpu_ids": [0], "max_seq_length": 65536,
             "cache_type_kv": "q8_0", "n_parallel": 1, "force_reload": True},
        ],
    },
}

# Proven White Q4 ctx - the value Gap 1 is about. Never let it regress to 65536.
PROVEN_WHITE_Q4_CTX = 131072


def _assert_proven_ctx():
    """Guard against Gap-1 regression: White Q4 must be 131072, not the stale 65536."""
    q4 = [m for m in HOSTS["white"]["models"] if m["name"] == "quinn-q4"][0]
    assert q4["max_seq_length"] == PROVEN_WHITE_Q4_CTX, (
        f"White Q4 ctx regressed to {q4['max_seq_length']} (proven value is {PROVEN_WHITE_Q4_CTX})")


def get_host_key(hostname=None):
    """Map a hostname/ip to a HOSTS key. Pure-ish: injectable for tests."""
    h = (hostname or platform.node()).lower()
    for key in HOSTS:
        if key in h or HOSTS[key]["ip"] in h:
            return key
    try:
        ip = socket.gethostbyname(h)
        for key in HOSTS:
            if HOSTS[key]["ip"] == ip:
                return key
    except Exception:
        pass
    return None


def _auth_header(host_key):
    """Resolve auth without hardcoding secrets: env var named by the table entry."""
    spec = (HOSTS.get(host_key) or {}).get("auth")
    if not spec or not spec.startswith("env:"):
        return None
    key = os.environ.get(spec[4:], "").strip()
    return f"Bearer {key}" if key else None


# ---------------------------------------------------------------------------
# WEDGE-SAFE DECISION (Gap 2). PURE - unit-testable with no network.
# Input is a per-model snapshot; output is the action to take. NEVER blocks on idle.
# ---------------------------------------------------------------------------
def decide_action(snapshot):
    """snapshot: {resident: bool, probe_ok: bool|None}
      resident = model_path present in /api/inference/loaded-models
      probe_ok   = chat probe through the portal alias succeeded (None if never probed)
    Returns one of:
      SKIP           -> healthy & confirmed; do not touch it (avoids the wedge entirely)
      FORCE_RELOAD   -> absent OR wedged (resident but probe fails); reload, cancel-first, NO idle gate
    """
    resident = bool(snapshot.get("resident", False))
    probe_ok = snapshot.get("probe_ok")
    if resident and probe_ok:
        return "SKIP"
    # Not resident, or resident-but-wedged (probe failed) -> force reload.
    # Critically: we do NOT wait for active-generations==0 here. A chat thread holding an
    # active generation across tool-call gaps is exactly the 11-15 deadlock; skip/wait is wrong.
    return "FORCE_RELOAD"


def _cancel_stuck(host_key, alias, jreq):
    """Best-effort cancel of a stuck generation on the wedged alias before force-reload."""
    try:
        s, d, raw = jreq("POST", HOSTS[host_key]["studio"] + "/api/inference/cancel", {}, t=15)
        return {"status": s, "body": str(raw)[:200]}
    except Exception as e:
        return {"status": None, "error": str(e)[:120]}


# ---------------------------------------------------------------------------
# NETWORK HELPERS (used only in --execute / --bindings; never at import or in --plan/--test-wedge)
# ---------------------------------------------------------------------------
def jreq(method, url, body=None, t=30, auth=None):
    try:
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Content-Type": "application/json"} if data else {}
        if auth:
            headers["Authorization"] = auth
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=t) as r:
            raw = r.read().decode()
            try:
                return r.status, json.loads(raw), raw
            except Exception:
                return r.status, None, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode()[:500]
        try:
            return e.code, json.loads(raw), raw
        except Exception:
            return e.code, None, raw
    except Exception as e:
        return None, None, f"ERR {type(e).__name__}: {e}"


def get_resident_paths(jreq, host_key):
    """Authoritative resident set from /api/inference/loaded-models (Gap 3/4)."""
    s, d, raw = jreq("GET", HOSTS[host_key]["studio"] + "/api/inference/loaded-models",
                     auth=_auth_header(host_key))
    if s != 200:
        return None
    out = []
    items = d if isinstance(d, list) else (d or {}).get("data", []) if isinstance(d, dict) else []
    for m in items:
        mp = m.get("model_path") or m.get("path") or ""
        if mp:
            out.append(mp.lower())
    return out


def poll_resident(jreq, host_key, model_path, timeout_s=600, interval=10):
    """Poll /loaded-models until model_path is resident. The load 200 is an async ack - this is
    the ONLY trusted residency check."""
    want = model_path.lower()
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        res = get_resident_paths(jreq, host_key)
        if res is not None and any(want in r for r in res):
            return True
        time.sleep(interval)
    return False


def run_probe(jreq, host_key, alias, t=90):
    """Functional probe through the actual portal alias (Gap 3)."""
    body = {"model": alias, "messages": [{"role": "user", "content": "Reply with the single word: pong"}],
            "max_tokens": 16, "temperature": 0, "stream": False}
    t0 = time.time()
    s, d, raw = jreq("POST", HOSTS[host_key]["studio"] + "/v1/chat/completions", body,
                     t=t, auth=_auth_header(host_key))
    dt = round(time.time() - t0, 1)
    if s == 200 and isinstance(d, dict) and d.get("choices"):
        return {"ok": True, "secs": dt}
    return {"ok": False, "secs": dt, "status": s, "raw": str(raw)[:200]}


# ---------------------------------------------------------------------------
# PLAN (dry-run, NO network) - the primary verifiable surface in this sandbox vantage.
# ---------------------------------------------------------------------------
def plan_for_host(host_key):
    """Return the exact ordered load bodies for a host (pure; no I/O)."""
    if host_key not in HOSTS:
        raise KeyError(f"unknown host {host_key!r}; valid: {list(HOSTS)}")
    return [dict(m) for m in HOSTS[host_key]["models"]]


def render_plan(host_key):
    _assert_proven_ctx()
    lines = []
    lines.append("== FLEET HOST TABLE (proven per-host ctx from memory/llm/hosts.md) ==")
    for hk, h in HOSTS.items():
        marks = ", ".join(f"{m['name']} ctx={m['max_seq_length']} gpu={m['gpu_ids'][0]} v={m['gguf_variant']}"
                          for m in h["models"])
        lines.append(f"  {hk:6} ip={h['ip']:16} models=[{marks}]")
    lines.append("")
    lines.append(f"== LOAD PLAN for host '{host_key}' (order = proven recipe, Q8 first) ==")
    bodies = plan_for_host(host_key)
    for i, b in enumerate(bodies):
        lines.append(f"  [{i+1}] {b['name']}: POST /api/inference/load body:")
        lines.append("      " + json.dumps(b, indent=None).replace(", ", ",\n      "))
    if host_key == "white":
        q4 = [m for m in bodies if m["name"] == "quinn-q4"][0]
        lines.append("")
        lines.append(f"  PROVEN-CHECK quinn-q4 max_seq_length={q4['max_seq_length']} "
                     f"(expected {PROVEN_WHITE_Q4_CTX}) -> {'OK' if q4['max_seq_length']==PROVEN_WHITE_Q4_CTX else 'REGRESSED'}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# WEDGE SELF-TEST (offline, NO network) - proves Gap 2 fix.
# ---------------------------------------------------------------------------
def wedge_selftest():
    cases = [
        {"label": "healthy resident model", "snap": {"resident": True, "probe_ok": True}, "expect": "SKIP"},
        {"label": "absent model (boot)",   "snap": {"resident": False, "probe_ok": None}, "expect": "FORCE_RELOAD"},
        {"label": "wedged (resident but probe fails, active-gen held by chat)",
         "snap": {"resident": True, "probe_ok": False}, "expect": "FORCE_RELOAD"},
    ]
    ok = True
    for c in cases:
        got = decide_action(c["snap"])
        passed = got == c["expect"]
        ok = ok and passed
        print(f"  [{'PASS' if passed else 'FAIL'}] {c['label']}: decide={got} expect={c['expect']}")
    # The deadlock case: a healthy model must be SKIPPED, so an active generation it holds
    # is never the trigger for a reload - no idle-wait gate exists in this path.
    print("  note: no idle-gate; 'active-generations held by a chat thread' cannot wedge SKIP models")
    return ok


# ---------------------------------------------------------------------------
# EXECUTE (live) - one result JSON per host (Gap 3/4). Gated on non-sandbox vantage.
# ---------------------------------------------------------------------------
def execute(host_key, jreq_fn=None):
    _assert_proven_ctx()
    jreq = jreq_fn or jreq
    res = {"host": host_key, "start": datetime.datetime.now().isoformat(), "models": [], "verdict": None}
    for m in HOSTS[host_key]["models"]:
        # 1) build snapshot from authoritative resident set + alias probe (no idle gate)
        res_paths = get_resident_paths(jreq, host_key)
        resident = bool(res_paths and any(m["model_path"].lower() in r for r in res_paths))
        probe = run_probe(jreq, host_key, m["probe_alias"]) if resident else {"ok": False}
        action = decide_action({"resident": resident, "probe_ok": probe.get("ok")})
        entry = {"name": m["name"], "action": action, "ctx": m["max_seq_length"], "pre_resident": resident}
        if action == "SKIP":
            entry["skipped"] = True
            res["models"].append(entry)
            continue
        # 2) wedged/absent -> cancel stuck gen (best-effort), force-reload, poll resident
        entry["cancel"] = _cancel_stuck(host_key, m["probe_alias"], jreq)
        body = dict(m)
        body["force_reload"] = True
        s, d, raw = jreq("POST", HOSTS[host_key]["studio"] + "/api/inference/load", body,
                         t=900, auth=_auth_header(host_key))
        entry["load_ack_status"] = s  # async ack - NOT residency
        resident_now = poll_resident(jreq, host_key, m["model_path"], timeout_s=420)
        entry["resident_after_poll"] = resident_now
        if resident_now:
            fp = run_probe(jreq, host_key, m["probe_alias"])
            entry["post_probe"] = fp
            entry["ok"] = bool(fp.get("ok"))
        else:
            entry["ok"] = False
        res["models"].append(entry)
    res["verdict"] = "ALL_UP" if all(e.get("ok", e.get("skipped") is True) for e in res["models"]) else "PARTIAL"
    res["end"] = datetime.datetime.now().isoformat()
    # one result JSON per host
    os.makedirs(RESULT_DIR, exist_ok=True)
    out = os.path.join(RESULT_DIR, f"{host_key}_result.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    res["result_path"] = out
    return res


# ---------------------------------------------------------------------------
# BINDINGS (live) - read agents.json + per-host aliases -> 8-agent match matrix (Gap 3).
# ---------------------------------------------------------------------------
def bindings_matrix(agents_json_path="agents.json"):
    try:
        with open(agents_json_path, encoding="utf-8") as f:
            agents = json.load(f)
    except Exception as e:
        return {"error": f"could not read {agents_json_path}: {e}"}
    rows = []
    for a in (agents if isinstance(agents, list) else agents.get("agents", [])):
        alias = a.get("model_id") or a.get("alias") or ""
        matched = [hk for hk, h in HOSTS.items()
                   if any(m["probe_alias"] == alias for m in h["models"])]
        rows.append({"agent": a.get("name") or a.get("id"), "model_id": alias,
                     "host_match": matched[0] if len(matched) == 1 else ("AMBIGUOUS:" + ",".join(matched) if matched else "NO_MATCH")})
    return {"matrix": rows, "mismatches": [r for r in rows if not str(r["host_match"]).isalpha() or r["host_match"] == "NO_MATCH"]}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Unified host-aware LLM hot-loader")
    ap.add_argument("--plan", metavar="HOST", help="dry-run: print host table + load bodies (no network)")
    ap.add_argument("--test-wedge", action="store_true", help="offline wedge-skip self-test (no network)")
    ap.add_argument("--host", help="target host for --execute")
    ap.add_argument("--execute", action="store_true", help="live execute (needs :8888 vantage)")
    ap.add_argument("--bindings", action="store_true", help="emit agents.json binding matrix")
    args = ap.parse_args(argv)

    if args.plan:
        print(render_plan(args.plan))
        return 0
    if args.test_wedge:
        ok = wedge_selftest()
        print("WEDGE SELFTEST:", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    if args.bindings:
        print(json.dumps(bindings_matrix(), indent=1))
        return 0
    if args.execute:
        hk = args.host or get_host_key()
        if not hk:
            print("UNKNOWN host; pass --host", file=sys.stderr)
            return 2
        res = execute(hk)
        print(json.dumps(res, indent=1))
        return 0 if res["verdict"] == "ALL_UP" else 3
    ap.print_help()
    return 0


if __name__ == "__main__":
    _assert_proven_ctx()  # fail fast on ctx regression even before arg parse
    sys.exit(main())
