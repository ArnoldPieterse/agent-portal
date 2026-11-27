"""E2E test for milestone_trigger.py (isolated via MILESTATE_* env overrides).

Proves the auto-draft fires on BOTH trigger types and that --on-change is idempotent,
WITHOUT touching live fleet state. Re-runnable: python memory/outlet/test_milestone_trigger.py
"""
import json, os, tempfile, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRIGGER = HERE / "milestone_trigger.py"
PY = sys.executable or "python"

def run(env_extra):
    env = dict(os.environ)
    env.update(env_extra)
    r = subprocess.run([PY, str(TRIGGER), "--on-change"], capture_output=True, text=True, env=env)
    return r.returncode, (r.stdout + r.stderr).strip()

def write(path, obj):
    Path(path).write_text(json.dumps(obj), encoding="utf-8")

def touch(path):
    # ensure mtime strictly advances past any prior read
    t = time.time() + 1.0
    os.utime(path, (t, t))

def main():
    tmp = tempfile.mkdtemp(prefix="milestone_e2e_")
    levels = Path(tmp) / "levels.json"
    ledger = Path(tmp) / "ledger.json"
    queue = Path(tmp) / "queue"; queue.mkdir()
    state = Path(tmp) / "state.json"
    env = {"MILESTATE_LEVELS": str(levels), "MILESTATE_LEDGER": str(ledger),
           "MILESTATE_QUEUE": str(queue), "MILESTATE_STATE": str(state)}

    base_level = {"level": 10, "history": []}
    base_ledger = {"fleet_pct_reached": 98}
    write(levels, base_level); write(ledger, base_ledger)
    write(state, {"last_level": 10, "last_pct_bucket": 90})

    results = []

    # Phase A: first poll sees changed sources (no watermark yet) -> runs logic, no
    # crossing -> "No trigger" + writes watermark (no draft). Second poll with no source
    # rewrite -> genuine skip. Both must produce zero drafts.
    rc1, out1 = run(env)
    rc2, out2 = run(env)
    drafts_a = [f for f in queue.iterdir() if f.is_file()]
    okA = (rc1 == 0 and rc2 == 0 and len(drafts_a) == 0
           and "no trigger" in out1.lower()
           and ("no source change" in out2 or "skipping" in out2.lower()))
    results.append(("A_first_poll_no_cross", okA, out1.splitlines()[0] if out1 else ""))
    results.append(("A2_unchanged_skip", okA and ("no source change" in out2 or "skipping" in out2.lower()), out2.splitlines()[-1] if out2 else ""))

    # Phase B: pct crosses 90 -> 100 bucket (advance ledger mtime)
    write(ledger, {"fleet_pct_reached": 100}); touch(ledger); time.sleep(0.05)
    rc, out = run(env)
    drafts_b = [f for f in queue.iterdir() if f.is_file()]
    okB = rc == 0 and len(drafts_b) == 1 and "pct-threshold" in out
    results.append(("B_pct_threshold_fire", okB, (drafts_b[0].name if drafts_b else "") + " | " + out.splitlines()[0]))

    # Phase C: level bumps 10 -> 11 (advance levels mtime)
    write(levels, {"level": 11, "history": []}); touch(levels); time.sleep(0.05)
    rc, out = run(env)
    drafts_c = [f for f in queue.iterdir() if f.is_file()]
    okC = rc == 0 and len(drafts_c) == 2 and "level-up" in out
    results.append(("C_levelup_fire", okC, (drafts_c[-1].name if drafts_c else "") + " | " + out.splitlines()[0]))

    # Phase D: run again with NO change -> skip, still 2 drafts
    rc, out = run(env)
    drafts_d = [f for f in queue.iterdir() if f.is_file()]
    okD = rc == 0 and len(drafts_d) == 2 and ("no source change" in out or "skipping" in out.lower())
    results.append(("D_idempotent_no_dup", okD, str(len(drafts_d)) + " drafts | " + out.splitlines()[-1]))

    # Show a sample drafted body
    sample = drafts_c[0].read_text(encoding="utf-8") if drafts_c else ""

    print("=" * 60)
    for name, ok, detail in results:
        print(("PASS" if ok else "FAIL"), name, "->", detail)
    print("-" * 60)
    print("SAMPLE DRAFT:\n" + sample.strip())
    all_ok = all(r[1] for r in results)
    # cleanup temp (keep project tidy); evidence leaf records the result
    import shutil; shutil.rmtree(tmp, ignore_errors=True)
    print("=" * 60)
    print("E2E", "ALL PASS" if all_ok else "FAILED")
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
