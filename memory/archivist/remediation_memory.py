#!/usr/bin/env python3
"""archivist/remediation_memory.py - Remediation Outcome Memory (learning loop).
After each auto-remediation executes, record a structured outcome and maintain
a per-action success-rate model so a fix that fails repeatedly is demoted in
ranking.

Record format (JSONL): {situation_hash, action, outcome, timestamp}
Model: per-action {total, successes, failures, partials, rate}

CLI:
  python memory/archivist/remediation_memory.py --record <action> <outcome> [--situation "..."]
  python memory/archivist/remediation_memory.py --model
  python memory/archivist/remediation_memory.py --selftest
"""
import json, os, re, sys, hashlib
from datetime import datetime, timezone

ARCH = os.path.dirname(os.path.abspath(__file__))
RECORDS_FILE = os.path.join(ARCH, "remediation-outcomes.jsonl")
MODEL_FILE = os.path.join(ARCH, "remediation-model.json")

def situation_hash(situation):
    """Deterministic hash of a situation description."""
    return hashlib.sha256(situation.strip().lower().encode()).hexdigest()[:16]

def record_outcome(action, outcome, situation=""):
    """Record a remediation outcome. Idempotent: same situation+action won't double-count."""
    assert outcome in ("success", "fail", "partial"), f"outcome must be success|fail|partial, got {outcome!r}"
    sh = situation_hash(situation) if situation else ""
    entry = {
        "situation_hash": sh,
        "action": action.strip(),
        "outcome": outcome,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    # Idempotency check: if same situation_hash + action already recorded, skip
    existing = _load_records()
    for e in existing:
        if e["situation_hash"] == sh and e["action"] == action.strip():
            return {"status": "duplicate", "entry": entry}
    with open(RECORDS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    # Rebuild model
    rebuild_model()
    return {"status": "recorded", "entry": entry}

def _load_records():
    if not os.path.exists(RECORDS_FILE):
        return []
    records = []
    with open(RECORDS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records

def rebuild_model():
    """Rebuild the per-action success-rate model from all records."""
    records = _load_records()
    actions = {}
    for r in records:
        a = r["action"]
        if a not in actions:
            actions[a] = {"total": 0, "successes": 0, "failures": 0, "partials": 0}
        actions[a]["total"] += 1
        o = r["outcome"]
        if o == "success":
            actions[a]["successes"] += 1
        elif o == "fail":
            actions[a]["failures"] += 1
        else:
            actions[a]["partials"] += 1
    # Compute rates
    for a, stats in actions.items():
        stats["rate"] = round(stats["successes"] / stats["total"], 4) if stats["total"] > 0 else 0.0
    model = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_records": len(records),
        "actions": actions
    }
    with open(MODEL_FILE, "w", encoding="utf-8") as f:
        json.dump(model, f, indent=2)
    return model

def get_model():
    """Return the current success-rate model."""
    if os.path.exists(MODEL_FILE):
        with open(MODEL_FILE, encoding="utf-8") as f:
            return json.load(f)
    return rebuild_model()

def rank_actions(model=None):
    """Rank actions by success rate (desc), then by total count (desc) for ties."""
    if model is None:
        model = get_model()
    items = [(a, s["rate"], s["total"]) for a, s in model["actions"].items()]
    items.sort(key=lambda x: (-x[1], -x[2], x[0]))
    return [{"action": a, "rate": r, "total": t} for a, r, t in items]

def selftest():
    """Verify: 10 seeded outcomes produce correct rates; fail-3x < success-2x; idempotent."""
    import tempfile, shutil
    print("=== remediation_memory.py selftest ===")
    
    # Use temp files to avoid polluting real data
    global RECORDS_FILE, MODEL_FILE
    orig_records, orig_model = RECORDS_FILE, MODEL_FILE
    test_dir = os.path.join(ARCH, "_test_rm")
    os.makedirs(test_dir, exist_ok=True)
    RECORDS_FILE = os.path.join(test_dir, "outcomes.jsonl")
    MODEL_FILE = os.path.join(test_dir, "model.json")
    # Clean
    for f in (RECORDS_FILE, MODEL_FILE):
        if os.path.exists(f): os.remove(f)
    
    try:
        # Seed 10 outcomes: action_A succeeds 2x, fails 3x; action_B succeeds 5x
        seeds = [
            ("fix-dangling-pointers", "success", "sit-1"),
            ("fix-dangling-pointers", "success", "sit-2"),
            ("fix-dangling-pointers", "fail", "sit-3"),
            ("fix-dangling-pointers", "fail", "sit-4"),
            ("fix-dangling-pointers", "fail", "sit-5"),
            ("rebuild-index", "success", "sit-6"),
            ("rebuild-index", "success", "sit-7"),
            ("rebuild-index", "success", "sit-8"),
            ("rebuild-index", "success", "sit-9"),
            ("rebuild-index", "success", "sit-10"),
        ]
        for action, outcome, sit in seeds:
            r = record_outcome(action, outcome, situation=sit)
            assert r["status"] == "recorded", f"Expected recorded, got {r['status']}"
        
        model = get_model()
        print(f"  Records: {model['total_records']}")
        
        # Check rates
        a_rate = model["actions"]["fix-dangling-pointers"]["rate"]
        b_rate = model["actions"]["rebuild-index"]["rate"]
        print(f"  fix-dangling-pointers rate: {a_rate} (expect 0.4)")
        print(f"  rebuild-index rate: {b_rate} (expect 1.0)")
        assert abs(a_rate - 0.4) < 0.01, f"Rate mismatch: {a_rate}"
        assert abs(b_rate - 1.0) < 0.01, f"Rate mismatch: {b_rate}"
        
        # Check ranking: fail-3x (rate 0.4) must rank below success-5x (rate 1.0)
        ranked = rank_actions(model)
        print(f"  Ranking: {[(r['action'], r['rate']) for r in ranked]}")
        assert ranked[0]["action"] == "rebuild-index", "Highest-rate action should rank first"
        assert ranked[1]["action"] == "fix-dangling-pointers", "Lower-rate action should rank second"
        
        # Idempotency: re-record same situation+action
        r_dup = record_outcome("fix-dangling-pointers", "success", situation="sit-1")
        assert r_dup["status"] == "duplicate", f"Expected duplicate, got {r_dup['status']}"
        model2 = get_model()
        assert model2["total_records"] == 10, f"Should still be 10 records, got {model2['total_records']}"
        print(f"  Idempotency: PASS (duplicate detected, count stays at 10)")
        
        # Write report
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        report_path = os.path.join(ARCH, f"remediation-memory-{date_str}.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# Remediation Memory Report - {date_str}\n\n")
            f.write(f"Total records: {model['total_records']}\n\n")
            f.write("## Per-Action Success Rates\n\n")
            f.write(f"| Action | Total | Success | Fail | Partial | Rate |\n")
            f.write(f"|--------|-------|---------|------|---------|------|\n")
            for a, s in sorted(model["actions"].items()):
                f.write(f"| {a} | {s['total']} | {s['successes']} | {s['failures']} | {s['partials']} | {s['rate']:.2f} |\n")
            f.write(f"\n## Ranking (by success rate)\n\n")
            for i, r in enumerate(ranked, 1):
                f.write(f"{i}. {r['action']} (rate={r['rate']:.2f}, n={r['total']})\n")
        print(f"  Report: {report_path}")
        
        # Write selftest JSON
        st = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_records": model["total_records"],
            "actions": model["actions"],
            "ranking": ranked,
            "idempotency_pass": True,
            "rate_check_pass": True,
            "all_pass": True
        }
        st_path = os.path.join(ARCH, "remediation-memory-selftest.json")
        with open(st_path, "w", encoding="utf-8") as f:
            json.dump(st, f, indent=2)
        print(f"  Selftest JSON: {st_path}")
        print("  ALL TESTS PASS")
    finally:
        RECORDS_FILE, MODEL_FILE = orig_records, orig_model
        shutil.rmtree(test_dir, ignore_errors=True)

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    elif "--record" in sys.argv:
        i = sys.argv.index("--record")
        action = sys.argv[i+1]
        outcome = sys.argv[i+2]
        situation = ""
        if "--situation" in sys.argv:
            situation = sys.argv[sys.argv.index("--situation")+1]
        r = record_outcome(action, outcome, situation)
        print(json.dumps(r, indent=2))
    elif "--model" in sys.argv:
        m = get_model()
        print(json.dumps(m, indent=2))
    else:
        print("Usage: python remediation_memory.py [--selftest | --record <action> <outcome> | --model]")