#!/usr/bin/env python
"""Residency Matrix Auto-Refresh (Researcher goal #2).

Compares EXPECTED model residency (from memory/llm/hotload-catalog.json) against
ACTUAL loaded models per host, and writes memory/llm/residency-matrix.md with
drift flags.

Expected residency = {host: set(model.id for model in catalog.models if model.host==host)}.
Actual residency  = the set of model ids each host reports as currently loaded via
                    GET /api/inference/loaded-models (fallback: /v1/models).

Drift classes per (host, expected model):
  - DRIFT : expected resident but NOT loaded  (the 'deliberately unloaded' case)
  - OK    : expected resident AND loaded
Unloaded-but-not-expected models are reported as EXTRA.

Usage:
  python memory/researcher/residency_matrix.py               # live: query each host's API
  python memory/researcher/residency_matrix.py --hosts H.json  # offline replay from a capture file
  python memory/researcher/residency_matrix.py --selftest        # prove drift logic, no network

--hosts H.json format: {"<host>": ["loaded-model-id", ...], ...}
A non-sandbox seat (White ops terminal / RDP) captures real API output into H.json,
then any seat can replay the comparison offline.
"""
import json, os, sys, datetime
try:
    import urllib.request
except Exception:
    urllib = None

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG = os.path.normpath(os.path.join(HERE, "..", "llm", "hotload-catalog.json"))
OUT = os.path.normpath(os.path.join(HERE, "..", "llm", "residency-matrix.md"))
TIMEOUT = 6


def load_catalog(path=CATALOG):
    with open(path) as f:
        return json.load(f)


def expected_residency(catalog):
    """{host: set(model ids)} from catalog.models[].host."""
    exp = {}
    for m in catalog.get("models", []):
        h = m.get("host")
        if not h:
            continue
        exp.setdefault(h, set()).add(m["id"])
    return exp


def host_apis(catalog):
    return catalog.get("_meta", {}).get("hosts", {})


def query_host_loaded(api_url):
    """Return set of loaded model ids from a host's LM Studio API, or None on failure."""
    if urllib is None:
        return None
    for path in ("/api/inference/loaded-models", "/v1/models"):
        url = api_url.rstrip("/") + path
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
                data = json.loads(r.read().decode())
        except Exception:
            continue
        ids = set()
        models = data.get("data", data if isinstance(data, list) else [])
        for m in models:
            mid = m.get("id") or m.get("model") or m.get("name")
            if not mid:
                continue
            # /v1/models may report loaded flag; only count resident ones when the field exists
            if isinstance(m, dict) and "loaded" in m and not m["loaded"]:
                continue
            ids.add(mid)
        if ids or path == "/api/inference/loaded-models":
            return ids
    return None


def compare(expected, actual):
    """Return (rows, drift_count, extra_count). rows = list of dicts for the matrix."""
    rows, drift, extra = [], 0, 0
    hosts = sorted(set(expected) | set(actual))
    for h in hosts:
        exp = expected.get(h, set())
        act = actual.get(h)
        if act is None:
            # host unreachable -> report as UNREACHABLE, do not count as drift
            rows.append({"host": h, "expected": sorted(exp), "status": "UNREACHABLE", "drift": []})
            continue
        for mid in sorted(exp):
            if mid in act:
                rows.append({"host": h, "model": mid, "status": "OK", "drift": False})
            else:
                drift += 1
                rows.append({"host": h, "model": mid, "status": "DRIFT", "drift": True})
        for mid in sorted(act - exp):
            extra += 1
            rows.append({"host": h, "model": mid, "status": "EXTRA", "drift": False})
    return rows, drift, extra


def render(catalog, expected, actual, rows, drift, extra):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    hosts = host_apis(catalog)
    unreachable = [r["host"] for r in rows if r.get("status") == "UNREACHABLE"]
    lines = []
    lines.append("# Residency Matrix (auto-refreshed)")
    lines.append("")
    lines.append(f"Last run: {now}  |  hosts: {len(hosts)}  |  DRIFT: **{drift}**  |  EXTRA: {extra}  |  unreachable: {len(unreachable)}")
    lines.append("")
    lines.append("Expected residency is derived from `memory/llm/hotload-catalog.json` (`models[].host`).")
    lines.append("Actual = each host's `GET /api/inference/loaded-models`. DRIFT = expected resident but not loaded.")
    lines.append("")
    for h in sorted(set(expected) | set(actual)):
        exp = expected.get(h, set())
        api = hosts.get(h, {}).get("api", "?")
        act = actual.get(h)
        if act is None:
            lines.append(f"## {h}  ({api}) — UNREACHABLE")
            lines.append("")
            continue
        hrows = [r for r in rows if r["host"] == h]
        status = "CLEAN" if not any(r.get("drift") for r in hrows) else f"{sum(1 for r in hrows if r.get('drift'))} DRIFT"
        lines.append(f"## {h}  ({api}) — {status}")
        lines.append("")
        lines.append("| model | expected | actual | status |")
        lines.append("|---|---|---|---|")
        for r in hrows:
            exp_mark = "yes" if r.get("drift") is not None or r["status"] in ("OK", "DRIFT") else "-"
            act_mark = "loaded" if (r["status"] == "OK" or r["status"] == "EXTRA") else "absent"
            lines.append(f"| {r['model']} | {exp_mark} | {act_mark} | **{r['status']}** |")
        lines.append("")
    return "\n".join(lines)


def selftest():
    """Prove drift logic offline: clean state -> 0 drifts; deliberately unloaded model -> DRIFT."""
    catalog = load_catalog()
    expected = expected_residency(catalog)
    if not expected:
        print("SELFTEST FAIL: no expected residency derived from catalog")
        return 1
    # Case A (clean): every host reports all its expected models loaded -> 0 drifts.
    clean_actual = {h: set(ids) for h, ids in expected.items()}
    rows_a, drift_a, extra_a = compare(expected, clean_actual)
    ok_a = drift_a == 0 and extra_a == 0
    # Case B (degraded): unload one expected model on the first host -> exactly that model DRIFTs.
    degraded = {h: set(ids) for h, ids in expected.items()}
    target_host = sorted(expected)[0]
    target_model = sorted(expected[target_host])[0]
    degraded[target_host].discard(target_model)
    rows_b, drift_b, extra_b = compare(expected, degraded)
    drifted = [r["model"] for r in rows_b if r.get("drift")]
    ok_b = (
        drift_b == 1
        and drifted == [target_model]
        and any(
            r["host"] == target_host and r["model"] == target_model and r["status"] == "DRIFT"
            for r in rows_b
        )
    )
    # Case C (unreachable): a host that returns None is reported UNREACHABLE, not counted as drift.
    unreach = {h: set(ids) for h, ids in expected.items()}
    unreach.pop(sorted(unreach)[0], None)
    rows_c, drift_c, _ = compare(expected, unreach)
    ok_c = any(r.get("status") == "UNREACHABLE" for r in rows_c)

    print(f"catalog: {len(expected)} hosts, expected models: {sum(len(v) for v in expected.values())}")
    print(f"[A] clean state          -> drifts={drift_a} extras={extra_a}  (expect 0/0)  {'PASS' if ok_a else 'FAIL'}")
    print(f"[B] unload {target_host}:{target_model} -> drifts={drift_b} drifted={drifted}  (expect [that model])  {'PASS' if ok_b else 'FAIL'}")
    print(f"[C] host unreachable     -> UNREACHABLE flagged, not counted as drift  {'PASS' if ok_c else 'FAIL'}")
    result = ok_a and ok_b and ok_c
    print("SELFTEST", "PASS" if result else "FAIL")
    return 0 if result else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    hosts_json = None
    if "--hosts" in argv:
        hosts_json = argv[argv.index("--hosts") + 1]
    catalog = load_catalog()
    expected = expected_residency(catalog)
    actual = {}
    if hosts_json:
        with open(hosts_json) as f:
            cap = json.load(f)
        for h, ids in cap.items():
            actual[h] = set(ids)
    else:
        for h, info in host_apis(catalog).items():
            actual[h] = query_host_loaded(info.get("api", ""))
    rows, drift, extra = compare(expected, actual)
    md = render(catalog, expected, actual, rows, drift, extra)
    with open(OUT, "w") as f:
        f.write(md + "\n")
    print(f"wrote {os.path.relpath(OUT)}  drifts={drift} extras={extra}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))