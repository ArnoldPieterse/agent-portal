"""gev_snapshot.py - world memory pipeline + host risk awareness (2026-11-27, Phase 8 steps 57-58).

Runs from the portal's _world_watchdog thread every 30 min (also: `python memory/world/gev_snapshot.py`
for a one-shot). Keyless GEV MCP feeds only:
  * snapshots.jsonl - one line per run: quakes M>4 (24h), active cyclones, recent launches,
    + situation_brief over the user location when configured (memory/world/config.json)
  * events.jsonl    - threshold events (quake M>5 / active cyclone / notable launch) that feed
    the Mind Lab "planet event" cards (step 59) via /api/mind-lab op=planet
  * host risk       - fleet host coordinates (config.host_locations) cross-referenced against the
    same events; a hit appends a NEEDS-HUMAN line to memory/ops/blockers.md + host-risk.json

Coordinates are OURS, chosen in config.json (step 63: no user-location leakage into feed queries;
nothing here phones home). Every GEV call is best-effort with a hard timeout - a dead globe
records an honest error field and never raises.
"""
import json, math, os, re, time

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # memory/world -> root
WORLD_DIR = os.path.join(HERE, "memory", "world")
CONFIG_PATH = os.path.join(WORLD_DIR, "config.json")
SNAP_PATH = os.path.join(WORLD_DIR, "snapshots.jsonl")
EVENTS_PATH = os.path.join(WORLD_DIR, "events.jsonl")
RISK_PATH = os.path.join(WORLD_DIR, "host-risk.json")
BLOCKERS = os.path.join(HERE, "memory", "ops", "blockers.md")

DEFAULT_CONFIG = {"user_location": None,          # {lat, lon, place?} - set to enable the local brief
                  "host_locations": {},           # {"White": [lat, lon], ...} - for host-risk cross-ref
                  "risk_radius_km": 500}


def _load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        d = json.load(open(CONFIG_PATH, encoding="utf-8"))
        if isinstance(d, dict):
            cfg.update({k: d[k] for k in DEFAULT_CONFIG if k in d})
    except Exception:
        pass
    return cfg


def _gev_call(name, arguments=None, timeout=60):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "gs_gev", os.path.join(HERE, "memory", "archivist", "gev_bridge.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.call(name, arguments or {}, timeout=timeout)


def _haversine_km(a, b):
    try:
        lat1, lon1, lat2, lon2 = map(math.radians, [a[0], a[1], b[0], b[1]])
        h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
        return 6371.0 * 2 * math.asin(math.sqrt(h))
    except Exception:
        return None


def _append_jsonl(path, rec):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


_EP = None
def _event_parse():
    global _EP
    if _EP is None:
        import sys as _s
        _s.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import event_parse as _EP
    return _EP

def _parse_coords(text):
    """GEV texts often carry 'lat, lon' pairs; grab the first plausible one."""
    m = re.search(r"(-?\d{1,2}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)", text or "")
    if m:
        return [float(m.group(1)), float(m.group(2))]
    return None


def _quake_events(r):
    """JSON-blob aware via event_parse.py (2026-11-27 fix)."""
    return [e for e in _event_parse().events_from({"quakes": r.get("text") or ""}) if e["kind"] == "quake"]
def _cyclone_events(r):
    """JSON-blob aware via event_parse.py (2026-11-27 fix)."""
    return [e for e in _event_parse().events_from({"cyclones": r.get("text") or ""}) if e["kind"] == "cyclone"]
def _launch_events(r):
    """JSON-blob aware via event_parse.py (2026-11-27 fix)."""
    return [e for e in _event_parse().events_from({"launches": r.get("text") or ""}) if e["kind"] == "launch"]
def take_snapshot():
    """One world pass. Returns the snapshot record (also appended to snapshots.jsonl)."""
    cfg = _load_config()
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    snap = {"ts": ts, "globe_up": True}
    events = []
    try:
        r = _gev_call("get_earthquakes", {"min_magnitude": 4.0, "limit": 12})
        snap["quakes"] = (r.get("text") or "")[:3000]
        events += _quake_events(r)
    except Exception as e:
        snap["globe_up"] = False
        snap["quakes_error"] = str(e)[:150]
    if snap["globe_up"]:
        try:
            r = _gev_call("get_cyclones", {})
            snap["cyclones"] = (r.get("text") or "")[:2000]
            events += _cyclone_events(r)
        except Exception as e:
            snap["cyclones_error"] = str(e)[:150]
        try:
            r = _gev_call("get_recent_launches", {"limit": 8})
            snap["launches"] = (r.get("text") or "")[:2500]
            events += _launch_events(r)
        except Exception as e:
            snap["launches_error"] = str(e)[:150]
        ul = cfg.get("user_location")
        if isinstance(ul, dict) and ul.get("lat") is not None:
            try:
                r = _gev_call("situation_brief",
                              {"area": {"lat": float(ul["lat"]), "lon": float(ul["lon"]),
                                        "radius_km": 300}})
                snap["local_brief"] = (r.get("text") or "")[:2500]
            except Exception as e:
                snap["local_brief_error"] = str(e)[:150]
    _append_jsonl(SNAP_PATH, snap)
    # threshold events -> mind-lab planet cards (deduped against what's already on file)
    known = set()
    try:
        for line in open(EVENTS_PATH, encoding="utf-8"):
            try:
                known.add(json.loads(line).get("id"))
            except Exception:
                pass
    except Exception:
        pass
    fresh = [e for e in events if e["id"] not in known]
    for e in fresh[:10]:
        _append_jsonl(EVENTS_PATH, {"ts": ts, **e})
    snap["new_events"] = len(fresh)
    _host_risk(cfg, fresh, ts)
    return snap


def _host_risk(cfg, events, ts):
    """Step 58: fleet host locations vs world events -> NEEDS-HUMAN in blockers.md + host-risk.json."""
    locs = cfg.get("host_locations") or {}
    if not locs:
        return
    radius = float(cfg.get("risk_radius_km") or 500)
    risk = {"active": [], "checked_at": ts}
    for host, coords in locs.items():
        try:
            hc = [float(coords[0]), float(coords[1])]
        except Exception:
            continue
        for e in events:
            # coordinates only where the event text carried them; otherwise skip (honest)
            ec = _parse_coords(e.get("desc") or "")
            if not ec:
                continue
            d = _haversine_km(hc, ec)
            if d is None or d > radius:
                continue
            alert = {"host": host, "event_id": e["id"], "kind": e["kind"],
                     "distance_km": round(d, 1), "desc": e.get("desc", "")[:200], "ts": ts}
            risk["active"].append(alert)
            try:
                line = ("- [%s] NEEDS-HUMAN (world-risk): %s - %s within %.0f km of host %s "
                        "(GEV snapshot, auto; clear when the event passes)\n"
                        % (ts[:16].replace("T", " "), e["kind"], e.get("desc", "")[:120], d, host))
                with open(BLOCKERS, "a", encoding="utf-8") as f:
                    f.write(line)
            except Exception:
                pass
    try:
        os.makedirs(WORLD_DIR, exist_ok=True)
        with open(RISK_PATH, "w", encoding="utf-8") as f:
            json.dump(risk, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


if __name__ == "__main__":
    s = take_snapshot()
    print(json.dumps({k: v for k, v in s.items() if not isinstance(v, str) or len(v) < 200}, indent=1))
