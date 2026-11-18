# -*- coding: utf-8 -*-
"""Smoke Test Suite v2 - Verifier Goal #1 (cycle-5)
Covers: all /api/* endpoints, UI panel DOM nodes, file integrity.
Usage: python memory/verifier/smoke8.py [--static] [--live] [--timeout 5]
Exit codes: 0=all pass, 1=one or more failures
"""
import argparse, json, os, re, sys, time, urllib.request

BASE_URL = "http://localhost:8099"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

def get_json(path, timeout=5):
    try:
        with urllib.request.urlopen(BASE_URL + path, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"_error": str(e)}

def check_agents_json():
    results = []
    p = "agents.json"
    if not os.path.exists(p):
        results.append(("agents.json exists", False, "not found"))
        return results
    try:
        d = json.load(open(p))
        ok = isinstance(d, dict) and "agents" in d
        results.append(("agents.json valid JSON with agents key", ok, "" if ok else str(type(d))))
        agents = d.get("agents", [])
        names = [a.get("name") for a in (agents if isinstance(agents, list) else agents.values())]
        results.append(("agents.json has agent entries", len(names) > 0, "%d agents" % len(names)))
    except Exception as e:
        results.append(("agents.json parses", False, str(e)))
    return results

def check_goal_files():
    results = []
    gdir = "memory/goals"
    if not os.path.isdir(gdir):
        results.append(("memory/goals/ exists", False, "not found"))
        return results
    results.append(("memory/goals/ exists", True, ""))
    agents = [f for f in os.listdir(gdir) if re.match(r"^[a-z]+\.md$", f)]
    results.append(("goal files present (>=5)", len(agents) >= 5, "%d found: %s" % (len(agents), ",".join(sorted(agents)))))
    bad = []
    for f in agents:
        txt = open(os.path.join(gdir, f), encoding="utf-8").read()
        if not re.search(r"^#\s", txt, re.M):
            bad.append(f)
    results.append(("all goal files have H1 header", len(bad) == 0, ",".join(bad) if bad else ""))
    return results

def check_ui_panels():
    results = []
    p = "index.html"
    if not os.path.exists(p):
        results.append(("index.html exists", False, "not found"))
        return results
    html = open(p, encoding="utf-8").read()
    results.append(("index.html exists and non-empty", len(html) > 100, "%d bytes" % len(html)))
    # Check for core DOM elements the portal UI depends on
    expected_ids = ["composer", "msgs", "status", "send"]
    all_ids = set()
    for m in re.finditer(r"id=[\"']([a-z][a-z0-9-]*)[\"']", html):
        all_ids.add(m.group(1))
    missing = [e for e in expected_ids if e not in all_ids]
    results.append(("core DOM elements present (%s)" % ",".join(expected_ids), len(missing) == 0, "missing: %s" % ",".join(missing) if missing else "%d ids total" % len(all_ids)))
    # Check that UI JS files exist and are non-empty
    ui_dir = "ui"
    js_files = []
    if os.path.isdir(ui_dir):
        js_files = [f for f in os.listdir(ui_dir) if f.endswith(".js") or f.endswith(".css")]
    empty = [f for f in js_files if os.path.getsize(os.path.join(ui_dir, f)) == 0]
    results.append(("ui/ directory with non-empty assets", len(js_files) >= 1 and not empty, "%d files%s" % (len(js_files), ", EMPTY: %s" % ",".join(empty) if empty else "")))
    # Check JS syntax (basic: balanced braces)
    js_bad = []
    for f in js_files:
        if f.endswith(".js"):
            txt = open(os.path.join(ui_dir, f), encoding="utf-8").read()
            if txt.count("{") != txt.count("}"):
                js_bad.append("%s({%d vs }%d)" % (f, txt.count("{"), txt.count("}")))
    results.append(("JS files have balanced braces", len(js_bad) == 0, "; ".join(js_bad[:3])))
    return results

def check_api_endpoints(timeout=5):
    results = []
    src = open("agent_portal.py", encoding="utf-8").read()
    endpoints = sorted(set(re.findall(r"['\"](/api/[a-z0-9/_-]+)['\"]", src)))
    endpoints = [e for e in endpoints if not e.endswith("/")]
    results.append(("discovered %d /api/ endpoints" % len(endpoints), True, ",".join(endpoints[:5]) + "..."))
    pass_c, fail_c = 0, 0
    for ep in endpoints:
        data = get_json(ep, timeout)
        if "_error" in data:
            fail_c += 1
            results.append((ep, False, data["_error"][:60]))
        else:
            pass_c += 1
    results.append(("API endpoints returning valid JSON: %d/%d" % (pass_c, len(endpoints)), fail_c == 0, "%d failed" % fail_c))
    return results

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--static", action="store_true", help="File/DOM checks only")
    ap.add_argument("--live", action="store_true", help="Include API endpoint tests")
    ap.add_argument("--timeout", type=int, default=5)
    args = ap.parse_args()
    live = args.live or not args.static
    t0 = time.time()
    all_results = []
    print("[1/3] File integrity checks...")
    all_results += check_agents_json()
    all_results += check_goal_files()
    print("[2/3] UI panel checks...")
    all_results += check_ui_panels()
    if live:
        print("[3/3] API endpoint checks (live)...")
        probe = get_json("/api/goals", args.timeout)
        if "_error" in probe:
            print("  [SKIP] Portal unreachable: %s" % probe["_error"][:50])
            all_results.append(("portal reachable", False, "static-only mode (portal down)"))
        else:
            all_results += check_api_endpoints(args.timeout)
    else:
        print("[3/3] API endpoint checks: SKIPPED (static mode)")
    elapsed = time.time() - t0
    passed = sum(1 for _, ok, _ in all_results if ok)
    failed = sum(1 for _, ok, _ in all_results if not ok)
    print("")
    print("=" * 60)
    print("SMOKE8 RESULTS: %d pass / %d fail / %d total (%.1fs)" % (passed, failed, len(all_results), elapsed))
    for name, ok, detail in all_results:
        mark = "PASS" if ok else "FAIL"
        line = "  [%s] %s" % (mark, name)
        if detail and not ok:
            line += " -- %s" % detail
        print(line)
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
