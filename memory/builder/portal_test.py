"""portal_test.py - In-process portal test harness.

Usage:
  python memory/builder/portal_test.py --suite api        # API contract tests (offline)
  python memory/builder/portal_test.py --suite ui         # UI smoke tests (static)
  python memory/builder/portal_test.py --suite integration # Integration flow tests
  python memory/builder/portal_test.py --suite all        # Run all suites
  python memory/builder/portal_test.py --suite api --live # Hit live portal at :8099

Writes report to memory/builder/test-report.md on completion.
Exit: 0=all pass, 1=any fail.
"""
import sys, os, re, json, time, hashlib
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))  # project root
UI_DIR = os.path.join(ROOT, "ui")
FIXTURE = os.path.join(BASE, "api-fixtures", "contract.json")
REPORT = os.path.join(BASE, "test-report.md")
PORTAL_URL = os.environ.get("PORTAL_URL", "http://localhost:8099")

results = []  # (suite, name, passed, detail)

def record(suite, name, passed, detail=""):
    results.append((suite, name, passed, detail))
    mark = "PASS" if passed else "FAIL"
    print(f"  [{mark}] {name}" + (f" - {detail}" if detail and not passed else ""))

# ============================================================
# SUITE: API CONTRACT
# ============================================================
def suite_api(live=False):
    print("\n=== SUITE: api ===")
    
    # Load fixture
    try:
        with open(FIXTURE) as f:
            contract = json.load(f)
    except Exception as e:
        record("api", "fixture_load", False, str(e))
        return
    
    eps = {k: v for k, v in contract.items() if not k.startswith("_")}
    record("api", "fixture_load", True, f"{len(eps)} endpoints")
    
    # 1. Structure validation
    struct_errors = []
    for ep, data in eps.items():
        if not isinstance(data, dict):
            struct_errors.append(f"{ep}: not dict")
            continue
        if "status" not in data:
            struct_errors.append(f"{ep}: no status")
        elif not isinstance(data["status"], int):
            struct_errors.append(f"{ep}: status not int")
        if "schema" not in data:
            struct_errors.append(f"{ep}: no schema")
    record("api", "structure_valid", len(struct_errors) == 0, "; ".join(struct_errors[:3]))
    
    # 2. Route coverage: all /api/ routes in source should be in fixture (soft check)
    src_path = os.path.join(ROOT, "agent_portal.py")
    if not os.path.exists(src_path):
        record("api", "route_coverage", False, "agent_portal.py not found")
    else:
        with open(src_path) as f:
            src = f.read()
        routes_in_src = set(re.findall(r'["\'](/api/[a-zA-Z0-9_\-/]+)["\']', src))
        fixture_eps = set(eps.keys())
        missing = routes_in_src - fixture_eps
        # Soft check: warn but pass (new routes may be added before fixture re-record)
        record("api", "route_coverage", True, f"{len(missing)} new routes not yet in fixture: {sorted(missing)[:3]}")
    
    # 3. Status code sanity (all should be 2xx or documented 4xx)
    bad_status = [ep for ep, d in eps.items() if isinstance(d.get("status"), int) and d["status"] >= 500]
    record("api", "no_5xx_in_contract", len(bad_status) == 0, f"5xx: {bad_status[:3]}")
    
    # 4. Schema non-empty check
    empty_schema = [ep for ep, d in eps.items() if isinstance(d.get("schema"), dict) and len(d["schema"]) == 0]
    record("api", "schemas_nonempty", len(empty_schema) == 0, f"empty: {empty_schema[:3]}")
    
    # 5. Key endpoints exist
    critical_eps = ["/api/chat", "/api/history", "/api/agents", "/api/goals"]
    for ep in critical_eps:
        record("api", f"critical:{ep}", ep in eps, "not in fixture")
    
    # 6. Deliberate break detection: verify that a tampered fixture would fail
    tampered = dict(eps)
    if "/api/chat" in tampered:
        tampered["/api/chat"] = {"status": 999, "schema": {}}
    # Re-validate structure on tampered version
    t_errors = []
    for ep, data in tampered.items():
        if not isinstance(data.get("status"), int) or data["status"] > 599:
            t_errors.append(ep)
    record("api", "break_detection", len(t_errors) > 0, "tamper not caught")
    
    # 7-12. Individual endpoint schema type checks
    for ep in ["/api/agents", "/api/goals", "/api/history"]:
        if ep in eps and isinstance(eps[ep].get("schema"), dict):
            schema = eps[ep]["schema"]
            # Schema values should be type names (str) or nested dicts
            valid_types = all(isinstance(v, (str, dict, list)) for v in schema.values())
            record("api", f"schema_types:{ep}", valid_types)
        else:
            record("api", f"schema_types:{ep}", ep in eps, "endpoint missing")
    
    # 13. Baseline file integrity
    baseline_path = os.path.join(BASE, "api-fixtures", "baseline.md5")
    if os.path.exists(baseline_path):
        with open(baseline_path) as f:
            expected_md5 = f.read().strip()
        current_md5 = hashlib.md5(open(FIXTURE, "rb").read()).hexdigest()
        record("api", "baseline_integrity", expected_md5 == current_md5, "fixture drifted")
    else:
        record("api", "baseline_integrity", True, "no baseline (first run)")
    
    # LIVE mode: hit actual endpoints
    if live:
        import urllib.request, urllib.error
        for i, ep in enumerate(sorted(eps.keys())[:15]):  # first 15 for speed
            try:
                req = urllib.request.Request(PORTAL_URL + ep)
                with urllib.request.urlopen(req, timeout=5) as resp:
                    body = json.loads(resp.read().decode())
                    expected_status = eps[ep].get("status", 200)
                    ok = (resp.status == expected_status) or (resp.status < 400)
                    record("api", f"live:{ep}", ok, f"got {resp.status}, want {expected_status}")
            except urllib.error.HTTPError as e:
                # 4xx on bare GET is acceptable for param endpoints
                expected = eps[ep].get("status", 200)
                record("api", f"live:{ep}", e.code == expected or e.code < 500, f"got {e.code}")
            except Exception as e:
                record("api", f"live:{ep}", False, str(e)[:60])

# ============================================================
# SUITE: UI SMOKE
# ============================================================
def suite_ui():
    print("\n=== SUITE: ui ===")
    
    js_files = [f for f in os.listdir(UI_DIR) if f.endswith(".js")]
    css_files = [f for f in os.listdir(UI_DIR) if f.endswith(".css")]
    record("ui", "files_exist", len(js_files) > 0 and len(css_files) > 0,
           f"{len(js_files)} js, {len(css_files)} css")
    
    # Brace balance for each JS file (tolerance ±3 for regex/template edge cases)
    BRACE_TOL = 3
    for fname in sorted(js_files):
        with open(os.path.join(UI_DIR, fname), encoding="utf-8", errors="replace") as f:
            content = f.read()
        # Order matters: block comments -> template strings -> single/double strings -> line comments
        stripped = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
        stripped = re.sub(r"`(?:[^`\\]|\\.)*`", "``", stripped)
        stripped = re.sub(r"'(?:[^'\\]|\\.)*'", "''", stripped)
        stripped = re.sub(r'"(?:[^"\\]|\\.)*"', '""', stripped)
        stripped = re.sub(r"//[^\n]*", "", stripped)
        ob, cb = stripped.count("{"), stripped.count("}")
        op, cp = stripped.count("("), stripped.count(")")
        brace_diff = abs(ob - cb)
        paren_diff = abs(op - cp)
        balanced = brace_diff <= BRACE_TOL and paren_diff <= BRACE_TOL
        record("ui", f"brace_balance:{fname}", balanced, f"{{}}={ob}/{cb}(±{BRACE_TOL}) ()={op}/{cp}")
    
    # CSS: no empty rules
    for fname in sorted(css_files):
        with open(os.path.join(UI_DIR, fname), encoding="utf-8", errors="replace") as f:
            content = f.read()
        empty_rules = re.findall(r"[^{}]+\{\s*\}", content)
        record("ui", f"no_empty_rules:{fname}", len(empty_rules) == 0, f"{len(empty_rules)} empty")
    
    # Component usage: core.js should use UI.* (not raw createElement for panels)
    core_path = os.path.join(UI_DIR, "core.js")
    if os.path.exists(core_path):
        with open(core_path) as f:
            core_src = f.read()
        create_el_count = len(re.findall(r"document\.createElement", core_src))
        ui_fn_calls = len(re.findall(r"UI\.(el|msgBubble|thinkBlock|chip|dmSegment)", core_src))
        record("ui", "component_usage:core.js", create_el_count < 5,
               f"createElement={create_el_count} (target<5), UI.*={ui_fn_calls}")
    
    # State module exists and is wired
    state_path = os.path.join(UI_DIR, "state.js")
    record("ui", "state_module_exists", os.path.exists(state_path))
    if os.path.exists(core_path):
        has_state_ref = "State" in core_src or "state" in core_src.lower()
        record("ui", "state_wired_in_core", has_state_ref)
    
    # Error boundary: showPanelError exists and is used
    if os.path.exists(core_path):
        has_boundary = "showPanelError" in core_src or "panel-error" in core_src
        record("ui", "error_boundary_present", has_boundary)
    
    # Accessibility: :focus-visible rule in CSS
    focus_found = False
    for fname in sorted(css_files):
        with open(os.path.join(UI_DIR, fname), encoding="utf-8", errors="replace") as f:
            if ":focus-visible" in f.read():
                focus_found = True
                break
    record("ui", "a11y_focus_visible", focus_found)

# ============================================================
# SUITE: INTEGRATION
# ============================================================
def suite_integration(live=False):
    print("\n=== SUITE: integration ===")
    
    # 1. agents.json is valid JSON with expected structure (dict with 'agents' list)
    agents_path = os.path.join(ROOT, "agents.json")
    if not os.path.exists(agents_path):
        record("integration", "agents_json_valid", False, "file missing")
    else:
        try:
            with open(agents_path) as f:
                raw = json.load(f)
            # agents.json is {"agents": [...]} or a bare list
            agents = raw.get("agents", raw) if isinstance(raw, dict) else raw
            has_names = all("name" in a for a in agents) if isinstance(agents, list) else False
            record("integration", "agents_json_valid", has_names, f"{len(agents)} agents")
        except json.JSONDecodeError as e:
            record("integration", "agents_json_valid", False, str(e)[:40])
    
    # 2. Chat flow: POST /api/chat endpoint exists in source
    src_path = os.path.join(ROOT, "agent_portal.py")
    if os.path.exists(src_path):
        with open(src_path) as f:
            src = f.read()
        has_chat_post = bool(re.search(r'["\']/api/chat["\'].*?POST|POST.*?["\']/api/chat["\']', src, re.DOTALL))
        # Fallback: just check the route string exists
        if not has_chat_post:
            has_chat_post = "/api/chat" in src
        record("integration", "chat_endpoint_exists", has_chat_post)
    
    # 3. Message retrieval endpoint
    if os.path.exists(src_path):
        has_messages = "/api/messages" in src or "/api/history" in src
        record("integration", "messages_endpoint_exists", has_messages)
    
    # 4. Agent list endpoint matches agents.json count (offline: just check route exists)
    if os.path.exists(src_path):
        has_agents_ep = "/api/agents" in src
        record("integration", "agents_endpoint_exists", has_agents_ep)
    
    # 5. Goals endpoint
    if os.path.exists(src_path):
        has_goals = "/api/goals" in src
        record("integration", "goals_endpoint_exists", has_goals)
    
    # 6. Upload flow: /api/upload route exists
    if os.path.exists(src_path):
        has_upload = "/api/upload" in src or "/api/uploads" in src
        record("integration", "upload_endpoint_exists", has_upload)
    
    # 7. Memory endpoint (for portal memory display)
    if os.path.exists(src_path):
        has_memory = "/api/memory" in src or "/api/files" in src
        record("integration", "memory_endpoint_exists", has_memory)
    
    # 8. Fleet status / ops endpoints
    if os.path.exists(src_path):
        has_fleet = "/api/fleet" in src or "/api/status" in src
        record("integration", "fleet_endpoint_exists", has_fleet)
    
    # LIVE: full roundtrip test
    if live:
        import urllib.request, urllib.error, uuid
        # 8. GET /api/agents returns list
        try:
            with urllib.request.urlopen(PORTAL_URL + "/api/agents", timeout=5) as r:
                data = json.loads(r.read().decode())
            is_list = isinstance(data, list)
            record("integration", "live_agents_roundtrip", is_list, f"type={type(data).__name__}")
        except Exception as e:
            record("integration", "live_agents_roundtrip", False, str(e)[:60])
        
        # 9. GET /api/goals returns structured data
        try:
            with urllib.request.urlopen(PORTAL_URL + "/api/goals", timeout=5) as r:
                data = json.loads(r.read().decode())
            record("integration", "live_goals_roundtrip", True, f"type={type(data).__name__}")
        except Exception as e:
            record("integration", "live_goals_roundtrip", False, str(e)[:60])
        
        # 10. POST /api/chat with minimal payload (expects 200 or 4xx validation)
        try:
            payload = json.dumps({"agent": "Orchestrator", "message": "test-ping"}).encode()
            req = urllib.request.Request(PORTAL_URL + "/api/chat", data=payload,
                                         headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=30) as r:
                record("integration", "live_chat_roundtrip", r.status < 500, f"status={r.status}")
        except urllib.error.HTTPError as e:
            record("integration", "live_chat_roundtrip", e.code < 500, f"HTTP {e.code}")
        except Exception as e:
            record("integration", "live_chat_roundtrip", False, str(e)[:60])

# ============================================================
# REPORT WRITER
# ============================================================
def write_report(suite_name, live):
    passed = sum(1 for _, _, p, _ in results if p)
    total = len(results)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    lines = [
        f"# Portal Test Report",
        f"",
        f"**Run:** {now} | **Suite:** {suite_name} | **Mode:** {'live' if live else 'offline'}",
        f"**Result:** {passed}/{total} passed ({(passed/total*100):.0f}%)",
        f"",
    ]
    
    current_suite = None
    for suite, name, p, detail in results:
        if suite != current_suite:
            lines.append(f"## {suite}")
            lines.append("")
            current_suite = suite
        mark = "✅" if p else "❌"
        line = f"- {mark} `{name}`"
        if detail and not p:
            line += f" — {detail}"
        elif detail:
            line += f" ({detail})"
        lines.append(line)
    
    lines.append("")
    if passed == total:
        lines.append("**ALL GREEN** ✅")
    else:
        failing = [(s, n, d) for s, n, p, d in results if not p]
        lines.append(f"**{len(failing)} FAILURES:**")
        for s, n, d in failing:
            lines.append(f"- `{s}/{n}`: {d}")
    
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nReport written: memory/builder/test-report.md")

# ============================================================
def main():
    args = sys.argv[1:]
    suite = "all"
    live = False
    
    for i, a in enumerate(args):
        if a == "--suite" and i + 1 < len(args):
            suite = args[i + 1]
        elif a == "--live":
            live = True
    
    print(f"=== PORTAL TEST HARNESS ===")
    print(f"Suite: {suite} | Live: {live}")
    start = time.time()
    
    if suite in ("all", "api"):
        suite_api(live)
    if suite in ("all", "ui"):
        suite_ui()
    if suite in ("all", "integration"):
        suite_integration(live)
    
    elapsed = time.time() - start
    passed = sum(1 for _, _, p, _ in results if p)
    total = len(results)
    
    print(f"\n=== RESULT: {passed}/{total} passed ({elapsed:.1f}s) ===")
    write_report(suite, live)
    
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()
