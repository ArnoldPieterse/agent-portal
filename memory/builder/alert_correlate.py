#!/usr/bin/env python3
"""
alert_correlate.py - Alert Correlation Engine (Builder goal #3, cycle-14).

Consumes raw alerts from fleet probes (memory/fleet/**/*.json) + OPS-NOTES in
memory/ops/blockers.md; groups temporally-close (< 5 min window) AND
topologically-linked (same host OR same agent) alerts into a single incident,
with a root-cause hypothesis derived from topology.

Output: memory/ops/incidents.jsonl
  fields per line: {ts, incident_id, alerts:[...], root_cause_hypothesis, severity, status}

Design: the correlation logic (group_into_incidents / root_cause / severity) is a
PURE function over a list of normalized alert dicts, so it is fully testable on
synthetic fixtures independent of which real probe files happen to exist.
IO wrappers (load_fleet_alerts / load_ops_note_alerts) are best-effort and return
[] when their source is absent, so a live run never crashes on missing data.

Usage:
  python memory/builder/alert_correlate.py            # correlate real sources -> incidents.jsonl
  python memory/builder/alert_correlate.py --selftest # run acceptance tests
"""
import json, os, re, sys, datetime, argparse
from collections import Counter

ROOT = "memory"
FLEET_DIR = os.path.join(ROOT, "fleet")
BLOCKERS_MD = os.path.join(ROOT, "ops", "blockers.md")
OUT_FILE = os.path.join(ROOT, "ops", "incidents.jsonl")

# Correlation windows / thresholds (per spec)
TIME_WINDOW_S = 300          # < 5 min
SEV_RANK = {"critical": 4, "error": 3, "warn": 2, "warning": 2,
            "info": 1, "ok": 0}
RANK_SEV = {4: "critical", 3: "error", 2: "warn", 1: "info", 0: "ok"}


# --------------------------------------------------------------------------- #
# Timestamp handling
# --------------------------------------------------------------------------- #
def parse_ts(ts):
    """Parse an ISO timestamp (or epoch) to epoch seconds; None on failure."""
    if ts is None:
        return None
    if isinstance(ts, (int, float)) and not isinstance(ts, bool):
        return float(ts)
    s = str(ts).strip()
    try:
        return float(s)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(s, fmt).timestamp()
        except ValueError:
            continue
    return None


def _rank(sev):
    if isinstance(sev, (int, float)) and not isinstance(sev, bool):
        return int(sev)
    return SEV_RANK.get(str(sev).strip().lower(), 1)


# --------------------------------------------------------------------------- #
# Normalization: any raw alert -> canonical dict
# --------------------------------------------------------------------------- #
def normalize_alert(raw, source=""):
    """Coerce a raw alert (dict or string) into a canonical alert dict."""
    if isinstance(raw, str):
        raw = {"message": raw}
    a = {
        "ts": parse_ts(raw.get("ts") or raw.get("timestamp") or raw.get("time")),
        "host": (str(raw["host"]).strip() if raw.get("host") else None),
        "agent": (str(raw["agent"]).strip() if raw.get("agent") else None),
        "component": (str(raw["component"]).strip()
                      if raw.get("component") else None),
        "severity": str(raw["severity"]).strip().lower() if raw.get("severity") else "warn",
        "message": str(raw.get("message") or raw.get("detail") or raw.get("note") or "").strip(),
        "source": source,
    }
    # component fallback: derive from host/agent so hypothesis always has a target
    if not a["component"]:
        a["component"] = a["host"] or a["agent"] or "unknown-component"
    return a


def _topology_nodes(a):
    nodes = set()
    if a.get("host"):
        nodes.add(("host", a["host"]))
    if a.get("agent"):
        nodes.add(("agent", a["agent"]))
    return nodes


def _linked(a, b):
    """Two alerts are linked iff temporally close AND share a topology node."""
    if a["ts"] is None or b["ts"] is None:
        # unknown time: rely on topology alone (conservative link)
        return bool(_topology_nodes(a) & _topology_nodes(b))
    if abs(a["ts"] - b["ts"]) > TIME_WINDOW_S:
        return False
    return bool(_topology_nodes(a) & _topology_nodes(b))


# --------------------------------------------------------------------------- #
# Pure correlation core (union-find over linked alerts)
# --------------------------------------------------------------------------- #
def group_into_incidents(alerts):
    """Group normalized alerts into connected components (incidents).

    Two alerts are in the same incident if they are temporally-close (<5min)
    AND topologically-linked (same host or agent); transitive closure via
    union-find. Returns list of lists of alert dicts, sorted by earliest ts.
    """
    n = len(alerts)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[ry] = rx

    for i in range(n):
        for j in range(i + 1, n):
            if _linked(alerts[i], alerts[j]):
                union(i, j)

    clusters = {}
    for i in range(n):
        clusters.setdefault(find(i), []).append(alerts[i])

    incidents = []
    for members in clusters.values():
        members.sort(key=lambda a: (a["ts"] if a["ts"] is not None else float("inf")))
        incidents.append(members)
    # stable ordering: by earliest ts, then size desc
    incidents.sort(key=lambda m: (m[0]["ts"] if m[0]["ts"] is not None else float("inf"), -len(m)))
    return incidents


def root_cause_hypothesis(members):
    """Derive a non-empty root-cause hypothesis from cluster topology.

    Strategy: the most-shared topology node (host/agent) is the likely epicentre;
    combine with the highest-severity alert's component + message as the symptom.
    """
    node_counts = Counter()
    for a in members:
        for node in _topology_nodes(a):
            node_counts[node] += 1

    if node_counts:
        # Break ties by preferring host over agent (hosts are more specific topo)
        sorted_nodes = sorted(node_counts.items(), key=lambda kv: (-kv[1], 0 if kv[0][0] == "host" else 1))
        (kind, name), cnt = sorted_nodes[0]
        epicentre = f"{name} ({kind})"
    else:
        epicentre = "an unidentified component"

    worst = max(members, key=lambda a: _rank(a["severity"]))
    symptom = (worst.get("message") or worst.get("component") or "fault").strip()
    n_alerts = len(members)
    return (f"Suspected root cause on {epicentre}: correlated burst of {n_alerts} alert(s) "
            f"sharing this topology node; leading symptom '{symptom}' "
            f"(severity={worst['severity']}).")


def incident_severity(members):
    return RANK_SEV[max(_rank(a["severity"]) for a in members)]


def build_incidents(alerts, now_iso=None):
    """Pure: normalized alerts -> list of incident records (no IO)."""
    now_iso = now_iso or datetime.datetime.now(datetime.timezone.utc).isoformat()
    incidents = []
    clusters = group_into_incidents(alerts)
    for idx, members in enumerate(clusters):
        ts_min = min((a["ts"] for a in members if a["ts"] is not None), default=None)
        ts_iso = (datetime.datetime.fromtimestamp(ts_min, datetime.timezone.utc).isoformat()
                  if ts_min is not None else now_iso)
        incidents.append({
            "ts": ts_iso,
            "incident_id": f"INC-{abs(hash((ts_iso, members[0]['component']))) % 10**8:08d}-{idx:02d}",
            "alerts": [{"ts": a["ts"], "host": a["host"], "agent": a["agent"],
                        "component": a["component"], "severity": a["severity"],
                        "message": a["message"], "source": a["source"]} for a in members],
            "root_cause_hypothesis": root_cause_hypothesis(members),
            "severity": incident_severity(members),
            "status": "open",
        })
    return incidents


# --------------------------------------------------------------------------- #
# IO wrappers (best-effort)
# --------------------------------------------------------------------------- #
def load_fleet_alerts(fleet_dir=FLEET_DIR):
    """Scan fleet probe JSON files for alert records. Returns normalized alerts.

    Accepts: a top-level list of alert dicts, an {"alerts": [...]} object, or an
    object whose values include per-host alert lists. Tolerant of any shape.
    """
    out = []
    if not os.path.isdir(fleet_dir):
        return out
    for dp, _dn, fns in os.walk(fleet_dir):
        for fn in sorted(fns):
            if not fn.endswith(".json"):
                continue
            path = os.path.join(dp, fn)
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue
            candidates = []
            if isinstance(data, list):
                candidates = data
            elif isinstance(data, dict):
                if isinstance(data.get("alerts"), list):
                    candidates = data["alerts"]
                else:
                    # treat any nested list of dicts that look like alerts
                    for v in data.values():
                        if isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
                            if any(k in v[0] for k in ("severity", "message", "detail", "note")):
                                candidates.extend(v)
            for c in candidates:
                if isinstance(c, dict) and any(k in c for k in ("severity", "message", "detail", "note", "alert")):
                    out.append(normalize_alert(c, source=os.path.relpath(path)))
    return out


_OPS_NOTE_RE = re.compile(r"^##\s*\[OPS-NOTE\s+([0-9]{4}-[0-9]{2}-[0-9]{2})[^\]]*\]\s*(.*)$", re.M)

def load_ops_note_alerts(blockers_md=BLOCKERS_MD):
    """Parse OPS-NOTE headers in blockers.md into alerts (one per note)."""
    out = []
    if not os.path.exists(blockers_md):
        return out
    try:
        text = open(blockers_md, encoding="utf-8").read()
    except Exception:
        return out
    matches = list(_OPS_NOTE_RE.finditer(text))
    for i, m in enumerate(matches):
        date, title = m.group(1), m.group(2).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end]
        # severity heuristic from title/body keywords
        low = (title + " " + body[:400]).lower()
        sev = "error" if any(k in low for k in ("down", "unreachable", "fail", "oom", "blocked", "crash")) else "warn"
        # host/agent hint from first @Name or host token
        agent_m = re.search(r"@([A-Za-z]+)", body)
        host_m = re.search(r"\b([a-z]{4,12})\s+seat\b|on ([A-Z][a-zA-Z0-9]+)\b", body)
        out.append(normalize_alert({
            "ts": f"{date}T00:00:00",
            "agent": agent_m.group(1) if agent_m else None,
            "host": (host_m.group(1) or host_m.group(2)) if host_m else None,
            "component": title[:60] or f"ops-note-{i}",
            "severity": sev,
            "message": title[:120],
        }, source="blockers.md"))
    return out


def correlate(fleet_dir=FLEET_DIR, blockers_md=BLOCKERS_MD):
    alerts = load_fleet_alerts(fleet_dir) + load_ops_note_alerts(blockers_md)
    # drop alerts with no topology node AND no time (pure noise) -> keep if any signal
    return build_incidents(alerts), alerts


def main():
    ap = argparse.ArgumentParser(description="Alert Correlation Engine")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--fleet-dir", default=FLEET_DIR)
    ap.add_argument("--blockers", default=BLOCKERS_MD)
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    incidents, alerts = correlate(args.fleet_dir, args.blockers)
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for inc in incidents:
            f.write(json.dumps(inc, ensure_ascii=False) + "\n")
    print(f"{len(alerts)} alerts -> {len(incidents)} incidents -> {OUT_FILE}")
    return 0


def selftest():
    """Acceptance tests matching the goal spec verification criteria."""
    print("=" * 60)
    print("alert_correlate.py - SELFTEST (spec-aligned)")
    print("=" * 60)

    base = datetime.datetime(2026, 11, 23, 10, 0, 0)
    def t(sec):
        return (base + datetime.timedelta(seconds=sec)).isoformat()

    # --- AC1: burst of 5 correlated alerts (same host, 3-min span) -> exactly 1 incident
    burst = [normalize_alert({"ts": t(i * 40), "host": "white", "agent": "mechanic",
                              "component": "gpu0", "severity": "error",
                              "message": f"VRAM OOM spike {i}"}, source="probe")
             for i in range(5)]  # span = 4*40 = 160s < 300s
    inc_burst = build_incidents(burst)
    ac1 = len(inc_burst) == 1 and len(inc_burst[0]["alerts"]) == 5
    print(f"AC1: 5 correlated (same host, 3-min span) -> exactly 1 incident "
          f"({len(inc_burst)} incident(s), {len(inc_burst[0]['alerts']) if inc_burst else 0} alerts) -> {'PASS' if ac1 else 'FAIL'}")

    # --- AC2: 2 uncorrelated alerts remain separate incidents
    u1 = normalize_alert({"ts": t(0), "host": "white", "agent": "mechanic",
                          "component": "gpu0", "severity": "error", "message": "A"}, source="probe")
    u2 = normalize_alert({"ts": t(3600), "host": "black", "agent": "researcher",
                          "component": "disk", "severity": "warn", "message": "B"}, source="probe")
    inc_unc = build_incidents([u1, u2])  # different host/agent AND >5min apart
    ac2 = len(inc_unc) == 2
    print(f"AC2: 2 uncorrelated alerts (diff host+agent, >5min) -> separate incidents "
          f"({len(inc_unc)}) -> {'PASS' if ac2 else 'FAIL'}")

    # --- AC3: root_cause_hypothesis non-empty AND references a specific component
    hyp = inc_burst[0]["root_cause_hypothesis"] if inc_burst else ""
    refs_component = ("white" in hyp) and bool(hyp.strip())
    ac3 = len(hyp.strip()) > 0 and refs_component
    print(f"AC3: root_cause non-empty + references component -> {'PASS' if ac3 else 'FAIL'}")
    print(f"      hypothesis: {hyp[:90]}...")

    # --- AC4: JSONL valid (json.loads per line) on a written temp file
    import tempfile
    tmp = os.path.join(tempfile.gettempdir(), "ac_selftest_incidents.jsonl")
    with open(tmp, "w", encoding="utf-8") as f:
        for inc in inc_burst + inc_unc:
            f.write(json.dumps(inc, ensure_ascii=False) + "\n")
    ok = True
    required = {"ts", "incident_id", "alerts", "root_cause_hypothesis", "severity", "status"}
    with open(tmp, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            if not required.issubset(rec.keys()):
                ok = False
    os.remove(tmp)
    ac4 = ok
    print(f"AC4: JSONL valid, all records carry required fields -> {'PASS' if ac4 else 'FAIL'}")

    # --- BONUS: topology linking chains across shared agent even with time gaps bridged
    c1 = normalize_alert({"ts": t(0), "agent": "builder", "component": "x", "severity": "warn", "message": "c1"}, source="p")
    c2 = normalize_alert({"ts": t(200), "agent": "builder", "host": "white", "component": "y", "severity": "error", "message": "c2"}, source="p")
    inc_chain = build_incidents([c1, c2])  # same agent, within window -> linked
    acb = len(inc_chain) == 1
    print(f"BONUS: shared-agent bridge links into 1 incident ({len(inc_chain)}) -> {'PASS' if acb else 'FAIL'}")

    passed = sum([ac1, ac2, ac3, ac4])
    print("=" * 60)
    print(f"RESULT: {passed}/4 ACs PASSED" + (f" (+bonus {'PASS' if acb else 'FAIL'})" if True else ""))
    return 0 if passed == 4 else 1


if __name__ == "__main__":
    sys.exit(main())
