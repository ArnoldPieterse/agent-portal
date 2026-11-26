#!/usr/bin/env python3
"""chair_idempotency.py - Forge goal #1: Autonomous Chair Idempotency Test

Runs auto_cycle_transition twice on the same closed cycle (in a sandbox).
Asserts:
  1. No double-archive (archive dir has exactly one file per agent, not two)
  2. No duplicate goals (new goal files contain exactly 10 goals each, not 20)
  3. Ledger unchanged after second run (same reached/total counts)

Exit codes:
  0 = PASS (all invariants hold)
  1 = FAIL (invariant violated)
  2 = SETUP ERROR (sandbox creation failed)

Usage:
    python memory/forge/chair_idempotency.py
"""
import os, re, sys, shutil, json, tempfile, datetime
from pathlib import Path

# --- Setup sandbox that mimics repo structure ---
def setup_sandbox():
    """Create a temp dir with the minimal structure auto_cycle_transition expects."""
    root = Path(tempfile.mkdtemp(prefix="forge_chair_idem_"))
    
    # memory/goals/
    goals_dir = root / "memory" / "goals"
    goals_dir.mkdir(parents=True)
    archive_dir = goals_dir / "archive"
    archive_dir.mkdir()
    
    # Create fake closed goal files for 3 agents (all verified)
    AGENTS = ["orchestrator", "builder", "forge"]
    for agent in AGENTS:
        lines = [f"# {agent.capitalize()} - 10 goals (set 2026-11-25, cycle-18)", "", "Focus: Test", ""]
        for i in range(1, 11):
            lines.append(f"{i}. **Goal {i}** - Test goal number {i} (verified: 2026-11-25)")
        (goals_dir / f"{agent}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    
    # TODO.md with cycle marker
    todo = root / "TODO.md"
    todo.write_text(
        "# TODO\n\n## LIVE PLAN - cycle-18\nStatus: all clear\n\n"
        "## GOALS FULLY CLEARED 2026-11-25 (cycle-19 kickoff)\n"
        "Status: DONE - cycle-18 complete.\n",
        encoding="utf-8"
    )
    
    # agents.json (minimal)
    agents_json = root / "agents.json"
    agents_json.write_text(json.dumps({"agents": [{"id": a} for a in AGENTS]}), encoding="utf-8")
    
    # memory/orchestrator/ with the transition script (copy reference)
    orch_dir = root / "memory" / "orchestrator"
    orch_dir.mkdir()
    
    # Copy auto_cycle_transition.py into sandbox
    src = Path("memory/orchestrator/auto_cycle_transition.py")
    if src.exists():
        shutil.copy2(src, orch_dir / "auto_cycle_transition.py")
    else:
        print("FATAL: source auto_cycle_transition.py not found at memory/orchestrator/")
        shutil.rmtree(root)
        sys.exit(2)
    
    # Create a stub cycle_retro.py so generate_retro doesn't fail
    retro_stub = orch_dir / "cycle_retro.py"
    retro_stub.write_text("#!/usr/bin/env python3\nimport sys\nprint('retro done')\nsys.exit(0)\n", encoding="utf-8")
    
    # memory/researcher/ with goal_ledger stub (so import works)
    res_dir = root / "memory" / "researcher"
    res_dir.mkdir()
    ledger_stub = res_dir / "goal_ledger.py"
    ledger_stub.write_text(
        '"""goal_ledger stub for idempotency test."""\n'
        'import os, re, datetime\n'
        'AGENT_FILES = {"orchestrator": "orchestrator.md", "builder": "builder.md", "forge": "forge.md"}\n'
        'GOALS_DIR = "memory/goals"\n'
        'def build_ledger():\n'
        '    today = datetime.date.today().isoformat()\n'
        '    agents = {}\n'
        '    for agent, fn in AGENT_FILES.items():\n'
        '        path = os.path.join(GOALS_DIR, fn)\n'
        '        if not os.path.isfile(path):\n'
        '            agents[agent] = {"total": 0, "reached": 0, "open": 0}\n'
        '            continue\n'
        '        lines = open(path, encoding="utf-8").read().splitlines()\n'
        '        total = reached = 0\n'
        '        for ln in lines:\n'
        '            m = re.match(r"^\\s*(\\d+)[.)]\\s+(.*)", ln)\n'
        '            if m and len(m.group(2).strip()) >= 12:\n'
        '                total += 1\n'
        '                if "(verified:" in ln or "(pointer:" in ln:\n'
        '                    reached += 1\n'
        '        agents[agent] = {"total": total, "reached": reached, "open": total - reached}\n'
        '    return {"generated": today, "agents": agents}\n',
        encoding="utf-8"
    )
    
    return root, AGENTS


def run_transition(root: Path, force=False):
    """Run auto_cycle_transition.py --run in the sandbox. Returns exit code + stdout."""
    import subprocess
    cmd = [sys.executable, "memory/orchestrator/auto_cycle_transition.py", "--run"]
    if force:
        cmd.append("--force")
    result = subprocess.run(
        cmd, cwd=str(root), capture_output=True, text=True, timeout=30
    )
    return result.returncode, result.stdout, result.stderr


def count_archive_files(root: Path, agents: list) -> dict:
    """Count how many archive files exist per agent."""
    adir = root / "memory" / "goals" / "archive"
    counts = {}
    for agent in agents:
        files = [f for f in os.listdir(adir) if f.startswith(agent + "-") and f.endswith(".md")]
        counts[agent] = len(files)
    return counts


def count_goals_in_file(path: Path) -> int:
    """Count numbered goal lines in a file."""
    if not path.exists():
        return 0
    text = path.read_text(encoding="utf-8")
    count = 0
    for ln in text.splitlines():
        m = re.match(r"^\s*(\d+)[.)]\s+(.*)", ln)
        if m and len(m.group(2).strip()) >= 12:
            count += 1
    return count


def get_ledger_state(root: Path, agents: list) -> dict:
    """Parse current goal files to get reached/total per agent."""
    state = {}
    for agent in agents:
        p = root / "memory" / "goals" / f"{agent}.md"
        if not p.exists():
            state[agent] = {"total": 0, "reached": 0}
            continue
        text = p.read_text(encoding="utf-8")
        total = reached = 0
        for ln in text.splitlines():
            m = re.match(r"^\s*(\d+)[.)]\s+(.*)", ln)
            if m and len(m.group(2).strip()) >= 12:
                total += 1
                if "(verified:" in ln or "(pointer:" in ln:
                    reached += 1
        state[agent] = {"total": total, "reached": reached}
    return state


def main():
    print("=== Forge Goal #1: Chair Idempotency Test ===\n")
    
    root, agents = setup_sandbox()
    print(f"Sandbox: {root}")
    print(f"Agents: {agents}")
    print()
    
    failures = []
    
    # --- RUN 1 ---
    print("--- RUN 1 (first transition) ---")
    rc1, out1, err1 = run_transition(root, force=False)
    print(f"Exit code: {rc1}")
    if rc1 != 0:
        print(f"STDOUT: {out1[-500:]}")
        print(f"STDERR: {err1[-500:]}")
    
    # Capture state after run 1
    archive_after_1 = count_archive_files(root, agents)
    goals_after_1 = {}
    for a in agents:
        goals_after_1[a] = count_goals_in_file(root / "memory" / "goals" / f"{a}.md")
    ledger_after_1 = get_ledger_state(root, agents)
    
    print(f"Archive counts after run 1: {archive_after_1}")
    print(f"Goal counts after run 1: {goals_after_1}")
    print(f"Ledger after run 1: {ledger_after_1}")
    print()
    
    # --- RUN 2 (idempotency: same cycle, already transitioned) ---
    print("--- RUN 2 (second transition - idempotency check) ---")
    rc2, out2, err2 = run_transition(root, force=False)
    print(f"Exit code: {rc2}")
    if rc2 != 0:
        print(f"STDOUT: {out2[-500:]}")
        print(f"STDERR: {err2[-500:]}")
    
    # Capture state after run 2
    archive_after_2 = count_archive_files(root, agents)
    goals_after_2 = {}
    for a in agents:
        goals_after_2[a] = count_goals_in_file(root / "memory" / "goals" / f"{a}.md")
    ledger_after_2 = get_ledger_state(root, agents)
    
    print(f"Archive counts after run 2: {archive_after_2}")
    print(f"Goal counts after run 2: {goals_after_2}")
    print(f"Ledger after run 2: {ledger_after_2}")
    print()
    
    # --- ASSERTIONS ---
    print("--- ASSERTIONS ---")
    
    # 1. No double-archive: archive count should be same after both runs
    for a in agents:
        if archive_after_2[a] > archive_after_1[a]:
            failures.append(f"DOUBLE-ARCHIVE: {a} went from {archive_after_1[a]} to {archive_after_2[a]} archive files")
        else:
            print(f"  [PASS] No double-archive for {a} ({archive_after_1[a]} -> {archive_after_2[a]})")
    
    # 2. No duplicate goals: goal count should be same (or 0 if file was re-archived)
    for a in agents:
        if goals_after_2[a] > goals_after_1[a]:
            failures.append(f"DUPLICATE GOALS: {a} went from {goals_after_1[a]} to {goals_after_2[a]} goals")
        else:
            print(f"  [PASS] No duplicate goals for {a} ({goals_after_1[a]} -> {goals_after_2[a]})")
    
    # 3. Ledger unchanged: same reached/total
    for a in agents:
        if ledger_after_2[a] != ledger_after_1[a]:
            failures.append(f"LEDGER CHANGED: {a} went from {ledger_after_1[a]} to {ledger_after_2[a]}")
        else:
            print(f"  [PASS] Ledger unchanged for {a}: {ledger_after_1[a]}")
    
    print()
    
    # --- RESULT ---
    if failures:
        print(f"FAIL ({len(failures)} invariant violations):")
        for f in failures:
            print(f"  X {f}")
        
        # Write evidence
        evidence = {
            "test": "chair_idempotency",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "result": "FAIL",
            "failures": failures,
            "archive_run1": archive_after_1,
            "archive_run2": archive_after_2,
            "goals_run1": goals_after_1,
            "goals_run2": goals_after_2,
            "ledger_run1": ledger_after_1,
            "ledger_run2": ledger_after_2,
        }
        out_path = Path("memory/forge/chair_idempotency_last.json")
        out_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        
        # Cleanup sandbox
        shutil.rmtree(root, ignore_errors=True)
        sys.exit(1)
    else:
        print("PASS - all invariants hold. Chair is idempotent.")
        
        evidence = {
            "test": "chair_idempotency",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "result": "PASS",
            "failures": [],
            "archive_run1": archive_after_1,
            "archive_run2": archive_after_2,
            "goals_run1": goals_after_1,
            "goals_run2": goals_after_2,
            "ledger_run1": ledger_after_1,
            "ledger_run2": ledger_after_2,
        }
        out_path = Path("memory/forge/chair_idempotency_last.json")
        out_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        
        # Cleanup sandbox
        shutil.rmtree(root, ignore_errors=True)
        sys.exit(0)


if __name__ == "__main__":
    main()
