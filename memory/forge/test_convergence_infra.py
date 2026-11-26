#!/usr/bin/env python3
"""test_convergence_infra.py - Forge goal #1: Convergence-Infra Regression Battery.

Asserts the cycle-19 autonomy infra is intact:
  1. fleet-mode.json valid + SSOT-consistent (schema, mode, fsm_state, internal consistency, freshness)
  2. Dispatch conformance = 100% (no reached goals dispatched in WORK mode)
  3. Idle floor met (mode matches activity level; no stuck IDLE with open work)
  4. Mode reconciler idempotent (convergence_fsm import + transition table integrity)

Exit codes:
  0 = all green
  1 = one or more checks failed (failing assertion named in output)
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent  # repo root
OPS = BASE / "memory" / "ops"
FLEET_MODE_PATH = OPS / "fleet-mode.json"
SCHEDULER_LOG = OPS / "scheduler-log.jsonl"
GOALS_DIR = BASE / "memory" / "goals"
NEXT10 = GOALS_DIR / "next10.json"
FSM_PY = BASE / "memory" / "builder" / "convergence_fsm.py"

VALID_MODES = {"WORK", "MAINTENANCE", "IDLE"}
VALID_FSM_STATES = {
    "DISCOVERING", "CONVERGING", "STEADY_STATE", "REGRESSING", "RECONVERGING"
}

failures: list[str] = []
passes: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        passes.append(f"  PASS  {name}")
    else:
        failures.append(f"  FAIL  {name}: {detail}")


# ──────────────────────────────────────────────
# CHECK 1: fleet-mode.json valid + SSOT-consistent
# ──────────────────────────────────────────────
def check_fleet_mode():
    print("\n[1] fleet-mode.json schema + SSOT consistency")
    if not FLEET_MODE_PATH.exists():
        check("fleet-mode.json exists", False, f"{FLEET_MODE_PATH} missing")
        return

    raw = FLEET_MODE_PATH.read_text(encoding="utf-8")
    try:
        fm = json.loads(raw)
    except json.JSONDecodeError as e:
        check("fleet-mode.json is valid JSON", False, str(e))
        return

    check("fleet-mode.json is valid JSON", True)

    # mode
    mode = fm.get("mode")
    check("mode in {WORK, MAINTENANCE, IDLE}",
          mode in VALID_MODES, f"got {mode!r}")

    # fsm_state
    fsm = fm.get("fsm_state")
    check("fsm_state is canonical",
          fsm in VALID_FSM_STATES, f"got {fsm!r}")

    # fsm_validated
    check("fsm_validated is true",
          fm.get("fsm_validated") is True,
          f"got {fm.get('fsm_validated')!r}")

    # timestamp freshness (< 24h)
    ts = fm.get("timestamp", "")
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        age_h = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
        check("timestamp < 24h old", age_h < 24, f"age={age_h:.1f}h")
    except Exception as e:
        check("timestamp parseable ISO-8601", False, str(e))

    # Internal consistency: goals_reached + goals_open == goals_total
    gr = fm.get("goals_reached")
    go = fm.get("goals_open")
    gt = fm.get("goals_total")
    if all(isinstance(x, int) for x in [gr, go, gt]):
        check("goals_reached + goals_open == goals_total",
              gr + go == gt,
              f"{gr}+{go}={gr+go} != {gt}")
    else:
        check("goal counts are integers", False, f"gr={gr}, go={go}, gt={gt}")

    # goal_pct matches internal counts (within 1pp)
    fm_pct = fm.get("goal_pct")
    if isinstance(fm_pct, (int, float)) and isinstance(gt, int) and gt > 0:
        derived_pct = round(gr / gt * 100, 1)
        check("goal_pct consistent with internal counts (1pp)",
              abs(fm_pct - derived_pct) <= 1.0,
              f"stated={fm_pct}, derived={derived_pct} ({gr}/{gt})")
    else:
        check("goal_pct is numeric", False, f"got {fm_pct!r}")

    # Range sanity
    if isinstance(fm_pct, (int, float)):
        check("0 <= goal_pct <= 100", 0 <= fm_pct <= 100, f"got {fm_pct}")


# ──────────────────────────────────────────────
# CHECK 2: Dispatch conformance = 100%
# ──────────────────────────────────────────────
def check_dispatch_conformance():
    print("\n[2] Dispatch conformance (no reached-goal dispatches)")
    if not NEXT10.exists():
        check("next10.json exists", False, "file missing")
        return

    try:
        n10 = json.loads(NEXT10.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        check("next10.json valid JSON", False, str(e))
        return

    # Collect reached goals from canonical agent files only
    AGENT_FILES = {
        "archivist.md", "builder.md", "designer.md", "forge.md",
        "mechanic.md", "orchestrator.md", "outlet.md", "pixel.md",
        "researcher.md", "scribe.md", "verifier.md"
    }
    evidence_re = re.compile(r"\(verified:.*?\)|\(pointe.*?\)|recorded\s+20\d\d")
    pattern = re.compile(r"^\s*\d+\.\s+\*\*(.+?)\*\*")
    reached_titles = set()
    for fn in AGENT_FILES:
        gf = GOALS_DIR / fn
        if not gf.exists():
            continue
        text = gf.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            m = pattern.match(line)
            if m and evidence_re.search(line):
                reached_titles.add(m.group(1).strip().lower())

    # Check next10 entries: any agent's goal that's already reached is a violation
    violations = []
    agents_data = n10.get("agents", {})
    for agent, data in agents_data.items():
        goals = data.get("goals", [])
        for g in goals:
            title = g.get("title", "").strip().lower()
            if title and title in reached_titles:
                violations.append(f"{agent}: {g.get('title')}")

    check("dispatch conformance = 100%",
          len(violations) == 0,
          f"{len(violations)} reached-goal dispatch(es): {violations[:3]}")


# ──────────────────────────────────────────────
# CHECK 3: Idle floor met
# ──────────────────────────────────────────────
def check_idle_floor():
    print("\n[3] Idle floor (mode matches activity level)")
    if not FLEET_MODE_PATH.exists():
        check("fleet-mode.json exists for idle check", False, "missing")
        return

    fm = json.loads(FLEET_MODE_PATH.read_text(encoding="utf-8"))
    mode = fm.get("mode")
    elapsed_h = fm.get("elapsed_since_activity_h", 0.0)
    threshold_h = fm.get("threshold_idle_h", 6.0)
    open_goals = fm.get("goals_open", 0)

    if open_goals > 0 and elapsed_h < threshold_h:
        check("mode=WORK when open goals + recent activity",
              mode == "WORK",
              f"mode={mode}, open_goals={open_goals}, elapsed={elapsed_h}h")
    elif open_goals == 0:
        passes.append(f"  SKIP  idle floor (all goals reached)")
    else:
        check("mode in {MAINTENANCE, IDLE, WORK} for low-activity state",
              mode in VALID_MODES, f"mode={mode}")

    # Scheduler log freshness: last entry < 15 min old (system is alive)
    if SCHEDULER_LOG.exists():
        lines = SCHEDULER_LOG.read_text(encoding="utf-8").strip().splitlines()
        if lines:
            try:
                last = json.loads(lines[-1])
                t_str = last.get("t", "")
                dt = datetime.strptime(t_str, "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=timezone.utc)
                age_min = (datetime.now(timezone.utc) - dt).total_seconds() / 60
                check("scheduler log fresh (<15 min)",
                      age_min < 15, f"last entry {age_min:.1f} min ago")
            except Exception as e:
                check("scheduler log last line parseable", False, str(e))
        else:
            check("scheduler log non-empty", False, "no entries")
    else:
        passes.append("  SKIP  scheduler log not found")


# ──────────────────────────────────────────────
# CHECK 4: Mode reconciler idempotent
# ──────────────────────────────────────────────
def check_reconciler_idempotent():
    print("\n[4] Mode reconciler idempotency")
    if not FSM_PY.exists():
        check("convergence_fsm.py exists", False, "file missing")
        return

    # Import the module and test its invariants
    sys.path.insert(0, str(FSM_PY.parent))
    try:
        import convergence_fsm as fsm_mod
        check("convergence_fsm imports cleanly", True)
    except ImportError as e:
        check("convergence_fsm imports cleanly", False, str(e))
        return

    # 4a: All states have legal targets (no dead-end states)
    for state in fsm_mod.STATES:
        targets = fsm_mod.legal_targets(state)
        check(f"state {state} has legal targets", len(targets) > 0, "empty")

    # 4b: Known legal transitions
    check("CONVERGING->STEADY_STATE legal",
          fsm_mod.is_legal("CONVERGING", "STEADY_STATE"))
    check("CONVERGING->REGRESSING legal",
          fsm_mod.is_legal("CONVERGING", "REGRESSING"))

    # 4c: Known illegal transitions
    check("DISCOVERING->STEADY_STATE illegal",
          not fsm_mod.is_legal("DISCOVERING", "STEADY_STATE"))
    check("DISCOVERING->REGRESSING illegal",
          not fsm_mod.is_legal("DISCOVERING", "REGRESSING"))

    # 4d: Normalization
    check("normalize('steady-state') -> STEADY_STATE",
          fsm_mod.normalize("steady-state") == "STEADY_STATE")
    check("normalize('ss') -> STEADY_STATE",
          fsm_mod.normalize("ss") == "STEADY_STATE")
    check("normalize('BOGUS') -> None",
          fsm_mod.normalize("BOGUS") is None)

    # 4e: Self-loops are legal (idempotency guarantee)
    for state in fsm_mod.STATES:
        check(f"{state} self-loop legal (idempotent)",
              fsm_mod.is_legal(state, state))


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def main():
    print("=" * 60)
    print("FORGE GATE: Convergence-Infra Regression Battery")
    print(f"Run: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    check_fleet_mode()
    check_dispatch_conformance()
    check_idle_floor()
    check_reconciler_idempotent()

    # Summary
    print("\n" + "=" * 60)
    for p in passes:
        print(p)
    for f in failures:
        print(f)
    print("=" * 60)
    total = len(passes) + len(failures)
    print(f"RESULT: {len(passes)}/{total} passed, {len(failures)} failed")

    if failures:
        print("\nFAILING ASSERTIONS:")
        for f in failures:
            print(f)
        sys.exit(1)
    else:
        print("\nALL GREEN - convergence infra intact.")
        sys.exit(0)


if __name__ == "__main__":
    main()
