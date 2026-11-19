#!/usr/bin/env python3
"""
auto_cycle_transition.py — Orchestrator's cycle lifecycle automation (cycle-5 goal #1)

WHAT IT DOES:
  * Detects when ALL agents have reached 10/10 goals (via goal_ledger parse).
  * Archives current memory/goals/<agent>.md -> memory/goals/archive/<agent>-<date>.md
  * Generates a cycle kickoff note at memory/goals/cycle<N+1>-kickoff-<date>.md
  * Updates TODO.md: strikes old "## AGENT GOALS" section, inserts new cycle header.

USAGE:
  python memory/orchestrator/auto_cycle_transition.py --check      # report status only
  python memory/orchestrator/auto_cycle_transition.py --run        # execute transition
  python memory/orchestrator/auto_cycle_transition.py --dry-run    # show what WOULD happen
"""
import os, re, sys, shutil, json, datetime, time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "researcher"))
try:
    from goal_ledger import build_ledger, AGENT_FILES, GOALS_DIR
except ImportError:
    # fallback: manual parse if module not found
    AGENT_FILES = {
        "orchestrator": "orchestrator.md", "researcher": "researcher.md",
        "builder": "builder.md", "archivist": "archivist.md",
        "scribe": "scribe.md", "verifier": "verifier.md",
        "designer": "designer.md", "mechanic": "mechanic.md",
    }
    GOALS_DIR = "memory/goals"

    def build_ledger():
        import json
        today = datetime.date.today().isoformat()
        agents = {}
        for agent, fn in AGENT_FILES.items():
            path = os.path.join(GOALS_DIR, fn)
            if not os.path.isfile(path):
                agents[agent] = {"total": 0, "reached": 0, "open": 0}
                continue
            lines = open(path, encoding="utf-8").read().splitlines()
            total = reached = 0
            for ln in lines:
                m = re.match(r"^\s*(\d+)[.)]\s+(.*)", ln)
                if m and len(m.group(2).strip()) >= 12:
                    total += 1
                    if "(verified:" in ln or "(pointer:" in ln:
                        reached += 1
            agents[agent] = {"total": total, "reached": reached, "open": total - reached}
        return {"generated": today, "agents": agents}


def repo_root():
    d = os.path.dirname(os.path.abspath(__file__))
    # memory/orchestrator/ -> two up
    root = os.path.dirname(os.path.dirname(d))
    if os.path.isdir(os.path.join(root, "memory")):
        return root
    return os.getcwd()


def get_current_cycle():
    """Extract current cycle number from TODO.md or goal files."""
    root = repo_root()
    todo_path = os.path.join(root, "TODO.md")
    if os.path.isfile(todo_path):
        txt = open(todo_path, encoding="utf-8").read()
        m = re.search(r"cycle-(\d+)", txt, re.IGNORECASE)
        if m:
            return int(m.group(1))
    # fallback: check goal file headers
    for fn in AGENT_FILES.values():
        p = os.path.join(root, GOALS_DIR, fn)
        if os.path.isfile(p):
            txt = open(p, encoding="utf-8").read()[:200]
            m = re.search(r"cycle-(\d+)", txt, re.IGNORECASE)
            if m:
                return int(m.group(1))
    return 4  # default


def check_all_closed():
    """Return (all_closed: bool, per_agent: dict, message)."""
    root = repo_root()
    ledger = build_ledger()
    agents = ledger["agents"]
    all_closed = True
    details = []
    for agent, data in sorted(agents.items()):
        total = data.get("total", 0)
        reached = data.get("reached", 0)
        open_count = data.get("open", total - reached)
        if total == 0 or open_count > 0:
            all_closed = False
        details.append(f"  {agent:<12} {reached}/{total}")
    msg = "ALL CLOSED - ready for transition" if all_closed else f"NOT READY - {sum(d.get('open',0) for d in agents.values())} goals still open"
    return all_closed, agents, msg


def archive_goals(dry_run=False):
    """Move current goal files to archive/ with date suffix. Returns list of moves."""
    root = repo_root()
    today = datetime.date.today().isoformat()
    gdir = os.path.join(root, GOALS_DIR)
    adir = os.path.join(gdir, "archive")
    if not os.path.isdir(adir):
        os.makedirs(adir)
    moves = []
    for agent, fn in sorted(AGENT_FILES.items()):
        src = os.path.join(gdir, fn)
        if not os.path.isfile(src):
            continue
        dst_name = f"{agent}-{today}.md"
        dst = os.path.join(adir, dst_name)
        # avoid overwriting existing archive (append cycle number)
        counter = 2
        while os.path.exists(dst):
            dst_name = f"{agent}-{today}_{counter}.md"
            dst = os.path.join(adir, dst_name)
            counter += 1
        if dry_run:
            moves.append(f"[DRY] {fn} -> archive/{dst_name}")
        else:
            shutil.move(src, dst)
            moves.append(f"{fn} -> archive/{dst_name}")
    return moves


def lane_arc_summary(cycle_num):
    """Per-agent arc for the closing cycle: reached/total (from the ledger SSOT),
    last goal closed, and carry-forward count. Returns list of markdown lines."""
    root = repo_root()
    gdir = os.path.join(root, GOALS_DIR)
    try:
        counts = build_ledger().get("agents", {})
    except Exception:
        counts = {}
    lines = []
    for agent in sorted(AGENT_FILES):
        fn = AGENT_FILES[agent]
        path = os.path.join(gdir, fn)
        if not os.path.isfile(path):
            lines.append(f"- **{agent}**: no goal file found")
            continue
        c = counts.get(agent, {})
        total = c.get("total", 0)
        reached = c.get("reached", 0)
        last_closed = None
        for ln in open(path, encoding="utf-8").read().splitlines():
            m = re.match(r"^\s*(\d+)[.)]\s+(.*)", ln)
            if not m or len(m.group(2).strip()) < 12:
                continue
            body = m.group(2).strip()
            title_m = re.match(r"\*\*(.+?)\*\*", body)
            title = title_m.group(1) if title_m else body[:60]
            if "(verified:" in ln:
                last_closed = title
        carry = total - reached
        arc = f"{reached}/{total} reached"
        if last_closed:
            arc += f" · last closed: {last_closed}"
        arc += f" · carries {carry}" + (" goal(s) forward" if carry != 1 else " goal forward")
        lines.append(f"- **{agent}**: {arc}")
    return lines


def generate_kickoff(cycle_num, dry_run=False):
    """Generate cycle kickoff note. Returns path."""
    root = repo_root()
    today = datetime.date.today().isoformat()
    gdir = os.path.join(root, GOALS_DIR)
    fname = f"cycle{cycle_num+1}-kickoff-{today}.md"
    path = os.path.join(gdir, fname)
    
    # Lane-arc summary for the closing cycle
    arc_lines = lane_arc_summary(cycle_num)

    # Gather carry-forward from archived files (most recent per agent)
    adir = os.path.join(gdir, "archive")
    carry_lines = []
    for agent in sorted(AGENT_FILES):
        # find most recent archive for this agent
        archives = sorted([f for f in os.listdir(adir) if f.startswith(agent + "-") and f.endswith(".md")], reverse=True)
        if archives:
            src = os.path.join(adir, archives[0])
            txt = open(src, encoding="utf-8").read()
            # find unmet goals (no verified/pointer marker)
            unmet = []
            for ln in txt.splitlines():
                m = re.match(r"^\s*(\d+)[.)]\s+(.*)", ln)
                if m and len(m.group(2).strip()) >= 12:
                    if "(verified:" not in ln and "(pointer:" not in ln:
                        unmet.append(m.group(2).strip()[:80])
            if unmet:
                carry_lines.append(f"- **{agent}**: {len(unmet)} carried forward")
                for u in unmet[:3]:
                    carry_lines.append(f"  - {u}")
    
    content = f"""# Cycle {cycle_num+1} Kickoff — {today}

## Transition Summary
- Previous cycle: **{cycle_num}** (all goals closed)
- New cycle start: {today}
- Agents: {len(AGENT_FILES)} seats active

## Lane Arcs (cycle {cycle_num})
{chr(10).join(arc_lines) if arc_lines else "- No agent goal files found"}

## Carry-Forward (unmet from previous cycle)
{chr(10).join(carry_lines) if carry_lines else "- None - all goals met"}

## Next Steps
1. Each agent proposes ~10 new goals for cycle {cycle_num+1}
2. Orchestrator collects into TODO.md `## AGENT GOALS` + memory/goals/<agent>.md
3. Ledger sweep confirms baseline (0/80 reached)
4. Auto-loop begins

---
*Generated by auto_cycle_transition.py*
"""
    if dry_run:
        print(f"[DRY] Would create: {fname}")
        print(content[:500])
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created: {fname}")
    return path


def update_todo(cycle_num, dry_run=False):
    """Update TODO.md: mark old cycle complete, add new cycle header."""
    root = repo_root()
    todo_path = os.path.join(root, "TODO.md")
    if not os.path.isfile(todo_path):
        print("WARNING: TODO.md not found, skipping update")
        return None
    
    txt = open(todo_path, encoding="utf-8").read()
    today = datetime.date.today().isoformat()
    
    # Mark the current live plan as complete
    new_header = f"## GOALS FULLY CLEARED {today} (cycle-{cycle_num+1} kickoff)"
    
    # Find and replace the "LIVE PLAN" or top section header
    lines = txt.splitlines()
    insert_at = 0
    for i, ln in enumerate(lines):
        if ln.startswith("## GOALS FULLY CLEARED") or ln.startswith("## LIVE PLAN"):
            insert_at = i
            break
    
    new_lines = [new_header]
    new_lines.append(f"Status: **DONE** - cycle-{cycle_num} complete. New cycle {cycle_num+1} goals being set.")
    new_lines.append("")
    
    if dry_run:
        print(f"[DRY] Would insert at line {insert_at}:")
        print("\n".join(new_lines[:3]))
    else:
        lines = lines[:insert_at] + new_lines + lines[insert_at:]
        with open(todo_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"Updated TODO.md (inserted at line {insert_at})")
    return todo_path


def save_roster_snapshot(cycle_num, dry_run=False):
    """Save current agents.json as a cycle snapshot for roster-diff comparisons."""
    snap_dir = os.path.join(repo_root(), "memory", "fleet", "roster-snapshots")
    if not dry_run:
        os.makedirs(snap_dir, exist_ok=True)
    agents_path = os.path.join(repo_root(), "agents.json")
    with open(agents_path, encoding="utf-8") as f:
        data = json.load(f)
    snap_file = os.path.join(snap_dir, f"cycle-{cycle_num}.json") if not dry_run else None
    if dry_run:
        print(f"  SNAPSHOT: [DRY] would save cycle-{cycle_num} roster ({len(data.get('agents', []))} agents)")
        return snap_file
    with open(snap_file, "w", encoding="utf-8") as f:
        json.dump({"cycle": cycle_num, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "agents": data.get("agents", [])}, f, indent=2)
    print(f"  SNAPSHOT: saved cycle-{cycle_num} roster ({len(data.get('agents', []))} agents)")
    return snap_file


def create_goal_files(cycle_num, dry_run=False):
    """Create empty goal file skeletons for each agent in the new cycle. Returns list of paths."""
    root = repo_root()
    gdir = os.path.join(root, GOALS_DIR)
    today = datetime.date.today().isoformat()
    created = []
    for agent, fn in sorted(AGENT_FILES.items()):
        path = os.path.join(gdir, fn)
        if os.path.exists(path) and not dry_run:
            # file already exists (shouldn't after archive), skip
            continue
        skeleton = (
            f"# {agent.capitalize()} - 10 goals (set {today}, cycle-{cycle_num+1})\n"
            f"\n"
            f"Focus: TBD\n"
            f"\n"
            f"1. **Goal 1** - (TBD)\n"
            f"2. **Goal 2** - (TBD)\n"
            f"3. **Goal 3** - (TBD)\n"
            f"4. **Goal 4** - (TBD)\n"
            f"5. **Goal 5** - (TBD)\n"
            f"6. **Goal 6** - (TBD)\n"
            f"7. **Goal 7** - (TBD)\n"
            f"8. **Goal 8** - (TBD)\n"
            f"9. **Goal 9** - (TBD)\n"
            f"10. **Goal 10** - (TBD)\n"
        )
        if dry_run:
            created.append(f"[DRY] {fn}")
        else:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(skeleton)
            created.append(fn)
    return created


def main():
    mode = "--check"
    for arg in sys.argv[1:]:
        if arg in ("--run", "--dry-run", "--check"):
            mode = arg
    
    root = repo_root()
    os.chdir(root)
    
    print(f"=== Auto Cycle Transition ===")
    print(f"Root: {root}")
    cycle = get_current_cycle()
    print(f"Current cycle: {cycle}")
    print()
    
    # Step 1: Check if all closed
    all_closed, agents, msg = check_all_closed()
    print(f"Status: {msg}")
    for a, d in sorted(agents.items()):
        t = d.get("total", 0)
        r = d.get("reached", 0)
        o = d.get("open", t - r)
        flag = "OK" if o == 0 and t > 0 else f"OPEN({o})"
        print(f"  {a:<12} {r}/{t}  [{flag}]")
    print()
    
    if not all_closed:
        print("CANNOT TRANSITION: goals still open. Use --force to override (not implemented).")
        return 1
    
    # Step 2-4: Execute transition
    print(f"Mode: {mode}")
    dry = (mode == "--dry-run")
    
    save_roster_snapshot(cycle, dry_run=dry)
    moves = archive_goals(dry_run=dry)
    for m in moves:
        print(f"  ARCHIVE: {m}")
    
    new_files = create_goal_files(cycle, dry_run=dry)
    for nf in new_files:
        print(f"  NEW GOALS: {nf}")
    
    kickoff_path = generate_kickoff(cycle, dry_run=dry)
    update_todo(cycle, dry_run=dry)
    
    print()
    if dry:
        print("[DRY-RUN COMPLETE - no files modified]")
    else:
        print(f"[TRANSITION COMPLETE] Cycle {cycle} -> {cycle+1}")
        print(f"  Kickoff: memory/goals/{os.path.basename(kickoff_path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
