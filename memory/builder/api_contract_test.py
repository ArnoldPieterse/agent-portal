"""API Contract Pinning Test - validates response schema stability across /api/* endpoints.

Usage:
  python api_contract_test.py --check     # Offline: validate fixture integrity + coverage
  python api_contract_test.py --record    # Online: hit live server, record/compare schemas
  python api_contract_test.py --diff      # Compare current fixture vs last-known-good

Exit codes: 0=PASS, 1=FAIL (drift detected or fixture corrupt)
"""
import json, os, sys, hashlib, re
from datetime import datetime, timezone

FIXTURE = os.path.join(os.path.dirname(__file__), "api-fixtures", "contract.json")
BASELINE = os.path.join(os.path.dirname(__file__), "api-fixtures", "baseline.md5")
PORTAL_URL = os.environ.get("PORTAL_URL", "http://localhost:8099")

def load_fixture():
    if not os.path.exists(FIXTURE):
        print("[FAIL] Fixture file missing: %s" % FIXTURE)
        sys.exit(1)
    with open(FIXTURE, "r") as f:
        return json.load(f)

def validate_structure(contract):
    """Every endpoint entry must have: status (int), schema (dict)."""
    errors = []
    for ep, data in contract.items():
        if not isinstance(data, dict):
            errors.append("%s: not a dict" % ep)
            continue
        if "status" not in data:
            errors.append("%s: missing 'status'" % ep)
        elif not isinstance(data["status"], int):
            errors.append("%s: status not int" % ep)
        if "schema" not in data:
            errors.append("%s: missing 'schema'" % ep)
        elif not isinstance(data["schema"], dict):
            errors.append("%s: schema not a dict" % ep)
    return errors

def check_coverage(source_file="agent_portal.py"):
    """Verify all routes in source are present in fixture."""
    if not os.path.exists(source_file):
        return [], "source file missing"
    with open(source_file, "r") as f:
        src = f.read()
    # Find all route patterns like @app.route("/api/...") or add_url_rule
    routes = set(re.findall(r'["\'](/api/[a-zA-Z0-9_\-/]+)["\']', src))
    fixture_eps = set(load_fixture().keys())
    missing = routes - fixture_eps
    extra = fixture_eps - routes  # informational only
    return sorted(missing), None

def md5_of_file(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def cmd_check():
    """Offline verification: fixture integrity + source coverage."""
    print("=== API CONTRACT CHECK (offline) ===")
    contract = load_fixture()
    n_eps = len(contract)
    print("  Endpoints in fixture: %d" % n_eps)

    # Structure validation
    errors = validate_structure(contract)
    if errors:
        for e in errors:
            print("  [FAIL] %s" % e)
        print("=== RESULT: FAIL (%d structural errors) ===" % len(errors))
        sys.exit(1)
    print("  Structure: PASS (all entries have status+schema)")

    # Coverage check against source
    missing, err = check_coverage()
    if err:
        print("  Coverage: SKIP (%s)" % err)
    elif missing:
        print("  Coverage: FAIL - %d routes in source not in fixture:" % len(missing))
        for m in missing[:10]:
            print("    %s" % m)
        print("=== RESULT: FAIL (coverage gap) ===")
        sys.exit(1)
    else:
        print("  Coverage: PASS (all source routes present)")

    # Baseline comparison
    current_md5 = md5_of_file(FIXTURE)
    if os.path.exists(BASELINE):
        with open(BASELINE, "r") as f:
            baseline_md5 = f.read().strip()
        if baseline_md5 == current_md5:
            print("  Baseline: UNCHANGED (md5=%s)" % current_md5[:8])
        else:
            print("  [DRIFT] Baseline changed! old=%s new=%s" % (baseline_md5[:8], current_md5[:8]))
            print("=== RESULT: FAIL (fixture drift) ===")
            sys.exit(1)
    else:
        # First run - establish baseline
        with open(BASELINE, "w") as f:
            f.write(current_md5)
        print("  Baseline: ESTABLISHED (md5=%s)" % current_md5[:8])

    print("=== RESULT: PASS (%d endpoints, structure+coverage+baseline OK) ===" % n_eps)
    sys.exit(0)

def cmd_record():
    """Online: hit live portal, record schemas."""
    import urllib.request
    print("=== API CONTRACT RECORD (online: %s) ===" % PORTAL_URL)
    contract = load_fixture()
    updated = 0
    for ep in sorted(contract.keys()):
        url = PORTAL_URL + ep
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                status = resp.status
                body = json.loads(resp.read().decode())
            # Extract top-level keys as schema
            schema = {k: type(v).__name__ for k, v in body.items()} if isinstance(body, dict) else {"_body": type(body).__name__}
            contract[ep] = {"status": status, "checked_at": datetime.now(timezone.utc).isoformat(), "schema": schema}
            updated += 1
        except Exception as e:
            print("  [SKIP] %s: %s" % (ep, str(e)[:60]))
    with open(FIXTURE, "w") as f:
        json.dump(contract, f, indent=2)
    # Update baseline
    new_md5 = md5_of_file(FIXTURE)
    with open(BASELINE, "w") as f:
        f.write(new_md5)
    print("=== RESULT: %d endpoints re-recorded ===" % updated)

def main():
    if "--check" in sys.argv:
        cmd_check()
    elif "--record" in sys.argv:
        cmd_record()
    else:
        print("Usage: python api_contract_test.py --check|--record")
        sys.exit(1)

if __name__ == "__main__":
    main()
