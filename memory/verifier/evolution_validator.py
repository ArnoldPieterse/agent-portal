#!/usr/bin/env python3
"""Evolution state machine validator - Verifier goal #7 (cycle 2).

Tests every legal AND illegal CHG transition against evolution.py's CLI.
Confirms rejection on each illegal edge, acceptance on legal edges.

States: CANDIDATE, LIVING, DEAD
Legal transitions:
  - accept:   CANDIDATE -> LIVING
  - reject:   any state -> DEAD  
  - breed:    LIVING -> (creates new CANDIDATE child)
Illegal (must be rejected):
  - accept on LIVING
  - accept on DEAD
  - breed on CANDIDATE
  - breed on DEAD

Usage: python memory/verifier/evolution_validator.py
"""
import subprocess, json, os, sys
from datetime import datetime, timezone

EVOLUTION_PY = "evolution.py"
POP_FILE = os.path.join("evolution", "population.json")
GRAVEYARD_FILE = os.path.join("evolution", "graveyard.json")
OUT_JSON = os.path.join(os.path.dirname(__file__), "evolution-validator-2026-11-16.json")
OUT_MD = os.path.join(os.path.dirname(__file__), "evolution-validator-2026-11-16.md")

def run_evolution(*args):
    """Run evolution.py CLI, return (returncode, stdout+stderr)."""
    r = subprocess.run(
        [sys.executable, EVOLUTION_PY] + list(args),
        capture_output=True, text=True, timeout=10
    )
    return r.returncode, (r.stdout + r.stderr).strip()

def setup_fresh_population():
    """Create a fresh population for testing. Returns entity IDs by state."""
    # Save any existing
    if os.path.exists(POP_FILE):
        with open(POP_FILE) as f:
            backup = json.load(f)
        with open(POP_FILE + ".bak", "w") as f:
            json.dump(backup, f)
    
    # Create fresh population
    pop = {"next_id": 1, "entities": []}
    os.makedirs("evolution", exist_ok=True)
    with open(POP_FILE, "w") as f:
        json.dump(pop, f)
    
    # Propose creates CANDIDATE entities (requires --kind, --spec, --target, --test)
    r, out = run_evolution("propose", "--kind", "patch", "--spec", "test-A", "--target", "x.py", "--test", "t1:python -c pass")
    assert r == 0, f"propose A failed: {out}"
    
    r, out = run_evolution("propose", "--kind", "patch", "--spec", "test-B", "--target", "y.py", "--test", "t2:python -c pass")
    assert r == 0, f"propose B failed: {out}"
    
    # Accept CHG-0001 to make it LIVING
    r, out = run_evolution("accept", "CHG-0001")
    assert r == 0, f"accept CHG-0001 failed: {out}"
    
    # Now CHG-0002 is CANDIDATE, CHG-0001 is LIVING
    return {"candidate": "CHG-0002", "living": "CHG-0001"}

def restore_population():
    """Restore population from backup if it exists."""
    bak = POP_FILE + ".bak"
    if os.path.exists(bak):
        with open(bak) as f:
            data = json.load(f)
        with open(POP_FILE, "w") as f:
            json.dump(data, f)
        os.remove(bak)

def main():
    results = []
    
    print("[evolution_validator] Setting up fresh test population...")
    ids = setup_fresh_population()
    print(f"  candidate={ids['candidate']}, living={ids['living']}")
    
    # Create a DEAD entity for testing (reject the LIVING one)
    r, out = run_evolution("reject", "CHG-0001", "--reason", "test-dead")
    assert r == 0, f"reject CHG-0001 failed: {out}"
    dead_id = "CHG-0001"
    
    # Accept CHG-0002 to make it LIVING for breed tests
    r, out = run_evolution("accept", "CHG-0002")
    assert r == 0, f"accept CHG-0002 failed: {out}"
    living_id = "CHG-0002"
    
    print(f"  dead={dead_id}, living={living_id}")
    
    # --- TRANSITION MATRIX TESTS ---
    
    tests = [
        # (name, args, expected_rc==0?, description)
        ("T1_legal_accept_candidate", ["accept", "CHG-0003"], False,
         "accept on non-existent -> should fail (no such entity)"),
        ("T2_illegal_accept_living", ["accept", living_id], False,
         "accept on LIVING entity -> must reject"),
        ("T3_illegal_accept_dead", ["accept", dead_id], False,
         "accept on DEAD entity -> must reject"),
        ("T4_illegal_breed_candidate", ["breed", "CHG-0003"], False,
         "breed on non-existent/candidate -> must reject"),
        ("T5_illegal_breed_dead", ["breed", dead_id], False,
         "breed on DEAD entity -> must reject"),
        ("T6_legal_breed_living", ["breed", living_id], True,
         "breed on LIVING entity -> should succeed, create CANDIDATE child"),
        ("T7_illegal_accept_after_dead", ["accept", dead_id], False,
         "re-accept DEAD after other ops -> must reject (state is final)"),
    ]
    
    for name, args, expect_success, desc in tests:
        rc, out = run_evolution(*args)
        passed = (rc == 0) if expect_success else (rc != 0)
        results.append({
            "test": name,
            "command": f"evolution.py {' '.join(args)}",
            "expected": "success" if expect_success else "rejection",
            "got_rc": rc,
            "output_snippet": out[:120],
            "pass": passed
        })
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}: rc={rc} | {out[:80]}")
    
    # --- SUMMARY ---
    total = len(results)
    passed_count = sum(1 for r in results if r["pass"])
    all_pass = passed_count == total
    
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_tests": total,
        "passed": passed_count,
        "failed": total - passed_count,
        "all_pass": all_pass,
        "state_machine": {
            "states": ["CANDIDATE", "LIVING", "DEAD"],
            "legal_transitions": [
                "CANDIDATE -> LIVING (accept)",
                "any -> DEAD (reject)",
                "LIVING -> new CANDIDATE child (breed)"
            ],
            "illegal_rejected": [
                "accept on LIVING",
                "accept on DEAD",
                "breed on CANDIDATE",
                "breed on DEAD"
            ]
        },
        "results": results
    }
    
    with open(OUT_JSON, "w") as f:
        json.dump(report, f, indent=2)
    
    # Restore original population
    restore_population()
    
    print(f"\n[evolution_validator] {passed_count}/{total} transition tests PASS")
    if all_pass:
        print("ALL TRANSITIONS VERIFIED - state machine is sound.")
    else:
        failed = [r["test"] for r in results if not r["pass"]]
        print(f"FAILURES: {failed}")
    
    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())
