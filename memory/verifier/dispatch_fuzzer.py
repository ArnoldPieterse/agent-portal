#!/usr/bin/env python3
"""dispatch_fuzzer.py - Fuzz the canonical dispatch filter (cycle-15 verifier G4).

100 random configs (agent x open/reached goals x mode) through
memory/orchestrator/dispatch_filter.dispatch(). Asserts on EVERY config:
  * no REACHED goal title ever appears in the dispatch text
  * MAINTENANCE/IDLE with all goals reached -> output is exactly that role's
    daily task from memory/ops/idle-maintenance-rotation-2026-11-24.md
  * open goals present -> kind "goal" and every open title IS listed
Selftest: python dispatch_fuzzer.py [--seed N]
"""
import importlib.util, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, *rel.split("/")))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def main():
    seed = 1500
    for i in range(1, len(sys.argv)):
        if sys.argv[i] == "--seed" and i + 1 < len(sys.argv):
            seed = int(sys.argv[i + 1])
    rng = random.Random(seed)
    df = _load("dispatch_filter", "memory/orchestrator/dispatch_filter.py")
    table = df.rotation_table(force=True)
    assert table, "rotation table missing/empty - cannot fuzz"
    roles = list(table.keys())
    N = 100
    for trial in range(1, N + 1):
        role = rng.choice(roles)
        n_open = rng.randint(0, 6)
        n_reached = rng.randint(0, 6)
        mode = rng.choice(["WORK", "MAINTENANCE", "IDLE", None])
        queued = rng.random() < 0.1
        open_goals = [f"OPEN-{role.upper()}-{trial}-{j}" for j in range(n_open)]
        reached_goals = [f"REACHED-{role.upper()}-{trial}-{j}" for j in range(n_reached)]
        wday = rng.randint(0, 4)
        out = df.dispatch(role, open_goals=open_goals, reached_goals=reached_goals,
                          mode=mode, queued=queued, wday=wday)
        text = out["text"]
        # invariant 1: no reached goal ever surfaces
        for g in reached_goals:
            assert g not in text, f"trial {trial}: REACHED goal leaked into dispatch: {g}"
        if queued:
            assert out["kind"] == "queued", f"trial {trial}: queued must win, got {out['kind']}"
        elif n_open > 0:
            assert out["kind"] == "goal", f"trial {trial}: open goals present, got {out['kind']}"
            for g in open_goals:   # every OPEN goal is listed
                assert g in text, f"trial {trial}: open goal missing from dispatch: {g}"
        else:
            mu = str(mode or "").upper()
            expect_rot = df.rotation_task(role, wday=wday)
            if mu in ("MAINTENANCE", "IDLE") and expect_rot:
                assert out["kind"] == "maintenance", f"trial {trial}: expected maintenance, got {out['kind']}"
                assert expect_rot in text, f"trial {trial}: rotation task not in output: {expect_rot!r}"
            else:
                assert out["kind"] == "generic", f"trial {trial}: expected generic, got {out['kind']}"
    print(f"SELFTEST OK ({N} random configs, seed={seed}, roles={len(roles)}: "
          f"no reached-goal leakage; goal lists exact; MAINT/IDLE match rotation table)")

if __name__ == "__main__":
    sys.exit(main())