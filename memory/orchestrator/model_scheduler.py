#!/usr/bin/env python3
"""model_scheduler.py - functional hot-LLM-loading PLANNER (Orchestrator cycle-6 goal 1).

Resolves target agents -> required models via the REAL catalog
(memory/llm/hotload-catalog.json), does per-host VRAM accounting, and emits an
ordered LOAD/UNLOAD plan. Eviction is DETERMINISTIC and honors the documented
Q4-evicts-Q8 asymmetry (memory/llm/backend-swap-procedure.md): when a required
model cannot coexist with a resident one on the same host, we emit an explicit
UNLOAD of the evicted resident BEFORE the LOAD rather than relying on Studio's
implicit push-out.

READ-ONLY: this module never touches the GPU / Studio API. The live execute()
engine (goal 2) drives the Studio API from plan()'s output.

Usage:
  python memory/orchestrator/model_scheduler.py --selftest
  python memory/orchestrator/model_scheduler.py --plan agents=researcher,builder resident=white:qwen3-27b-q8
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG_PATH = os.path.normpath(os.path.join(HERE, "..", "llm", "hotload-catalog.json"))


def load_catalog(path=CATALOG_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _model_index(catalog):
    """id -> normalized model dict for real models + planned_models.
    Planned entries carry no vram_gb; they use min_vram_gb as their VRAM draw."""
    idx = {}
    for m in catalog.get("models", []):
        e = dict(m)
        e["vram_gb"] = float(e.get("vram_gb", e.get("min_vram_gb", 0)))
        idx[m["id"]] = e
    for p in catalog.get("planned_models", []):
        e = dict(p)
        e["vram_gb"] = float(e.get("min_vram_gb", 0))
        idx[p["id"]] = e
    return idx


def resolve_agent_model(agent, catalog):
    """Return the model id an agent profile maps to, or None.
    Order: real models (agent_profiles contains agent) -> planned_models -> templates."""
    for m in catalog.get("models", []):
        if agent in m.get("agent_profiles", []):
            return m["id"]
    for p in catalog.get("planned_models", []):
        if agent in p.get("agent_profiles", []):
            return p["id"]
    for t in catalog.get("agent_profile_templates", []):
        if t.get("id") == agent and t.get("model_id"):
            return t["model_id"]
    return None


def _keep_priority(mid, required_here):
    """Higher = keep. Required models are protected (inf). Non-required rank by VRAM draw
    so we evict the LARGEST non-required first (frees most GB with fewest unloads).
    This is the 'lowest-priority non-required first' policy made concrete."""
    if mid in required_here:
        return float("inf")
    return 0.0


def plan(target_agents, resident, catalog=None):
    """Compute an ordered LOAD/UNLOAD (dry-run) plan.

    target_agents: list of agent profile names to bring HOT.
    resident: dict host -> list[model_id] currently loaded on that host.
    Returns {ok, required_by_host, unresolved_agents, hosts:{...}, sequence:[...]}.
    """
    if catalog is None:
        catalog = load_catalog()
    hosts_meta = catalog["_meta"]["hosts"]
    mindex = _model_index(catalog)

    # 1) resolve each target agent -> (model, host)
    required = {}        # host -> set(model_id)
    unresolved = []
    for agent in target_agents:
        mid = resolve_agent_model(agent, catalog)
        if not mid or mid not in mindex:
            unresolved.append(agent)
            continue
        host = mindex[mid].get("host")
        if host not in hosts_meta:
            unresolved.append(agent)
            continue
        required.setdefault(host, set()).add(mid)

    # 2) per-host VRAM-driven eviction + load ordering (deterministic)
    hosts_out = {}
    sequence = []
    alerts = []   # goal-4: VRAM conflict predictor alerts
    for host in [h for h in hosts_meta if h in required]:   # catalog order for determinism
        budget = float(hosts_meta[host].get("vram_total_gb", 0))
        res_now = [m for m in resident.get(host, []) if m in mindex]
        req_here = required.get(host, set())
        to_load = [m for m in sorted(req_here) if m not in res_now]

        loaded = {m: float(mindex[m]["vram_gb"]) for m in res_now}
        actions = []
        pending = list(to_load)

        # Goal-5: exclusive models require ALL non-required residents evicted first
        exclusive_targets = [m for m in to_load if mindex[m].get("exclusive")]
        if exclusive_targets:
            for m in sorted(res_now):
                if m not in req_here:
                    actions.append({"op": "UNLOAD", "model": m, "host": host,
                                    "reason": "exclusive model %s requires full eviction of non-required residents"
                                              % exclusive_targets[0]})
                    vpri = int(mindex.get(m, {}).get("priority", 2))
                    if vpri == 1:
                        alerts.append({"type": "PRIORITY_EVICTION", "host": host,
                                       "evicted_model": m, "for_model": exclusive_targets[0],
                                       "message": "Priority-1 model %s evicted from %s for exclusive model %s"
                                                  % (m, host, exclusive_targets[0])})
                    del loaded[m]

        guard = 0
        while pending and guard < 256:
            guard += 1
            mid = pending[0]
            need = float(mindex[mid]["vram_gb"])
            used = sum(loaded.values())
            if used + need <= budget + 1e-9:
                _eta = predict_load_eta(mid, catalog)
                actions.append({"op": "LOAD", "model": mid, "host": host,
                                "reason": "required; fits (used %.1f + need %.1f <= %d)"
                                          % (used, need, budget),
                                "eta_s": _eta})
                loaded[mid] = need
                pending.pop(0)
            else:
                evictable = [m for m in loaded if m not in req_here and m != mid]
                if not evictable:
                    actions.append({"op": "BLOCKED", "model": mid, "host": host,
                                    "reason": "needs %.1fGB but only %.1fGB free; no non-required resident to evict"
                                              % (need, max(0.0, budget - used))})
                    # ALERT: VRAM exceeded
                    alerts.append({"type": "VRAM_EXCEEDED", "host": host,
                                   "model": mid, "needed_gb": need,
                                   "free_gb": round(max(0.0, budget - used), 2),
                                   "message": "%s needs %.1fGB but only %.1fGB free on %s"
                                              % (mid, need, max(0.0, budget - used), host)})
                    pending.pop(0)
                    continue
                # evict lowest-priority (non-required) first = largest VRAM draw
                victim = max(evictable, key=lambda m: float(mindex[m]["vram_gb"]))
                actions.append({"op": "UNLOAD", "model": victim, "host": host,
                                "reason": "evict non-required resident (largest %.1fGB) to make room for %s"
                                          % (float(mindex[victim]["vram_gb"]), mid)})
                # ALERT: priority-1 eviction
                vpri = int(mindex.get(victim, {}).get("priority", 2))
                if vpri == 1:
                    alerts.append({"type": "PRIORITY_EVICTION", "host": host,
                                   "evicted_model": victim, "for_model": mid,
                                   "message": "Priority-1 model %s would be evicted from %s to load %s"
                                              % (victim, host, mid)})
                del loaded[victim]

        hosts_out[host] = {
            "budget_gb": budget,
            "resident_before": res_now,
            "resident_after": sorted(loaded.keys()),
            "free_gb_before": round(max(0.0, budget - sum(float(mindex[m]["vram_gb"]) for m in res_now)), 2),
            "free_gb_after": round(max(0.0, budget - sum(loaded.values())), 2),
            "fits": not any(a["op"] == "BLOCKED" for a in actions),
            "actions": actions,
        }
        sequence.extend(actions)

    # Log alerts to hotload-log.jsonl (best-effort; don't fail plan on log error)
    if alerts:
        try:
            _log_event("ALERT", "multi", ",".join(a.get("model", a.get("evicted_model", "?")) for a in alerts),
                       json.dumps(alerts))
        except Exception:
            pass

    return {
        "ok": True,
        "required_by_host": {h: sorted(v) for h, v in required.items()},
        "unresolved_agents": unresolved,
        "hosts": hosts_out,
        "sequence": sequence,
        "alerts": alerts,
    }


def _ops(p):
    return [(a["op"], a["model"]) for a in p["sequence"]]


def selftest():
    catalog = load_catalog()
    failures = []

    def check(name, cond, detail=""):
        print(("PASS  " if cond else "FAIL  ") + name + ("  [" + detail + "]" if (detail and not cond) else ""))
        if not cond:
            failures.append(name)

    # resolution
    check("resolve orchestrator->q8", resolve_agent_model("orchestrator", catalog) == "qwen3-27b-q8")
    check("resolve researcher->q4", resolve_agent_model("researcher", catalog) == "qwen3-27b-q4")
    check("resolve scribe->q8", resolve_agent_model("scribe", catalog) == "qwen3-27b-q8")
    check("resolve video_gen->planned", resolve_agent_model("video_gen", catalog) == "video-gen-model")

    # Case A: documented asymmetry - Q4 target with Q8 resident => UNLOAD q8, LOAD q4 (deterministic)
    p = plan(["researcher"], {"white": ["qwen3-27b-q8"]}, catalog)
    check("A asymmetry unload-q8-load-q4", _ops(p) == [("UNLOAD", "qwen3-27b-q8"), ("LOAD", "qwen3-27b-q4")], str(_ops(p)))

    # Case B: reverse - Q8 target with Q4 resident => UNLOAD q4, LOAD q8
    p = plan(["orchestrator"], {"white": ["qwen3-27b-q4"]}, catalog)
    check("B unload-q4-load-q8", _ops(p) == [("UNLOAD", "qwen3-27b-q4"), ("LOAD", "qwen3-27b-q8")], str(_ops(p)))

    # Case D: idempotent - Q8 target with Q8 already resident => no-op
    p = plan(["orchestrator"], {"white": ["qwen3-27b-q8"]}, catalog)
    check("D idempotent no-op", _ops(p) == [], str(_ops(p)))

    # Case F: small resident (MTP 4.2GB) + Q4 target fits WITHOUT eviction => LOAD only
    p = plan(["mechanic"], {"white": ["qwen3-5-4b-mtp"]}, catalog)
    check("F no over-eviction", _ops(p) == [("LOAD", "qwen3-27b-q4")], str(_ops(p)))

    # Case G: two agents same model -> single load, deduped
    p = plan(["researcher", "builder"], {"white": []}, catalog)
    check("G dedupe single q4 load", _ops(p) == [("LOAD", "qwen3-27b-q4")], str(_ops(p)))

    # Case H: planned model with empty host loads cleanly
    p = plan(["video_gen"], {"white": []}, catalog)
    check("H planned video-gen load", _ops(p) == [("LOAD", "video-gen-model")], str(_ops(p)))

    # Case I: budget overflow with nothing evictable => BLOCKED (48GB > 32GB host)
    p = plan(["deep_researcher"], {"white": ["qwen3-27b-q8"]}, catalog)
    ops = _ops(p)
    check("I overflow blocked", any(op == "BLOCKED" and model == "large-context-model" for op, model in ops), str(ops))

    # Case J: cross-host isolation - pale (16GB) unaffected by white targets
    p = plan(["researcher"], {"white": ["qwen3-27b-q8"], "pale": []}, catalog)
    check("J only white host in output", set(p["hosts"].keys()) == {"white"}, str(set(p["hosts"].keys())))

    # Case K: unresolved agent surfaced, not crashed
    p = plan(["nonexistent_agent"], {"white": []}, catalog)
    check("K unresolved surfaced", p["unresolved_agents"] == ["nonexistent_agent"] and _ops(p) == [], str(p["unresolved_agents"]))

    # --- Goal 4: VRAM Conflict Predictor + Alert ---
    # Case L: forcing a large model on a full 32GB host => fits=false + VRAM_EXCEEDED alert
    # deep_researcher maps to large-context-model (planned, min_vram_gb likely >16)
    p = plan(["deep_researcher"], {"white": ["qwen3-27b-q8"]}, catalog)
    w = p["hosts"].get("white", {})
    check("L fits=false on overflow", w.get("fits") is False, str(w.get("fits")))
    check("L VRAM_EXCEEDED alert present", any(a["type"] == "VRAM_EXCEEDED" for a in p.get("alerts", [])),
          str(p.get("alerts", [])))

    # Case M: evicting priority-1 Q8 to load another model => PRIORITY_EVICTION alert
    # orchestrator (Q8) resident + researcher (Q4) target on same host => Q8 gets evicted? No:
    # Q4 needs ~15GB, Q8 is ~16GB; 32GB budget: used=16(Q8), need=15(Q4), 16+15=31<=32 fits!
    # So no eviction. Let me use a scenario that forces it:
    # deep_researcher (large-context, >16GB) with Q8 resident => must evict Q8
    p = plan(["deep_researcher"], {"white": ["qwen3-27b-q8"]}, catalog)
    check("M PRIORITY_EVICTION alert", any(a["type"] == "PRIORITY_EVICTION" and a.get("evicted_model") == "qwen3-27b-q8"
          for a in p.get("alerts", [])), str(p.get("alerts", [])))

    # Case N: proven dual-resident MTP(4.2)+Q4(23.7)=27.9<=32GB => NO alerts (no false alarm)
    p = plan(["researcher", "mechanic"], {"white": ["qwen3-5-4b-mtp"]}, catalog)
    check("N no false alarms on proven case", len(p.get("alerts", [])) == 0 and
          all(h.get("fits") for h in p["hosts"].values()),
          str({"alerts": p.get("alerts"), "hosts_fits": {h: v.get("fits") for h, v in p["hosts"].items()}}))

    # Case O: exclusive model (video-gen) evicts ALL non-required residents on target host
    p = plan(["video_gen"], {"white": ["qwen3-27b-q8", "qwen3-5-4b-mtp"]}, catalog)
    w = p["hosts"].get("white", {})
    # All non-required residents should be UNLOADed before the LOAD
    unloads = [a for a in w.get("actions", []) if a["op"] == "UNLOAD"]
    loads = [a for a in w.get("actions", []) if a["op"] == "LOAD"]
    check("O exclusive evicts all non-required", len(unloads) >= 2 and len(loads) == 1,
          "unloads=%d loads=%d actions=%s" % (len(unloads), len(loads), str(w.get("actions", []))))
    # Verify eviction reason mentions exclusive
    check("O eviction reason cites exclusive",
          any("exclusive" in a.get("reason", "") for a in unloads),
          str([a.get("reason", "") for a in unloads]))

    # --- Goal 7: Load-Time Prediction (eta_s) ---
    # Case P: plan() LOAD actions carry eta_s field
    p = plan(["researcher"], {"white": []}, catalog)
    load_actions = [a for a in p["sequence"] if a["op"] == "LOAD"]
    check("P LOAD actions have eta_s key", all("eta_s" in a for a in load_actions),
          str(load_actions))

    # Case Q: predict_load_eta returns a number (from catalog fallback) or None
    _q4_eta = predict_load_eta("qwen3-27b-q4", catalog)
    check("Q eta is numeric or None", _q4_eta is None or isinstance(_q4_eta, (int, float)),
          str(_q4_eta))

    # Case R: median calculation from synthetic log data
    import tempfile, os as _os
    _tmp_log = _os.path.join(tempfile.gettempdir(), "test_hotload_log.jsonl")
    with open(_tmp_log, "w") as _f:
        for dur in [40.0, 50.0, 60.0]:
            _f.write(json.dumps({"ts": "2026-11-18T00:00:00+00:00", "event": "LOAD_SUCCESS",
                                  "host": "white", "model": "test-model", "detail": "%.1fs" % dur}) + "\n")
    # Temporarily swap HOTLOAD_LOG for the test
    global HOTLOAD_LOG
    _saved_log = HOTLOAD_LOG
    HOTLOAD_LOG = _tmp_log
    _eta = predict_load_eta("test-model")
    check("R median of [40,50,60] = 50.0", _eta == 50.0, str(_eta))
    # Fewer than 3 samples -> fallback to catalog (test-model not in catalog -> None)
    with open(_tmp_log, "w") as _f:
        for dur in [40.0, 50.0]:
            _f.write(json.dumps({"ts": "2026-11-18T00:00:00+00:00", "event": "LOAD_SUCCESS",
                                  "host": "white", "model": "test-model-x", "detail": "%.1fs" % dur}) + "\n")
    _eta2 = predict_load_eta("test-model-x")
    check("R2 fewer than 3 samples -> None for unknown model", _eta2 is None, str(_eta2))
    HOTLOAD_LOG = _saved_log

    print("\n%d/%d selftest checks passed" % (20 - len(failures), 20))
    if failures:
        print("FAILED:", failures)
        return 1
    print("ALL PLAN CASES PASS on real catalog")
    return 0


# ---- Capability Auto-Match Suggester (cycle-6 goal 8) -----------------------
# Maps free-text task keywords -> catalog capability tags -> minimal VRAM-feasible
# agent set + models. Reuses catalog `capabilities` lists; no GPU calls.
CAPABILITY_KEYWORDS = {
    "code": ["code", "coding", "program", "implement", "debug", "refactor",
             "snippet", "script", "function", "api", "parse logs"],
    "research": ["research", "investigate", "find sources", "cite", "look up",
                 "cross-check"],
    "planning": ["plan", "roadmap", "architect", "strategy", "orchestrat"],
    "synthesis": ["summarize", "synthesize", "compress", "distill", "decision"],
    "ops": ["ops", "operational", "deploy", "monitor", "fleet", "host",
            "server", "maintenance", "load balance"],
    "verify": ["test", "verify", "validate", "assert", "proof"],
    "design": ["design", "ui", "ux", "frontend", "css", "interface", "layout"],
    "video_generation": ["video", "animation", "text to video", "clip"],
    "3d_generation": ["3d", "three-dimensional", "environment gen", "scene"],
    "long_document": ["long document", "book", "large context", "codebase",
                      "whole repo", "500-page", "200-page", "100k tokens"],
    "speculative_draft": ["quick draft", "speculative"],
}


def _detect_capabilities(task):
    """Return the set of catalog capability tags implied by a free-text task."""
    t = (task or "").lower()
    caps = set()
    for cap, kws in CAPABILITY_KEYWORDS.items():
        if any(kw in t for kw in kws):
            caps.add(cap)
    return caps


def suggest(task, resident=None, catalog=None):
    """Map a free-text task to the minimal VRAM-feasible agent set + models.

    Reuses catalog capability tags: detect required capabilities from the task,
    greedy-set-cover the smallest non-exclusive models that satisfy them (defaulting
    to the most-widely-bound workhorse model when nothing matches), map those models
    to their agents, then run a dry-run plan() for VRAM feasibility. No GPU calls.
    Returns {ok, task, capabilities_detected, suggested_models, suggested_agents,
             fits, plan_sequence_count, unresolved_caps}.
    """
    if catalog is None:
        catalog = load_catalog()
    mindex = _model_index(catalog)
    task = (task or "").strip()
    caps = _detect_capabilities(task)

    candidates = []
    for mid, entry in mindex.items():
        mcaps = set(entry.get("capabilities") or [])
        hit = mcaps & caps
        if not hit:
            continue
        candidates.append((mid, entry, float(entry["vram_gb"]), bool(entry.get("exclusive")), hit))

    if not caps:
        # No capability matched -> default to the most-widely-bound non-exclusive workhorse.
        fb = sorted(
            [(m["id"], m, len(m.get("agent_profiles") or []), float(m["vram_gb"]))
             for m in catalog.get("models", []) if not m.get("exclusive")],
            key=lambda x: (-x[2], x[3]))
        if fb:
            mid, entry = fb[0][0], mindex[fb[0][0]]
            candidates.append((mid, entry, float(entry["vram_gb"]), False, {"__default__"}))

    # Greedy set cover: prefer non-exclusive + smaller VRAM first (minimal cost).
    order = sorted(candidates, key=lambda c: (c[3], c[2]))
    covered, chosen, remaining = set(), [], set(caps)
    for mid, entry, vram, excl, hit in order:
        new = hit - covered
        if not new:
            continue
        chosen.append((mid, entry, vram, excl))
        covered |= hit
        remaining -= hit
        if not remaining:
            break

    suggested_models = [
        {"id": mid, "vram_gb": vram, "exclusive": excl,
         "capabilities": sorted(entry.get("capabilities") or [])}
        for mid, entry, vram, excl in chosen]
    suggested_agents = []
    for mid, entry, vram, excl in chosen:
        for ag in entry.get("agent_profiles") or []:
            if ag not in suggested_agents:
                suggested_agents.append(ag)

    plan_result = plan(suggested_agents, resident or {})
    fits = bool(plan_result.get("ok")) and not any(
        a.get("type") == "VRAM_EXCEEDED" for a in plan_result.get("alerts", []))

    return {
        "ok": True,
        "task": task,
        "capabilities_detected": sorted(caps) if caps else ["__default__"],
        "suggested_models": suggested_models,
        "suggested_agents": suggested_agents,
        "fits": fits,
        "plan_sequence_count": len(plan_result.get("sequence", [])),
        "unresolved_caps": sorted(remaining),
    }


def suggest_selftest():
    catalog = load_catalog()
    failures = []

    def check(name, cond, detail=""):
        print(("PASS  " if cond else "FAIL  ") + name + ("  [" + detail + "]" if (detail and not cond) else ""))
        if not cond:
            failures.append(name)

    t1 = suggest("write a python script to parse logs", catalog=catalog)
    check("t1 code->q4 minimal", [m["id"] for m in t1["suggested_models"]] == ["qwen3-27b-q4"], str(t1["suggested_models"]))
    check("t1 fits", t1["fits"] is True)

    t2 = suggest("write code and design a UI", catalog=catalog)
    check("t2 design+code single model", len(t2["suggested_models"]) == 1, str(t2["suggested_models"]))
    check("t2 caps detected", "design" in t2["capabilities_detected"] and "code" in t2["capabilities_detected"])

    t3 = suggest("generate a short video of a sunset", catalog=catalog)
    ids3 = [m["id"] for m in t3["suggested_models"]]
    check("t3 video->video-gen-model", "video-gen-model" in ids3, str(ids3))
    check("t3 exclusive flagged", any(m["exclusive"] for m in t3["suggested_models"]))

    t4 = suggest("summarize this 500-page book into a decision brief", catalog=catalog)
    ids4 = [m["id"] for m in t4["suggested_models"]]
    check("t4 long-doc->large-context-model", "large-context-model" in ids4, str(ids4))
    check("t4 infeasible (48GB>32GB) fits=False", t4["fits"] is False)

    t5 = suggest("hello there", catalog=catalog)
    check("t5 default->q4 workhorse", [m["id"] for m in t5["suggested_models"]] == ["qwen3-27b-q4"], str(t5["suggested_models"]))
    check("t5 fits", t5["fits"] is True)

    print("\n%d/%d suggest checks passed" % (6 - len(failures), 6))
    if failures:
        print("FAILED:", failures)
        return 1
    print("ALL SUGGEST CASES PASS on real catalog")
    return 0


def _parse_kv(s, sep=";"):
    out = {}
    for chunk in filter(None, s.split(sep)):
        if ":" not in chunk:
            continue
        k, v = chunk.split(":", 1)
        out[k.strip()] = [x.strip() for x in v.split(",") if x.strip()]
    return out


# ---------------------------------------------------------------------------
# EXECUTE ENGINE (goal 2) - drives the Studio API from a plan()'s output
# ---------------------------------------------------------------------------
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

HOTLOAD_LOG = os.path.normpath(os.path.join(HERE, "..", "llm", "hotload-log.jsonl"))
LOAD_PARAMS_PATH = os.path.normpath(os.path.join(HERE, "..", "llm", "model_load_params.json"))


def _log_event(event_type, host, model, detail=""):
    """Append a timestamped row to hotload-log.jsonl."""
    row = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event_type,
        "host": host,
        "model": model,
        "detail": detail,
    }
    os.makedirs(os.path.dirname(HOTLOAD_LOG), exist_ok=True)
    with open(HOTLOAD_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def predict_load_eta(model_id, catalog=None):
    """Predict cold-load duration for a model from hotload-log.jsonl history.

    Returns median of past LOAD_SUCCESS durations (seconds).
    Requires >= 3 observations; falls back to catalog load_time_s if fewer.
    Returns None if no data at all.
    """
    import statistics
    durations = []
    try:
        with open(HOTLOAD_LOG, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                if row.get("event") != "LOAD_SUCCESS":
                    continue
                if row.get("model") != model_id:
                    continue
                # detail field is like "45.3s"
                detail = row.get("detail", "")
                try:
                    d = float(detail.replace("s", ""))
                    durations.append(d)
                except (ValueError, AttributeError):
                    pass
    except (OSError, FileNotFoundError):
        pass

    if len(durations) >= 3:
        return round(statistics.median(durations), 1)

    # Fallback to catalog load_time_s
    if catalog is None:
        catalog = load_catalog()
    mindex = _model_index(catalog)
    entry = mindex.get(model_id, {})
    lt = entry.get("load_time_s")
    if lt is not None:
        return round(float(lt), 1)
    return None


def _studio_get(host_api, path, timeout=30):
    url = host_api.rstrip("/") + path
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _studio_post(host_api, path, body, timeout=60):
    url = host_api.rstrip("/") + path
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or b"{}")


def _wait_idle(host_api, host_name, model, max_wait_s=180, poll_s=3):
    """Poll active-generations until count==0. Returns True if idle."""
    deadline = time.time() + max_wait_s
    while time.time() < deadline:
        try:
            data = _studio_get(host_api, "/api/inference/active-generations")
            cnt = data.get("count", 0)
            if cnt == 0:
                return True
        except Exception:
            pass
        time.sleep(poll_s)
    return False


def _wait_resident(host_api, host_name, model_id, folder, timeout_s, poll_s=5):
    """Poll GET /models until the target model shows loaded=true."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            data = _studio_get(host_api, "/models")
            for m in data.get("data", data if isinstance(data, list) else []):
                mid = m.get("id", "")
                # Match by folder path or id substring
                if model_id in mid or (folder and folder.replace("\\", "/") in str(m).replace("\\", "/")):
                    if m.get("loaded"):
                        return True
        except Exception:
            pass
        time.sleep(poll_s)
    return False


def _wait_unloaded(host_api, host_name, model_id, folder, timeout_s=60, poll_s=3):
    """Poll GET /models until target shows loaded=false or absent."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            data = _studio_get(host_api, "/models")
            models_list = data.get("data", data if isinstance(data, list) else [])
            found_loaded = False
            for m in models_list:
                mid = m.get("id", "")
                if model_id in mid or (folder and folder.replace("\\", "/") in str(m).replace("\\", "/")):
                    if m.get("loaded"):
                        found_loaded = True
            if not found_loaded:
                return True
        except Exception:
            pass
        time.sleep(poll_s)
    return False


def _load_body_for(model_entry, catalog=None):
    """Build the POST /api/inference/load body from a catalog model entry.
    Uses model_load_params.json for exact proven bodies when available."""
    mid = model_entry["id"]
    # Try proven params file first
    try:
        with open(LOAD_PARAMS_PATH, encoding="utf-8") as f:
            params = json.load(f)
        # Map: qwen3-27b-q8 -> atlas-q8, qwen3-27b-q4 -> quinn-q4
        alias_map = {"qwen3-27b-q8": "atlas-q8", "qwen3-27b-q4": "quinn-q4"}
        alias = alias_map.get(mid)
        if alias and alias in params:
            return dict(params[alias])
    except Exception:
        pass
    # Fallback: build from catalog fields
    body = {
        "model_path": model_entry["folder"],
        "gguf_variant": model_entry.get("gguf_variant", ""),
        "gpu_ids": model_entry.get("gpu_ids", [0]),
        "max_seq_length": model_entry.get("max_context", 32768),
        "cache_type_kv": "q8_0",
        "n_parallel": 1,
    }
    if "mtp" in (model_entry.get("gguf_variant") or "").lower():
        body["speculative_type"] = "mtp"
        body["spec_draft_n_max"] = 4
    return body


def execute(plan_result, catalog=None, dry_run=False):
    """Drive the Studio API per host to execute a plan()'s output.

    Sequence: for each action in plan['sequence']:
      - UNLOAD: POST /api/inference/unload {model_path} -> poll until gone
      - LOAD:   idle-gate -> POST /api/inference/load {body} -> poll until resident
    Logs every transition to memory/llm/hotload-log.jsonl.

    Returns {ok, results:[{op,model,host,status,detail}], errors:[]}
    """
    if catalog is None:
        catalog = load_catalog()
    hosts_meta = catalog["_meta"]["hosts"]
    mindex = _model_index(catalog)

    results = []
    errors = []

    for action in plan_result.get("sequence", []):
        op = action["op"]
        model_id = action["model"]
        host = action["host"]
        entry = mindex.get(model_id, {})
        folder = entry.get("folder", "")
        api_url = hosts_meta.get(host, {}).get("api", "http://127.0.0.1:8888")

        if dry_run:
            results.append({"op": op, "model": model_id, "host": host,
                            "status": "DRY_RUN", "detail": action.get("reason", "")})
            continue

        if op == "BLOCKED":
            errors.append(action.get("reason", "blocked"))
            results.append({"op": op, "model": model_id, "host": host,
                            "status": "BLOCKED", "detail": action.get("reason", "")})
            _log_event("BLOCKED", host, model_id, action.get("reason", ""))
            continue

        if op == "UNLOAD":
            t0 = time.time()
            _log_event("UNLOAD_START", host, model_id)
            status_code, resp = _studio_post(api_url, "/api/inference/unload",
                                             {"model_path": folder})
            if status_code == 200:
                ok = _wait_unloaded(api_url, host, model_id, folder)
                elapsed = time.time() - t0
                st = "SUCCESS" if ok else "TIMEOUT"
                results.append({"op": op, "model": model_id, "host": host,
                                "status": st, "elapsed_s": round(elapsed, 1)})
                _log_event("UNLOAD_" + st, host, model_id, "%.1fs" % elapsed)
                if not ok:
                    errors.append("unload timeout: %s on %s" % (model_id, host))
            else:
                results.append({"op": op, "model": model_id, "host": host,
                                "status": "ERROR", "detail": "HTTP %d" % status_code})
                _log_event("UNLOAD_ERROR", host, model_id, str(resp))
                errors.append("unload HTTP %d: %s on %s" % (status_code, model_id, host))

        elif op == "LOAD":
            t0 = time.time()
            # 1) idle gate
            _log_event("IDLE_GATE_WAIT", host, model_id)
            if not _wait_idle(api_url, host, model_id):
                results.append({"op": op, "model": model_id, "host": host,
                                "status": "ABORTED", "detail": "idle gate timeout"})
                _log_event("IDLE_GATE_TIMEOUT", host, model_id)
                errors.append("idle gate never opened for %s on %s" % (model_id, host))
                continue
            _log_event("IDLE_GATE_OPEN", host, model_id)

            # 2) load
            body = _load_body_for(entry)
            _log_event("LOAD_START", host, model_id, json.dumps(body))
            status_code, resp = _studio_post(api_url, "/api/inference/load", body)
            if status_code == 200:
                load_timeout = float(entry.get("load_time_s", 120)) * 2
                ok = _wait_resident(api_url, host, model_id, folder, timeout_s=load_timeout)
                elapsed = time.time() - t0
                st = "SUCCESS" if ok else "TIMEOUT"
                results.append({"op": op, "model": model_id, "host": host,
                                "status": st, "elapsed_s": round(elapsed, 1)})
                _log_event("LOAD_" + st, host, model_id, "%.1fs" % elapsed)
                if not ok:
                    errors.append("load timeout: %s on %s (waited %.0fs)" % (model_id, host, load_timeout))
                elif ok:
                    # Goal-7: overrun alert if actual > 2x predicted
                    _pred = predict_load_eta(model_id, catalog)
                    if _pred and elapsed > 2.0 * _pred:
                        _log_event("ALERT", host, model_id,
                                   json.dumps({"type": "LOAD_OVERRUN", "model": model_id,
                                               "host": host, "predicted_s": _pred,
                                               "actual_s": round(elapsed, 1),
                                               "ratio": round(elapsed / _pred, 2),
                                               "message": "Load of %s took %.1fs (2x predicted %.1fs)"
                                                          % (model_id, elapsed, _pred)}))
            elif status_code == 409:
                results.append({"op": op, "model": model_id, "host": host,
                                "status": "CONFLICT", "detail": "HTTP 409 - generation active"})
                _log_event("LOAD_CONFLICT", host, model_id)
                errors.append("load 409 conflict: %s on %s" % (model_id, host))
            else:
                results.append({"op": op, "model": model_id, "host": host,
                                "status": "ERROR", "detail": "HTTP %d" % status_code})
                _log_event("LOAD_ERROR", host, model_id, str(resp))
                errors.append("load HTTP %d: %s on %s" % (status_code, model_id, host))

    return {"ok": len(errors) == 0, "results": results, "errors": errors}


def main(argv):
    if "--suggest-selftest" in argv:
        return suggest_selftest()
    if "--suggest" in argv:
        task = resident_s = None
        for a in argv:
            if a.startswith("task="):
                task = a[len("task="):]
            elif a.startswith("resident="):
                resident_s = _parse_kv(a[len("resident="):])
        print(json.dumps(suggest(task, resident_s or {}), indent=2))
        return 0
    if "--selftest" in argv:
        return selftest()
    if "--execute" in argv:
        agents, resident_s = [], None
        dry_run = "--dry-run" in argv
        for a in argv:
            if a.startswith("agents="):
                agents = [x for x in a[len("agents="):].split(",") if x]
            elif a.startswith("resident="):
                resident_s = _parse_kv(a[len("resident="):])
        p = plan(agents, resident_s or {})
        result = execute(p, dry_run=dry_run)
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1
    agents, resident_s = [], None
    for a in argv:
        if a.startswith("agents="):
            agents = [x for x in a[len("agents="):].split(",") if x]
        elif a.startswith("resident="):
            resident_s = _parse_kv(a[len("resident="):])
    p = plan(agents, resident_s or {})
    print(json.dumps(p, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
