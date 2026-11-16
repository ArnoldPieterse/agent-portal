#!/usr/bin/env python3
"""builder/evolution_fitness_test.py - Goal 4: Evolution fitness integration.

Wires test suites as scoring functions in evolution.py's cmd_score.
Acceptance: one cycle where a passing variant -> VALIDATED and a failing variant -> GRAVEYARD.

Usage: python memory/builder/evolution_fitness_test.py
"""
import json, os, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
EVO_HOME = os.path.join(ROOT, "evolution")

PASS = 0
FAIL = 0

def check(name, cond, detail=""):
    global PASS, FAIL
    mark = "PASS" if cond else "FAIL"
    print(f"  [{mark}] {name}" + (f"  -> {detail}" if detail and not cond else ""))
    if cond: PASS += 1
    else: FAIL += 1


def main():
    global PASS, FAIL
    os.environ["EVOLUTION_HOME"] = EVO_HOME

    # --- Setup: create two CANDIDATE entities in a temp evolution home ---
    tmp_home = tempfile.mkdtemp(prefix="evo_fitness_")
    pop_file = os.path.join(tmp_home, "population.json")
    grave_file = os.path.join(tmp_home, "graveyard.json")

    pop = {"entities": [
        {
            "id": "FIT-PASS-001",
            "status": "CANDIDATE",
            "description": "Variant with all-passing tests",
            "tests": [
                {"name": "trivial_pass", "command": 'python -c "exit(0)"'},
                {"name": "gate_check", "command": 'python memory/builder/pre_commit_gate.py'},
            ]
        },
        {
            "id": "FIT-FAIL-001",
            "status": "CANDIDATE",
            "description": "Variant with a failing test",
            "tests": [
                {"name": "trivial_pass", "command": 'python -c "exit(0)"'},
                {"name": "deliberate_fail", "command": 'python -c "exit(1)"'},
            ]
        },
    ]}
    with open(pop_file, "w") as f:
        json.dump(pop, f)
    with open(grave_file, "w") as f:
        json.dump({"entities": []}, f)

    # --- Run evolution.py score against temp home ---
    env = dict(os.environ, EVOLUTION_HOME=tmp_home)
    result = subprocess.run(
        [sys.executable, os.path.join(ROOT, "evolution.py"), "score"],
        capture_output=True, text=True, timeout=120,
        cwd=ROOT, env=env
    )
    print(f"  evolution.py score output (tail):")
    for line in result.stdout.strip().split('\n')[-15:]:
        print(f"    {line}")
    if result.stderr:
        print(f"  stderr: {result.stderr[-300:]}")

    check("score command exited cleanly", result.returncode == 0, f"rc={result.returncode}")

    # --- Verify outcomes ---
    with open(pop_file) as f:
        pop_after = json.load(f)

    by_id = {e["id"]: e for e in pop_after["entities"]}

    pass_ent = by_id.get("FIT-PASS-001")
    fail_ent = by_id.get("FIT-FAIL-001")

    check("passing variant -> VALIDATED",
          pass_ent and pass_ent["status"] == "VALIDATED",
          f"got {pass_ent['status'] if pass_ent else 'MISSING'}")

    check("failing variant -> GRAVEYARD",
          fail_ent and fail_ent["status"] == "GRAVEYARD",
          f"got {fail_ent['status'] if fail_ent else 'MISSING'}")

    # Verify graveyard received the failing entity
    with open(grave_file) as f:
        grave_after = json.load(f)
    grave_ids = [e["id"] for e in grave_after.get("entities", [])]
    check("graveyard contains FIT-FAIL-001", "FIT-FAIL-001" in grave_ids, f"ids={grave_ids}")

    # Verify score details recorded
    check("passing variant has score.all_passed=True",
          pass_ent and pass_ent.get("score", {}).get("all_passed") is True)

    check("failing variant has reject_reason",
          fail_ent and bool(fail_ent.get("reject_reason")),
          f"reason={fail_ent.get('reject_reason') if fail_ent else 'N/A'}")

    # --- Cleanup ---
    import shutil
    shutil.rmtree(tmp_home, ignore_errors=True)

    print(f"\n=== EVOLUTION FITNESS TEST: {PASS}/{PASS+FAIL} PASS ===")
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()