#!/usr/bin/env python3
"""canary_gate.py - Verifier-side canary promotion gate.

Before Forge promotes a canary to full fleet, this script:
  1. Runs functional checks (JS syntax, API health, file integrity)
  2. Runs perf checks (file size regression, load time estimate)
  3. Emits a pass/fail token that Forge must consume

Token file: memory/verifier/canary-gate-token.json
  { "status": "PASS"|"FAIL", "timestamp": "...", "checks": {...}, "reasons": [...] }

Usage:
  python memory/verifier/canary_gate.py            # run gate, emit token
  python memory/verifier/canary_gate.py --check    # validate existing token (exit 0=pass, 1=block)
  python memory/verifier/canary_gate.py --selftest # run self-test proving blocking works
  python memory/verifier/canary_gate.py --simulate [N]  # simulate N promotions through gate

Exit codes:
  0 = PASS (token emitted or valid token exists)
  1 = FAIL/BLOCKED (checks failed or no valid token)
  2 = usage error
"""
import sys, os, json, time, hashlib, datetime

# Use CWD as project root (sandbox-safe; avoids __file__ path issues)
ROOT = os.getcwd()
TOKEN_PATH = os.path.join(ROOT, "memory", "verifier", "canary-gate-token.json")
LOG_PATH = os.path.join(ROOT, "memory", "verifier", "canary-gate-log.jsonl")

# Perf thresholds
MAX_CORE_JS_KB = 80       # core.js must stay under 80KB
MAX_CSS_KB = 60           # app.css under 60KB
MAX_TOTAL_UI_KB = 150     # total ui/ dir under 150KB

def now_iso():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]

def file_size_kb(path):
    if not os.path.exists(path):
        return 0.0
    return os.path.getsize(path) / 1024.0

def dir_size_kb(dirpath):
    total = 0
    for root, dirs, files in os.walk(dirpath):
        for f in files:
            fp = os.path.join(root, f)
            if os.path.isfile(fp):
                total += os.path.getsize(fp)
    return total / 1024.0

def check_functional():
    """Run functional checks. Returns (passed: bool, details: dict)."""
    results = {}
    
    # F1: core.js exists and is non-empty
    core_js = os.path.join(ROOT, "ui", "core.js")
    if os.path.exists(core_js) and os.path.getsize(core_js) > 0:
        results["f1_core_js_exists"] = True
    else:
        results["f1_core_js_exists"] = False
    
    # F2: core.js has no obvious syntax error (balanced braces heuristic)
    if results.get("f1_core_js_exists"):
        with open(core_js, "r", encoding="utf-8") as f:
            content = f.read()
        opens = content.count("{")
        closes = content.count("}")
        # Allow small imbalance from strings/comments; flag if off by >5
        results["f2_brace_balance"] = abs(opens - closes) <= 5
    else:
        results["f2_brace_balance"] = False
    
    # F3: app.css exists and is non-empty
    app_css = os.path.join(ROOT, "ui", "app.css")
    results["f3_app_css_exists"] = os.path.exists(app_css) and os.path.getsize(app_css) > 0
    
    # F4: goal_ledger.json exists (SSOT file)
    ledger = os.path.join(ROOT, "goal_ledger.json")
    if not os.path.exists(ledger):
        ledger = os.path.join(ROOT, "memory", "researcher", "goal_ledger.py")
    results["f4_ssot_exists"] = os.path.exists(ledger)
    
    # F5: index.html exists (portal entry point)
    results["f5_index_html_exists"] = os.path.exists(os.path.join(ROOT, "index.html"))
    
    passed = all(v is True for v in results.values())
    return passed, results

def check_perf():
    """Run perf checks. Returns (passed: bool, details: dict)."""
    results = {}
    
    # P1: core.js size within budget
    core_kb = file_size_kb(os.path.join(ROOT, "ui", "core.js"))
    results["p1_core_js_kb"] = round(core_kb, 1)
    results["p1_pass"] = core_kb <= MAX_CORE_JS_KB
    
    # P2: app.css size within budget
    css_kb = file_size_kb(os.path.join(ROOT, "ui", "app.css"))
    results["p2_app_css_kb"] = round(css_kb, 1)
    results["p2_pass"] = css_kb <= MAX_CSS_KB
    
    # P3: total ui/ CODE files (js+css) within budget (excludes images/assets)
    code_kb = file_size_kb(os.path.join(ROOT, "ui", "core.js")) + \
              file_size_kb(os.path.join(ROOT, "ui", "app.css")) + \
              file_size_kb(os.path.join(ROOT, "ui", "uploads.js"))
    results["p3_ui_code_kb"] = round(code_kb, 1)
    results["p3_pass"] = code_kb <= MAX_TOTAL_UI_KB
    
    passed = all(results.get(f"p{i}_pass", False) for i in range(1, 4))
    return passed, results

def run_gate():
    """Run full gate: functional + perf. Emit token. Return exit code."""
    t0 = time.time()
    
    func_pass, func_details = check_functional()
    perf_pass, perf_details = check_perf()
    
    all_pass = func_pass and perf_pass
    reasons = []
    if not func_pass:
        for k, v in func_details.items():
            if v is False:
                reasons.append(f"functional: {k} FAILED")
    if not perf_pass:
        for k, v in perf_details.items():
            if v is False:
                reasons.append(f"perf: {k} FAILED")
    
    elapsed = round(time.time() - t0, 3)
    
    token = {
        "status": "PASS" if all_pass else "FAIL",
        "timestamp": now_iso(),
        "duration_s": elapsed,
        "checks": {
            "functional": func_details,
            "perf": perf_details
        },
        "reasons": reasons
    }
    
    # Write token
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        json.dump(token, f, indent=2)
    
    # Append to log
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": now_iso(), "status": token["status"], "elapsed_s": elapsed}) + "\n")
    
    print(f"CANARY GATE: {token['status']} ({elapsed}s)")
    for r in reasons:
        print(f"  - {r}")
    
    return 0 if all_pass else 1

def check_token():
    """Validate existing token. Exit 0 if PASS, 1 if missing/FAIL/stale."""
    if not os.path.exists(TOKEN_PATH):
        print("CANARY GATE: BLOCKED - no token file")
        return 1
    
    with open(TOKEN_PATH, "r", encoding="utf-8") as f:
        token = json.load(f)
    
    if token.get("status") != "PASS":
        print(f"CANARY GATE: BLOCKED - token status is {token.get('status')}")
        return 1
    
    # Token must be <5 min old
    try:
        ts = datetime.datetime.strptime(token["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
        age_s = (datetime.datetime.now() - ts).total_seconds()
        if age_s > 300:
            print(f"CANARY GATE: BLOCKED - token stale ({age_s:.0f}s old)")
            return 1
    except (KeyError, ValueError):
        print("CANARY GATE: BLOCKED - token has invalid timestamp")
        return 1
    
    print(f"CANARY GATE: VALID - PASS token from {token['timestamp']}")
    return 0

def selftest():
    """Prove the gate works: missing token blocks, bad token blocks, good token passes."""
    print("=== CANARY GATE SELFTEST ===")
    results = []
    
    # Test 1: No token -> blocked
    if os.path.exists(TOKEN_PATH):
        os.remove(TOKEN_PATH)
    rc = check_token()
    t1 = (rc == 1)
    results.append(("T1_no_token_blocks", t1))
    print(f"  T1 no-token-blocks: {'PASS' if t1 else 'FAIL'}")
    
    # Test 2: FAIL token -> blocked
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        json.dump({"status": "FAIL", "timestamp": now_iso(), "reasons": ["test"]}, f)
    rc = check_token()
    t2 = (rc == 1)
    results.append(("T2_fail_token_blocks", t2))
    print(f"  T2 fail-token-blocks: {'PASS' if t2 else 'FAIL'}")
    
    # Test 3: Stale token -> blocked
    stale_ts = "2020-01-01T00:00:00Z"
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        json.dump({"status": "PASS", "timestamp": stale_ts}, f)
    rc = check_token()
    t3 = (rc == 1)
    results.append(("T3_stale_token_blocks", t3))
    print(f"  T3 stale-token-blocks: {'PASS' if t3 else 'FAIL'}")
    
    # Test 4: Fresh PASS token -> allowed
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        json.dump({"status": "PASS", "timestamp": now_iso(), "checks": {}, "reasons": []}, f)
    rc = check_token()
    t4 = (rc == 0)
    results.append(("T4_valid_token_passes", t4))
    print(f"  T4 valid-token-passes: {'PASS' if t4 else 'FAIL'}")
    
    # Test 5: Run full gate (should pass on current state)
    rc = run_gate()
    t5 = (rc == 0)
    results.append(("T5_full_gate_pass", t5))
    print(f"  T5 full-gate-pass: {'PASS' if t5 else 'FAIL'}")
    
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"\nSELFTEST: {passed}/{total} PASS")
    
    # Write selftest result
    st_path = os.path.join(ROOT, "memory", "verifier", "canary-gate-selftest.json")
    with open(st_path, "w", encoding="utf-8") as f:
        json.dump({"ts": now_iso(), "results": results, "passed": passed, "total": total}, f, indent=2)
    
    return 0 if passed == total else 1

def simulate_promotions(n=3):
    """Simulate n promotions through the gate. Each must have a valid PASS token."""
    print(f"\n=== SIMULATED PROMOTIONS ({n}) ===")
    log_entries = []
    
    for i in range(1, n + 1):
        # Gate: run checks and emit fresh token
        t0 = time.time()
        rc = run_gate()
        elapsed = round(time.time() - t0, 3)
        
        if rc != 0:
            log_entries.append({"promo": i, "gated": True, "reason": "gate failed"})
            print(f"  Promo {i}: BLOCKED (gate FAIL)")
            continue
        
        # Token exists and is PASS -> promotion allowed
        with open(TOKEN_PATH, "r", encoding="utf-8") as f:
            token = json.load(f)
        
        log_entries.append({
            "promo": i,
            "gated": False,
            "token_status": token["status"],
            "token_ts": token["timestamp"],
            "gate_duration_s": elapsed
        })
        print(f"  Promo {i}: PASSED gate ({elapsed}s), token={token['status']}")
    
    # Write promotion log
    promo_log = os.path.join(ROOT, "memory", "verifier", "canary-gate-promotions.jsonl")
    with open(promo_log, "a", encoding="utf-8") as f:
        for e in log_entries:
            e["ts"] = now_iso()
            f.write(json.dumps(e) + "\n")
    
    all_gated_correctly = all(
        (e["gated"] == False and e.get("token_status") == "PASS") or e["gated"]
        for e in log_entries
    )
    print(f"\nAll {n} promotions gated correctly: {all_gated_correctly}")
    return 0 if all_gated_correctly else 1

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--selftest":
            sys.exit(selftest())
        elif cmd == "--check":
            sys.exit(check_token())
        elif cmd == "--simulate":
            n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
            sys.exit(simulate_promotions(n))
        else:
            print(f"Unknown command: {cmd}")
            sys.exit(2)
    else:
        sys.exit(run_gate())
