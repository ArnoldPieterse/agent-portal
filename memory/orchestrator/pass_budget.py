#!/usr/bin/env python3
"""Pass Budget Tracker (orchestrator goal #5).

Commands:
  init [--budget N]   Create/reset pass-budget.json
  increment           Add one consumed pass
  check               Print status; if exhausted, force fleet-mode to IDLE
  test                Run synthetic verification tests
"""
import json, os, sys, time, argparse
HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUDGET_FILE = os.path.join(HERE, "memory", "ops", "pass-budget.json")
MODE_FILE = os.path.join(HERE, "memory", "ops", "fleet-mode.json")

def _load():
    if os.path.exists(BUDGET_FILE):
        with open(BUDGET_FILE) as f: return json.load(f)
    return {"budget": 200, "consumed": 0, "cycle": "15", "updated": None}

def _save(d):
    d["updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    os.makedirs(os.path.dirname(BUDGET_FILE), exist_ok=True)
    with open(BUDGET_FILE, "w") as f: json.dump(d, f, indent=2)

def _force_idle(reason):
    if not os.path.exists(MODE_FILE): return
    with open(MODE_FILE) as f: fm = json.load(f)
    fm["mode"] = "IDLE"
    fm["reason"] = reason
    fm["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
    with open(MODE_FILE, "w") as f: json.dump(fm, f, indent=2)

def cmd_init(args):
    d = {"budget": args.budget, "consumed": 0, "cycle": "15",
         "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    _save(d)
    print(json.dumps(d, indent=2))

def cmd_increment(args):
    d = _load(); d["consumed"] += 1; _save(d)
    exhausted = d["consumed"] >= d["budget"]
    print(json.dumps({"consumed": d["consumed"], "budget": d["budget"], "exhausted": exhausted}))
    if exhausted: _force_idle("pass budget exhausted")

def cmd_check(args):
    d = _load(); remaining = d["budget"] - d["consumed"]
    out = {"consumed": d["consumed"], "budget": d["budget"], "remaining": remaining,
           "exhausted": remaining <= 0, "dispatch_work": remaining > 0}
    print(json.dumps(out))
    if remaining <= 0: _force_idle("pass budget exhausted")

def cmd_test(args):
    import shutil, tempfile
    # Use temp files to not pollute real state
    tmp = tempfile.mkdtemp()
    global BUDGET_FILE, MODE_FILE
    saved_b, saved_m = BUDGET_FILE, MODE_FILE
    BUDGET_FILE = os.path.join(tmp, "pass-budget.json")
    MODE_FILE = os.path.join(tmp, "fleet-mode.json")
    # Create a fake fleet-mode file
    with open(MODE_FILE, "w") as f:
        json.dump({"mode": "WORK", "timestamp": "2026-11-24T00:00:00+00:00"}, f)
    results = []
    # Test 1: init and increment
    _save({"budget": 5, "consumed": 0, "cycle": "test", "updated": None})
    d = _load()
    assert d["consumed"] == 0, "init consumed should be 0"
    for i in range(3): d["consumed"] += 1; _save(d)
    d = _load()
    results.append(("increment tracks correctly (3/5)", d["consumed"] == 3))
    # Test 2: at budget, dispatch_work=False
    d["consumed"] = 5; _save(d)
    d = _load(); remaining = d["budget"] - d["consumed"]
    results.append(("at budget: exhausted=True", remaining <= 0))
    results.append(("at budget: dispatch_work=False", remaining > 0 == False))
    # Test 3: force idle
    _force_idle("test")
    with open(MODE_FILE) as f: fm = json.load(f)
    results.append(("mode forced to IDLE", fm["mode"] == "IDLE"))
    # Cleanup
    BUDGET_FILE, MODE_FILE = saved_b, saved_m
    shutil.rmtree(tmp, ignore_errors=True)
    print("=== Pass Budget - Synthetic Test ===")
    for name, ok in results: print(f"  {name}: {'PASS' if ok else 'FAIL'}")
    all_ok = all(r[1] for r in results)
    print(f"ALL TESTS PASS ({sum(r[1] for r in results)}/{len(results)})" if all_ok else "SOME TESTS FAILED")
    return 0 if all_ok else 1

def main():
    ap = argparse.ArgumentParser(description="Pass budget tracker")
    sub = ap.add_subparsers(dest="cmd")
    s1 = sub.add_parser("init"); s1.add_argument("--budget", type=int, default=200)
    sub.add_parser("increment"); sub.add_parser("check"); sub.add_parser("test")
    args = ap.parse_args()
    if args.cmd == "init": cmd_init(args)
    elif args.cmd == "increment": cmd_increment(args)
    elif args.cmd == "check": cmd_check(args)
    elif args.cmd == "test": sys.exit(cmd_test(args))
    else: ap.print_help()
if __name__ == "__main__": main()
