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

EVICITION-AWARENESS RULE (Goal #4). Documented asymmetry (memory/llm/backend-swap-procedure.md,
drill 11-15 SwapDrill1114b): loading White Q4_K_S @131k ctx PUSHES OUT a resident Q8_0 - the
reverse is NOT true (Q8 fits onto a Q4-resident GPU set). So eviction is DIRECTIONAL. Decision
table for "restore dual residency" when loading model A would evict a still-wanted resident B:

  pre-resident          target set           action taken                          result
  -------------------   -------------------  -----------------------------------  ----------------------------------
  {B} (Q8)              {A,B} (want both)    LOAD A -> EVICTS B -> RELOAD B after  final={A,B}; ZERO binding loss;
                                                                     eviction + restore are LOGGED
  {B} (Q8)              {A}   (need A alone) LOAD A -> EVICTS B -> ACCEPT + LOG    final={A}; B gone by intent, LOGGED
  {}                    {A,B}                order loads that avoid the evict path no loss

RULE: never silently lose a resident model. Either (a) RELOAD the evicted still-wanted model AFTER
the evicting load (preserve dual residency), or (b) explicitly ACCEPT + LOG the eviction when the
target set does not want it. restore_order() implements this deterministically; execute() applies
it live. Bindings are path-bound aliases, so eviction never breaks an alias - but residency must be
restored OR logged either way (never silent).

RESIDENT CHECK CONTRACT (Gap 4/3): /api/inference/load returns a 200 ASYNC ACK. That ack is
NOT residency. The only authoritative resident check is GET /api/inference/loaded-models
polling until the model_path appears. poll_resident() implements exactly that and is the
single place it happens.

USAGE:
  python hot_load.py --plan white            # dry-run: print host table + exact load bodies (NO network)
  python hot_load.py --test-wedge            # offline self-test of the wedge-skip decision (NO network)
  python hot_load.py --host white --execute  # live: probe -> skip/reload -> poll resident -> alias probe
  python hot_load.py --bindings              # offline: read agents.json, emit 8-agent match matrix (no network)
  python hot_load.py --bindings --live       # + GET /api/settings/model-aliases per host (needs :8888 vantage)
  python hot_load.py --test-bindings         # offline self-test: reproduces known builder/verifier mismatch
                                              # flags; proves fetch never raises on an unreachable host (no network)
  python hot_load.py --test-eviction         # offline self-test (Goal #4): Q8-resident-before-Q4-reload
                                              # yields zero binding loss + logs the residency change (no network)

ACCEPTANCE (goal #1): ast.parse exits 0; --plan prints all 4 hosts and White Q4 max_seq_length==131072;
--test-wedge shows a healthy model is SKIPPED and a wedged one is FORCE_RELOAD. Live :8888 execution
is gated on a non-sandbox vantage, so the verifiable surface here is --plan + --test-wedge (fixtures).
"""
import json, os, re, sys, time, platform, socket, argparse, datetime, urllib.request, urllib.error

STUDIO_DEFAULT = "http://127.0.0.1:8888"
PORTAL         = "http://127.0.0.1:8099"
RESULT_DIR     = os.path.join("memory", "researcher", "hotload-results")
_THIS_DIR      = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT   = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))  # memory/researcher -> root
DEFAULT_AGENTS_JSON = os.path.join(PROJECT_ROOT, "agents.json")

# Goal #5 (Load-Trend Feed Integration): the SHARED load-trend feed. Latency-probe rows (no "kind")
# and per-host load EVENT rows (kind="load") both live in this one file; memory/ops/load_trend.py
# reads the latency rows for percentiles and SKIPS (but must PARSE) the kind="load" event rows, which
# are exactly the input Goal #6 (overnight-unload correlation) histograms over. Single file, two feeds.
BASELINE_FILE = os.path.join(PROJECT_ROOT, "memory", "ops", "load-baseline.jsonl")

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
        "ip": "IP_LAN", "studio": STUDIO_DEFAULT, "auth": None,
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

# Documented EVICTION ASYMMETRY (Goal #4). Directional edges: (loader, evicted) meaning
# "loading `loader` on this host pushes out a resident `evicted`". Source of truth:
# memory/llm/backend-swap-procedure.md (drill 11-15): White Q4_K_S @131k ctx evicts Q8_0; the
# reverse does NOT hold. Keep in lockstep with EVICTION handling in
# memory/orchestrator/model_scheduler.py (same asymmetry, explicit-UNLOAD policy).
EVICTION_EDGES = {
    "white": [("quinn-q4", "atlas-q8")],
}


def _evicted_by(host_key, load_name, resident_names):
    """Pure: which of `resident_names` does loading `load_name` push out (documented asymmetry)?"""
    ev = set()
    for (src, dst) in EVICTION_EDGES.get(host_key, []):
        if src == load_name and dst in resident_names:
            ev.add(dst)
    return ev


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


def restore_order(host_key, resident_before, target_set):
    """Goal #4: deterministic dual-residency restore that NEVER silently loses a wanted model.

      host_key:        HOSTS key
      resident_before: iterable of model names currently resident (authoritative /loaded-models)
      target_set:      iterable of model names we want resident afterwards (dual residency = both)
    Returns (order, log_lines, zero_loss):
      order      - list of (OP, name); OP in {UNLOAD, LOAD, RELOAD}, in execution order
      log_lines  - every residency change (eviction + restore) recorded here, never silent
      zero_loss  - True iff the final resident set == target_set (nothing wanted is left missing)
    Honors the documented Q4-evicts-Q8 asymmetry: if a LOAD would evict a model still in
    target_set, an explicit RELOAD of that model is appended AFTER it (preserve dual residency).
    If the evicted model is NOT in target_set, the eviction is ACCEPTED + LOGGED.
    """
    resident = set(resident_before)
    target = set(target_set)
    order = []
    log = []
    # 1) drop anything resident we do not want (log it - never silent)
    for name in sorted(resident - target):
        order.append(("UNLOAD", name))
        resident.discard(name)
        log.append(f"UNLOADED {name} (not in target set)")
    # 2) load each wanted-but-absent model; repair any still-wanted eviction it causes
    for name in sorted(target - resident):
        evicted = _evicted_by(host_key, name, resident)
        order.append(("LOAD", name))
        resident.add(name)
        for e in sorted(evicted):
            if e in target:
                log.append(f"EVICTED {e} by LOAD {name} (documented Q4-evicts-Q8 asymmetry)")
                order.append(("RELOAD", e))
                resident.add(e)  # restored
                log.append(f"RESTORED {e} after LOAD {name} -> dual residency preserved")
            else:
                resident.discard(e)
                log.append(f"EVICTION ACCEPTED for {e} (not in target set)")
    return order, log, (resident == target)


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
# EVICTION SELF-TEST (Goal #4, offline, NO network) - proves the restore rule.
# ---------------------------------------------------------------------------
def eviction_selftest():
    """The documented scenario: White Q8 was resident before a Q4 reload; we want dual residency
    back. Asserts zero binding loss + that the residency change is LOGGED (never silent)."""
    print("  [scenario] white: atlas-q8 resident, LOAD quinn-q4 (131k ctx) -> evicts q8")
    order, log, zero_loss = restore_order("white", ["atlas-q8"], {"atlas-q8", "quinn-q4"})
    print("    order =", order)
    for l in log:
        print("    log  :", l)

    ok1 = (zero_loss is True)
    print(f"  [{'PASS' if ok1 else 'FAIL'}] zero binding loss (final resident set == target set)")

    idx_load_q4 = next((i for i, (op, n) in enumerate(order) if op == "LOAD" and n == "quinn-q4"), None)
    idx_reload_q8 = next((i for i, (op, n) in enumerate(order) if op == "RELOAD" and n == "atlas-q8"), None)
    ok2 = (idx_load_q4 is not None and idx_reload_q8 is not None and idx_reload_q8 > idx_load_q4)
    print(f"  [{'PASS' if ok2 else 'FAIL'}] RELOAD atlas-q8 scheduled AFTER the evicting LOAD quinn-q4")

    joined = "\n".join(log).lower()
    ok3 = ("evicted atlas-q8" in joined) and ("restored atlas-q8" in joined)
    print(f"  [{'PASS' if ok3 else 'FAIL'}] residency change LOGGED (eviction + restore), never silent")

    # need-A-alone path: target={quinn-q4} only. The rule UNLOADs Q8 FIRST (doc rule #1) so the
    # Q4 load causes no eviction side-effect; either way Q8's departure must be LOGGED, never silent.
    order2, log2, zl2 = restore_order("white", ["atlas-q8"], {"quinn-q4"})
    joined2 = "\n".join(log2).lower()
    q8_departure_logged = ("atlas-q8" in joined2) and any(
        k in joined2 for k in ("unload", "evict", "accept"))
    ok4 = bool(zl2) and q8_departure_logged
    print(f"  [{'PASS' if ok4 else 'FAIL'}] need-A-alone: Q8 removal LOGGED + zero_loss={zl2} (order={[o for o,_ in order2]})")

    return ok1 and ok2 and ok3 and ok4


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
    # Goal #4: eviction-awareness. A White Q4 load evicts a resident Q8; our per-model snapshots
    # predate that side-effect, so RE-READ the authoritative resident set, diff vs wanted, and
    # explicitly RELOAD any wanted model now missing (never silently lose residency). Gated on the
    # live vantage like the rest of execute(); offline proof is --test-eviction.
    res_paths = get_resident_paths(jreq, host_key) or []
    final_resident = {m["name"] for m in HOSTS[host_key]["models"]
                      if any(m["model_path"].lower() in r for r in res_paths)}
    wanted_names = [m["name"] for m in HOSTS[host_key]["models"]]
    order, ev_log, zero_loss = restore_order(host_key, final_resident, wanted_names)
    for (op, name) in order:
        if op != "RELOAD":
            continue  # UNLOAD/LOAD were already handled in the main per-model loop
        m = [x for x in HOSTS[host_key]["models"] if x["name"] == name][0]
        entry = {"name": name, "action": "RESTORE", "ctx": m["max_seq_length"],
                 "restore_reason": ev_log}
        s, d, raw = jreq("POST", HOSTS[host_key]["studio"] + "/api/inference/load",
                         dict(m), t=900, auth=_auth_header(host_key))
        entry["load_ack_status"] = s
        resident_now = poll_resident(jreq, host_key, m["model_path"], timeout_s=420)
        entry["resident_after_poll"] = resident_now
        if resident_now:
            fp = run_probe(jreq, host_key, m["probe_alias"])
            entry["post_probe"] = fp
            entry["ok"] = bool(fp.get("ok"))
        else:
            entry["ok"] = False
        res["models"].append(entry)
    res["eviction_aware"] = {"log": ev_log, "zero_loss": zero_loss}
    res["verdict"] = "ALL_UP" if all(e.get("ok", e.get("skipped") is True) for e in res["models"]) else "PARTIAL"
    res["end"] = datetime.datetime.now().isoformat()
    # Goal #5: wall-clock time-to-resident (start->all-wanted-resident) for the load-trend feed.
    try:
        _t0 = datetime.datetime.fromisoformat(res["start"]); _t1 = datetime.datetime.fromisoformat(res["end"])
        res["time_to_resident_s"] = round((_t1 - _t0).total_seconds(), 1)
    except Exception:
        res["time_to_resident_s"] = 0.0
    # one result JSON per host
    os.makedirs(RESULT_DIR, exist_ok=True)
    out = os.path.join(RESULT_DIR, f"{host_key}_result.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    res["result_path"] = out
    # Goal #5: append this host's result to the shared load-trend feed (never let the feed break a live load).
    try:
        res["feed_row"] = record_load_result(res)
    except Exception as _e:
        res["feed_error"] = str(_e)
    return res


# ---------------------------------------------------------------------------
# BINDINGS (Goal #3) - read agents.json + per-host /api/settings/model-aliases ->
# the 8-agent match matrix. Promotes model-residency-study-2026-11-17 into a runnable
# check: an agent is a MISMATCH if its model_id is not a registered portal alias, OR its
# configured route host != the intended host for that alias.
#
# EXPECTED_ROUTING is the documented SSOT (memory/llm/hosts.md + residency study 11-17):
# which host each portal alias SHOULD resolve to. builder-q8 / verifier-q4 belong on Black.
# ---------------------------------------------------------------------------
EXPECTED_ROUTING = {
    "atlas-q8":     "white",
    "quinn-q4":     "white",
    "builder-q8":   "black",
    "verifier-q4":  "black",
    "designer-q4":  "pale",
    "archivist-q8": "pale",
    "scribe-q8":    "red",
    "mechanic-q4":  "red",
}


def _host_from_studio(studio_url):
    """Map an agent's 'studio' URL to a HOSTS key. None/empty/local => 'white' (the portal
    default routes local :8888). Remote IP matched against the HOSTS table."""
    if not studio_url or not str(studio_url).strip():
        return "white"
    m = re.search(r"//([0-9.]+)", str(studio_url))
    ip = m.group(1) if m else None
    if ip in (None, "127.0.0.1", "localhost"):
        return "white"
    for hk, h in HOSTS.items():
        if ip == h["ip"]:
            return hk
    return f"unknown:{ip}"


def fetch_host_aliases(jreq_fn, host_key, t=15):
    """GET /api/settings/model-aliases on one host. NEVER raises: returns (reachable, names).
    Unreachable host -> (False, None) so a full-outage run is not an exception."""
    try:
        s, d, raw = jreq_fn("GET", HOSTS[host_key]["studio"] + "/api/settings/model-aliases",
                            t=t, auth=_auth_header(host_key))
    except Exception:
        return False, None
    if s != 200 or not isinstance(d, (dict, list)):
        return False, None
    al = d.get("model_aliases") or d.get("aliases") if isinstance(d, dict) else d
    names = set()
    for x in (al or []):
        n = x.get("alias") if isinstance(x, dict) else x
        if isinstance(n, str):
            names.add(n)
    return True, names


def bindings_matrix(agents_json_path=DEFAULT_AGENTS_JSON, jreq_fn=None, live=False):
    """Emit the 8-agent match matrix. Pure/offline by default (live=False needs no network).
    With live=True + an injectable jreq_fn, also cross-checks alias registration per host.
    Never raises on a missing agents.json or an unreachable host."""
    try:
        with open(agents_json_path, encoding="utf-8") as f:
            agents = json.load(f)
    except Exception as e:
        return {"error": f"could not read {agents_json_path}: {e}"}
    agent_list = agents if isinstance(agents, list) else agents.get("agents", [])

    live_aliases = {}  # host_key -> {reachable, aliases:[...]} (only when live)
    if live and jreq_fn is not None:
        for hk in HOSTS:
            reachable, names = fetch_host_aliases(jreq_fn, hk)
            live_aliases[hk] = {"reachable": reachable, "aliases": sorted(names or [])}

    rows = []
    for a in agent_list:
        name = a.get("name") or a.get("id")
        mid = str(a.get("model_id") or "").strip()
        actual_host = _host_from_studio(a.get("studio"))
        intended_host = EXPECTED_ROUTING.get(mid)
        flags = []
        if mid not in EXPECTED_ROUTING:
            # model_id is a raw GGUF/model name (e.g. Qwen3.8-27B-Q8_0), not a portal alias
            flags.append("RAW_MODEL_NAME_NOT_ALIAS")
        elif actual_host != intended_host:
            flags.append(f"WRONG_HOST(actual={actual_host},intended={intended_host})")
        live_ok = None
        if live and intended_host in live_aliases:
            la = live_aliases[intended_host]
            if la["reachable"]:
                live_ok = mid in la["aliases"]
                if not live_ok:
                    flags.append("ALIAS_NOT_REGISTERED_ON_INTENDED_HOST")
        rows.append({"agent": name, "model_id": mid,
                     "actual_route_host": actual_host, "intended_host": intended_host,
                     "alias_registered_live": live_ok, "flags": flags, "match": not flags})
    return {"agents_total": len(rows),
            "matched": sum(1 for r in rows if r["match"]),
            "mismatches": [r for r in rows if not r["match"]],
            "live": live, "matrix": rows}


def bindings_selftest(agents_json_path=DEFAULT_AGENTS_JSON):
    """Offline self-test (Goal #3 acceptance): no network required.
      1) reproduces the KNOWN builder+verifier mismatch flags from agents.json;
      2) proves fetch_host_aliases NEVER raises on an unreachable host;
      3) confirms the full 8-agent matrix builds without error."""
    res = bindings_matrix(agents_json_path=agents_json_path, live=False)
    got_mm = sorted((r["agent"] or "").lower() for r in res.get("mismatches", []))
    expect_mm = ["builder", "verifier"]
    ok1 = got_mm == expect_mm
    print(f"  [{'PASS' if ok1 else 'FAIL'}] offline mismatches={got_mm} (expect {expect_mm})")

    def boom(method, url, *a, **k):
        raise OSError("simulated: port 8888 unreachable (WinError 10013)")
    ok2 = True
    try:
        reachable, names = fetch_host_aliases(boom, "white")
        ok2 = (reachable is False and names is None)
    except Exception as e:
        ok2 = False
        print(f"    raise-on-unreachable leaked: {e!r}")
    print(f"  [{'PASS' if ok2 else 'FAIL'}] unreachable host -> no raise, returns (False, None)")

    ok3 = ("error" not in res) and res.get("agents_total") == 8
    print(f"  [{'PASS' if ok3 else 'FAIL'}] matrix built agents_total={res.get('agents_total')} (expect 8), matched={res.get('matched')}")
    return ok1 and ok2 and ok3


# ---------------------------------------------------------------------------
# GOAL #5 - LOAD-TREND FEED INTEGRATION (offline-provable; no :8888 vantage needed).
# record_load_result() appends each execute() result as ONE kind='load' line to the shared feed;
# load_trend.load_days() is tolerant of these rows (parses them, excludes them from the latency
# percentile trend) so a full-outage run records one honest event row and never emits garbage stats.
# ---------------------------------------------------------------------------
def record_load_result(res, baseline_path=BASELINE_FILE):
    """Append this host's execute() result as ONE kind='load' line to the shared load-trend feed."""
    ts = res.get("end") or datetime.datetime.now().isoformat()
    models = res.get("models", []) or []
    ok = sum(1 for e in models if e.get("ok"))
    skip = sum(1 for e in models if e.get("skipped"))
    total = len(models)
    row = {"kind": "load", "ts": ts, "host": res.get("host"), "verdict": res.get("verdict"),
           "time_to_resident_s": res.get("time_to_resident_s", 0.0),
           "models_total": total, "models_ok": ok, "models_skipped": skip,
           "models_failed": max(0, total - ok - skip)}
    os.makedirs(os.path.dirname(baseline_path), exist_ok=True)
    with open(baseline_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    return row


def feed_selftest(baseline_path=BASELINE_FILE):
    """Goal #5 acceptance (offline): append ONE synthetic kind='load' event row to the shared feed,
    prove memory/ops/load_trend.py's read path PARSES it without error and EXCLUDES it from the
    latency percentile trend, and re-prove the all-error guard still skips a 100%-fail latency row.
    Returns True on PASS. Idempotent (won't double-append the fixture); guard checked on a temp copy."""
    import importlib.util, tempfile
    already = False
    if os.path.exists(baseline_path):
        with open(baseline_path, encoding="utf-8") as f:
            already = any("__feed_selftest__" in ln for ln in f)
    fixture = {"kind": "load", "ts": datetime.datetime.now().isoformat(), "host": "__feed_selftest__",
               "verdict": "ALL_UP", "time_to_resident_s": 12.3,
               "models_total": 2, "models_ok": 2, "models_skipped": 0, "models_failed": 0}
    if not already:
        os.makedirs(os.path.dirname(baseline_path), exist_ok=True)
        with open(baseline_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(fixture) + "\n")
    lt_path = os.path.join(PROJECT_ROOT, "memory", "ops", "load_trend.py")
    spec = importlib.util.spec_from_file_location("load_trend_under_test", lt_path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    prev = os.getcwd()
    try:
        os.chdir(PROJECT_ROOT)          # load_trend resolves BASELINE_FILE relative to CWD
        days = mod.load_days()          # must NOT raise on the kind='load' row
    finally:
        os.chdir(prev)
    assert all(d.get("host") != "__feed_selftest__" for d in days), \
        "kind='load' event row leaked into the latency percentile trend"
    # All-error guard proven against a TEMP copy so no junk accumulates in the real feed.
    tmp = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, dir=os.path.dirname(baseline_path))
    with open(baseline_path, encoding="utf-8") as src:
        tmp.write(src.read())
    allerr = {"ts": datetime.datetime.now().isoformat(), "levels": [
        {"concurrency": 1, "n": 3, "p50_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0, "errors": 3}]}
    tmp.write(json.dumps(allerr) + "\n"); tmp.close()
    saved = mod.BASELINE_FILE
    try:
        mod.BASELINE_FILE = tmp.name
        days2 = mod.load_days()
    finally:
        mod.BASELINE_FILE = saved
        os.remove(tmp.name)
    assert len(days2) == len(days), "all-error latency row was not skipped by the guard"
    print(f"  feed: kind='load' host={fixture['host']} ttr={fixture['time_to_resident_s']}s appended; "
          f"load_trend parsed {len(days)} latency day(s); fixture excluded from trend; all-error guard OK")
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="Unified host-aware LLM hot-loader")
    ap.add_argument("--plan", metavar="HOST", help="dry-run: print host table + load bodies (no network)")
    ap.add_argument("--test-wedge", action="store_true", help="offline wedge-skip self-test (no network)")
    ap.add_argument("--host", help="target host for --execute")
    ap.add_argument("--execute", action="store_true", help="live execute (needs :8888 vantage)")
    ap.add_argument("--bindings", action="store_true", help="emit agents.json binding match matrix (offline; add --live for alias cross-check)")
    ap.add_argument("--live", action="store_true", help="with --bindings: also GET /api/settings/model-aliases per host")
    ap.add_argument("--test-bindings", action="store_true", help="offline self-test of the binding matrix (no network)")
    ap.add_argument("--test-eviction", action="store_true", help="offline self-test of the eviction-awareness rule (Goal #4, no network)")
    ap.add_argument("--test-feed", action="store_true", help="offline self-test of the load-trend feed integration (Goal #5): append one synthetic kind='load' row + prove load_trend parses it (no network)")
    args = ap.parse_args(argv)

    if args.plan:
        print(render_plan(args.plan))
        return 0
    if args.test_wedge:
        ok = wedge_selftest()
        print("WEDGE SELFTEST:", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    if args.test_bindings:
        ok = bindings_selftest()
        print("BINDINGS SELFTEST:", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    if args.test_eviction:
        ok = eviction_selftest()
        print("EVICTION SELFTEST:", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    if args.test_feed:
        ok = feed_selftest()
        print("FEED SELFTEST:", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    if args.bindings:
        res = bindings_matrix(jreq_fn=jreq, live=args.live)
        print(json.dumps(res, indent=1))
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
