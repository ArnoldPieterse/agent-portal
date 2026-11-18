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
    for host in [h for h in hosts_meta if h in required]:   # catalog order for determinism
        budget = float(hosts_meta[host].get("vram_total_gb", 0))
        res_now = [m for m in resident.get(host, []) if m in mindex]
        req_here = required.get(host, set())
        to_load = [m for m in sorted(req_here) if m not in res_now]

        loaded = {m: float(mindex[m]["vram_gb"]) for m in res_now}
        actions = []
        pending = list(to_load)
        guard = 0
        while pending and guard < 256:
            guard += 1
            mid = pending[0]
            need = float(mindex[mid]["vram_gb"])
            used = sum(loaded.values())
            if used + need <= budget + 1e-9:
                actions.append({"op": "LOAD", "model": mid, "host": host,
                                "reason": "required; fits (used %.1f + need %.1f <= %d)"
                                          % (used, need, budget)})
                loaded[mid] = need
                pending.pop(0)
            else:
                evictable = [m for m in loaded if m not in req_here and m != mid]
                if not evictable:
                    actions.append({"op": "BLOCKED", "model": mid, "host": host,
                                    "reason": "needs %.1fGB but only %.1fGB free; no non-required resident to evict"
                                              % (need, max(0.0, budget - used))})
                    pending.pop(0)
                    continue
                # evict lowest-priority (non-required) first = largest VRAM draw
                victim = max(evictable, key=lambda m: float(mindex[m]["vram_gb"]))
                actions.append({"op": "UNLOAD", "model": victim, "host": host,
                                "reason": "evict non-required resident (largest %.1fGB) to make room for %s"
                                          % (float(mindex[victim]["vram_gb"]), mid)})
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

    return {
        "ok": True,
        "required_by_host": {h: sorted(v) for h, v in required.items()},
        "unresolved_agents": unresolved,
        "hosts": hosts_out,
        "sequence": sequence,
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

    print("\n%d/%d selftest checks passed" % (11 - len(failures), 11))
    if failures:
        print("FAILED:", failures)
        return 1
    print("ALL PLAN CASES PASS on real catalog")
    return 0


def _parse_kv(s, sep=";"):
    out = {}
    for chunk in filter(None, s.split(sep)):
        if ":" not in chunk:
            continue
        k, v = chunk.split(":", 1)
        out[k.strip()] = [x.strip() for x in v.split(",") if x.strip()]
    return out


def main(argv):
    if "--selftest" in argv:
        return selftest()
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
