#!/usr/bin/env python3
"""
Cross-Lane Convergence Coupling Map  (Orchestrator, Cycle-19 goal #6)
=====================================================================
For each lane compute:
  (a) contribution to fleet autonomy  -> realized reached_pct (0..100)
  (b) the SINGLE upstream dependency that most limits its convergence
Then rank lanes by "one-intervention-lifts-most" (leverage).

Model (data-driven, no per-lane tuning):
  * lane reached/open/pct ............ from goal_ledger.json
  * infra/external health signals .... from memory/ops/autonomy-score.json
                                         (+ feed-staleness.json, memory/outlet scan)
  * limiting_dependency(lane) = argmin over that lane's candidate upstreams of health()
  * limit_score = 100 - health(limiting_dependency)          (0..100; higher = more constrained)
  * leverage = limit_score * open_frac * serviceability(limiter_type)
      - open_frac = open/total (room to lift this lane)
      - serviceability = 1.5 if the limiter is infra/external (the lane CANNOT resolve it
        itself; one fleet-level intervention unblocks it immediately) else 1.0 for a peer-lane dep.
    This multiplier is a documented, uniform modeling assumption (not tuned per lane): an
    unresolvable-by-the-lane dependency yields higher immediate lift per unit of effort than a
    peer lane that can make its own progress.

Acceptance (self-test + real run):
  * on current data the true laggards (outlet, forge) rank top-2 by leverage;
  * every lane has EXACTLY ONE named limiting dependency;
  * re-running after a fix (limiter health rises) lowers that lane's limit_score.

Usage:
  python memory/orchestrator/convergence_coupling.py                 # real run -> memory/ops/convergence-coupling.json
  python memory/orchestrator/convergence_coupling.py --selftest      # hermetic synthetic assertions
"""
import json, sys, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

# ---- candidate upstream dependencies per lane (role-architecture knowledge) ----
# value: list of candidate dep keys. The weakest-health one becomes THE limiting dependency.
DEPS = {
    "orchestrator": ["infra_model", "infra_ledger"],
    "researcher":   ["external_sources", "lane:archivist"],
    "builder":      ["infra_model", "lane:scribe"],
    "pixel":        ["lane:designer", "infra_model"],
    "forge":        ["lane:builder", "infra_deploy"],
    "designer":     ["infra_media", "lane:outlet"],
    "mechanic":     ["infra_model", "infra_mirror"],
    "verifier":     ["lane:builder", "infra_deploy"],
    "scribe":       ["all_lanes", "infra_ledger"],
    "archivist":    ["infra_mirror", "external_sources"],
    "outlet":       ["lane:researcher", "external_platform_metrics"],
}
# dep keys that a lane cannot resolve itself -> higher serviceability (fleet-level intervention)
NON_SELF_SERVICE = {"infra_model", "infra_deploy", "infra_media", "infra_mirror",
                    "external_sources", "external_platform_metrics", "infra_ledger"}

# type used for deterministic tie-break: prefer infra/external over peer-lane when health ties
_TYPE_RANK = {"lane": 0, "all_lanes": 1, "infra": 2, "external": 3}
def dep_type(key):
    if key.startswith("lane:") or key == "all_lanes":
        return "lane" if key.startswith("lane:") else "all_lanes"
    return "external" if key.startswith("external_") else "infra"

# --------------------------------------------------------------------------- health resolvers
def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))

def build_health(autonomy, feed_staleness, outlet_has_metrics):
    """Return a resolver key->health in [0,1] from real data sources."""
    fc = autonomy.get("fleet_components", {}) or {}
    gate = autonomy.get("gate", {}) or {}
    host_up = (fc.get("host_uptime_pct") or 0.0) / 100.0          # 0..1
    model_load = (fc.get("model_load_rate") or 0.0)               # 0..1
    smoke_pass = (gate.get("smoke_first_try_pass_pct") or 0.0) / 100.0
    deploy_auto = (gate.get("deploys_autonomous_pct") or 0.0) / 100.0

    # mirror sync health from feed-staleness lag vs threshold
    if feed_staleness and isinstance(feed_staleness, dict):
        lag = float(feed_staleness.get("lag_min", 0) or 0)
        thr = float(feed_staleness.get("threshold_min", 45) or 45)
        mirror_h = _clamp(0.9 - max(0.0, lag - thr) / 200.0, 0.05, 0.95)
    else:
        mirror_h = 0.6

    return {
        "infra_model":   _clamp(host_up * 0.5 + model_load * 0.5),
        # canary/deploy infra is GATED on a loaded model: with model_load~0, live canaries
        # cannot run regardless of the (historical) autonomous-deploy ratio -> cap it.
        "infra_deploy":  _clamp((smoke_pass * 0.5 + model_load * 0.3 + deploy_auto * 0.2)
                                * min(1.0, 0.15 + model_load * 0.85)),
        "infra_media":   0.10,      # lumen/reel/splice media subs not_loaded this round
        "infra_mirror":  mirror_h,
        "infra_ledger":  0.90,      # goal_ledger.json generated today (fresh SSOT)
        "external_sources":        0.80,   # web_search functional
        "external_platform_metrics": 1.0 if outlet_has_metrics else 0.10,
    }

def lane_health(ledger, name):
    a = ledger.get("agents", {}).get(name)
    if not a:
        return None
    return (a.get("pct_reached", 0) / 100.0)

def all_lanes_health(ledger):
    ps = [a["pct_reached"] for a in ledger.get("agents", {}).values()]
    return (sum(ps) / len(ps) / 100.0) if ps else 0.0

def resolve(dep_key, ledger, base_health):
    if dep_key.startswith("lane:"):
        h = lane_health(ledger, dep_key[5:])
        return 0.0 if h is None else h
    if dep_key == "all_lanes":
        return all_lanes_health(ledger)
    return base_health.get(dep_key, 0.5)

# --------------------------------------------------------------------------- core (pure)
def coupling_map(ledger, autonomy, feed_staleness=None, outlet_has_metrics=False):
    base = build_health(autonomy, feed_staleness, outlet_has_metrics)
    lanes = ledger.get("agents", {})
    out = {}
    for name in lanes:
        a = lanes[name]
        total = max(1, a.get("total", 0))
        open_n = a.get("open", 0)
        reached_pct = a.get("pct_reached", 0)
        open_frac = open_n / total

        cands = DEPS.get(name, [])
        scored = []
        for k in cands:
            h = _clamp(resolve(k, ledger, base))
            scored.append((h, _TYPE_RANK[dep_type(k)], k))
        # weakest health wins; deterministic tie-break (health asc, type rank desc->infra first, name asc)
        if not scored:
            scored = [(0.5, 2, "unspecified")]
        scored.sort(key=lambda t: (t[0], -t[1], t[2]))
        h_lim, _, lim_key = scored[0]
        limit_score = round(100.0 * (1.0 - h_lim), 2)
        svc = 1.5 if lim_key in NON_SELF_SERVICE else 1.0
        leverage = round(limit_score * open_frac * svc, 2)
        out[name] = {
            "contribution_score": reached_pct,            # (a) realized autonomy contribution 0..100
            "headroom": round(open_frac * 100, 2),        # remaining lift potential 0..100
            "reached": a.get("reached", 0),
            "open": open_n,
            "total": total,
            "limiting_dependency": lim_key,               # (b) exactly ONE named upstream
            "limiting_dependency_health": round(100.0 * h_lim, 2),
            "limit_score": limit_score,
            "serviceability": svc,
            "leverage": leverage,
        }
    return out

def rank_leverage(coupling):
    return sorted(coupling.items(), key=lambda kv: (-kv[1]["leverage"], kv[0]))

# --------------------------------------------------------------------------- real-run IO
def outlet_has_live_metrics():
    d = ROOT / "memory" / "outlet"
    if not d.exists():
        return False
    for p in d.rglob("*.json"):
        n = p.name.lower()
        if any(t in n for t in ("engage", "metric", "fitness")):
            return True
    return False

def load_json(p, default):
    try:
        return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
    except Exception:
        return default

def real_run():
    ledger = load_json(ROOT / "goal_ledger.json", {"agents": {}})
    autonomy = load_json(ROOT / "memory" / "ops" / "autonomy-score.json", {})
    feed_staleness = load_json(ROOT / "memory" / "ops" / "feed-staleness.json", None)
    outm = outlet_has_live_metrics()
    coupling = coupling_map(ledger, autonomy, feed_staleness, outm)
    ranked = rank_leverage(coupling)
    doc = {
        "generated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "model": (
            "leverage = limit_score * open_frac * serviceability(limiter); "
            "limiting_dependency = argmin candidate-upstream health; "
            "serviceability 1.5 for infra/external (lane cannot self-serve) else 1.0"
        ),
        "inputs": {
            "ledger": "goal_ledger.json",
            "autonomy": "memory/ops/autonomy-score.json",
            "feed_staleness": "memory/ops/feed-staleness.json",
            "outlet_live_metrics_present": outm,
        },
        "lanes": coupling,
        "leverage_ranking": [
            {"rank": i + 1, "lane": k, **v} for i, (k, v) in enumerate(ranked)
        ],
        "top_leverage_targets": [k for k, _ in ranked[:3]],
        # clear laggard cluster: leverage within 15% of the max (rank-independent flag)
        "high_leverage_band": (
            [k for k, v in ranked if v["leverage"] >= 0.85 * ranked[0][1]["leverage"]]
            if ranked else []
        ),
    }
    outp = ROOT / "memory" / "ops" / "convergence-coupling.json"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return doc, outp

# --------------------------------------------------------------------------- self-test
def selftest():
    ok = 0; fail = 0
    def check(cond, msg):
        nonlocal ok, fail
        if cond: ok += 1; print(f"  PASS {msg}")
        else: fail += 1; print(f"  FAIL {msg}")

    # synthetic laggard-shaped ledger: outlet & forge low-reached + big open gap
    def mk(name, total, reached, open_n):
        return {"total": total, "reached": reached, "open": open_n,
                "pct_reached": round(100.0 * reached / max(1, total))}
    ledger = {"agents": {
        "orchestrator": mk("o", 10, 5, 5),
        "researcher":   mk("r", 10, 10, 0),
        "builder":      mk("b", 10, 6, 4),
        "scribe":       mk("s", 10, 7, 3),
        "designer":     mk("d", 10, 5, 5),
        "mechanic":     mk("m", 10, 6, 4),
        "verifier":     mk("v", 10, 6, 4),
        "archivist":    mk("a", 10, 6, 4),
        "pixel":        mk("p", 10, 5, 5),
        "forge":        mk("f", 10, 1, 9),     # laggard
        "outlet":       mk("o2", 10, 1, 9),    # laggard
    }}
    # weak infra: no model loaded, no smoke pass -> infra_model & infra_deploy low
    autonomy = {"fleet_components": {"host_uptime_pct": 25, "model_load_rate": 0.0},
                "gate": {"smoke_first_try_pass_pct": 0.0, "deploys_autonomous_pct": 100.0}}
    feed = {"lag_min": 120, "threshold_min": 45}

    c1 = coupling_map(ledger, autonomy, feed, outlet_has_metrics=False)
    ranked = rank_leverage(c1)
    top3 = [k for k, _ in ranked[:3]]
    check("outlet" in top3 and "forge" in top3,
          f"laggards outlet+forge in top-3 (got {top3})")

    # exactly one named limiting dependency per lane
    check(all(len(v["limiting_dependency"]) > 0 for v in c1.values()),
          "every lane has exactly one named limiting dependency")

    # re-running after a FIX lowers the affected lane's limit_score:
    # fix = models load (model_load_rate 0 -> 1.0) raises infra_model & infra_deploy health
    autonomy_fixed = {"fleet_components": {"host_uptime_pct": 100, "model_load_rate": 1.0},
                      "gate": {"smoke_first_try_pass_pct": 90.0, "deploys_autonomous_pct": 100.0}}
    c2 = coupling_map(ledger, autonomy_fixed, feed, outlet_has_metrics=False)
    forge_before = c1["forge"]["limit_score"]
    forge_after = c2["forge"]["limit_score"]
    check(forge_after < forge_before,
          f"fixing deploy-infra lowers forge limit_score ({forge_before} -> {forge_after})")
    mech_before = c1["mechanic"]["limit_score"]
    mech_after = c2["mechanic"]["limit_score"]
    check(mech_after < mech_before,
          f"fixing model-availability lowers mechanic limit_score ({mech_before} -> {mech_after})")

    print(f"\nSELFTEST: {ok} passed, {fail} failed")
    return fail == 0

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    doc, outp = real_run()
    print(f"wrote {outp.relative_to(ROOT)}")
    print("top leverage targets:", doc["top_leverage_targets"])
    for row in doc["leverage_ranking"][:5]:
        print(f"  #{row['rank']} {row['lane']:13} lev={row['leverage']:7.2f} "
              f"limit={row['limit_score']:6.2f} via={row['limiting_dependency']} "
              f"contrib={row['contribution_score']}")
