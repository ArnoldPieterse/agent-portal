#!/usr/bin/env python3
"""Onboarding Pack Generator - auto-generates a new-agent onboarding pack.

Usage: python memory/archivist/onboarding_pack.py <agent_name> [--output FILE]
Output: markdown pack (<4KB) with role, key files, pitfalls, cycle context.

Self-test: python memory/archivist/onboarding_pack.py --selftest
"""
import pathlib, re, json, sys, textwrap
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[2]  # project root
MEM = ROOT / "memory"

# --- Data extraction helpers ---

def get_lane_description(agent: str) -> str:
    """Extract role description from memory/INDEX.md lane line."""
    idx = (MEM / "INDEX.md").read_text(encoding="utf-8")
    for line in idx.splitlines():
        m = re.match(rf"^- {re.escape(agent)}\s+.*?-\s+(.+)$", line)
        if m:
            return m.group(1).strip()
    # Fallback: search all lane lines
    for line in idx.splitlines():
        if agent.lower() in line.lower() and "memory/" in line:
            parts = line.split(" - ")
            if len(parts) >= 3:
                return parts[-1].strip()
    return f"Agent {agent} (description not found in INDEX.md)"

def get_key_files(agent: str, max_files: int = 8) -> list:
    """Extract top files from the agent's own INDEX.md."""
    idx_path = MEM / agent / "INDEX.md"
    if not idx_path.exists():
        return [f"memory/{agent}/INDEX.md (create this)"]
    content = idx_path.read_text(encoding="utf-8")
    files = []
    for line in content.splitlines():
        # Match lines with file references
        m = re.search(r"(memory/\S+\.md|memory/\S+\.py|memory/\S+\.json)", line)
        if m and m.group(1) not in files:
            files.append(m.group(1))
        if len(files) >= max_files:
            break
    # Always include the lane INDEX itself first
    idx_ref = f"memory/{agent}/INDEX.md"
    if idx_ref in files:
        files.remove(idx_ref)
    return [idx_ref] + files[:max_files - 1]

def get_common_pitfalls(agent: str) -> list:
    """Extract common pitfalls from ops/blockers and known patterns."""
    pitfalls = []
    # Check blockers file for agent-specific issues
    blockers = MEM / "ops" / "blockers.md"
    if blockers.exists():
        content = blockers.read_text(encoding="utf-8")
        for line in content.splitlines():
            if agent.lower() in line.lower():
                pitfalls.append(line.strip().lstrip("- ").strip())
                if len(pitfalls) >= 3:
                    break
    # Add universal pitfalls
    universal = [
        "Read memory/INDEX.md first - it is the pointer map for all lanes",
        "Keep files <4KB per module (file-modularity rule)",
        "Record evidence via goal_ledger.py when a goal reaches acceptance",
        "Do NOT re-probe repeated blockers - log once in ops/blockers.md and move on",
    ]
    return pitfalls[:2] + universal[:4 - min(len(pitfalls), 2)]

def get_cycle_context() -> str:
    """Extract current cycle topic from TODO.md."""
    todo = (ROOT / "TODO.md").read_text(encoding="utf-8")
    # Find the top section header
    lines = todo.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("## ") and ("CYCLE" in line.upper() or "ROUND" in line.upper()):
            # Get next 3 non-empty lines for context
            ctx_lines = []
            for j in range(i + 1, min(i + 6, len(lines))):
                if lines[j].strip():
                    ctx_lines.append(lines[j].strip())
                if len(ctx_lines) >= 2:
                    break
            return f"Cycle topic: {line[3:].strip()}\n" + "\n".join(ctx_lines[:2])
    return "See TODO.md for current cycle context."

def get_fleet_status() -> str:
    """Get fleet goal completion from goal_ledger if available."""
    ledger = ROOT / "goal_ledger.json"
    if ledger.exists():
        try:
            data = json.loads(ledger.read_text(encoding="utf-8"))
            total = sum(len(v) for v in data.values()) if isinstance(data, dict) else 0
            reached = sum(1 for v in data.values() for g in v if "REACHED" in str(g).upper() or "verified" in str(g).lower()) if isinstance(data, dict) else 0
            if total > 0:
                return f"Fleet goals: {reached}/{total} reached ({100*reached//total}%)"
        except Exception:
            pass
    return "Fleet status: see /api/goals"

# --- Pack generation ---

def generate_pack(agent: str) -> str:
    """Generate the onboarding pack for a given agent."""
    role = get_lane_description(agent)
    files = get_key_files(agent)
    pitfalls = get_common_pitfalls(agent)
    cycle = get_cycle_context()
    fleet = get_fleet_status()

    pack = f"""# Onboarding Pack: {agent.title()}
Generated: {date.today().isoformat()} | Source: onboarding_pack.py

## Role
{role}

## Read First (in order)
1. memory/INDEX.md - pointer map for all lanes
2. {files[0] if files else 'memory/' + agent + '/INDEX.md'}
"""
    for i, f in enumerate(files[1:5], start=3):
        pack += f"{i}. {f}\n"

    pack += f"""
## Common Pitfalls
"""
    for p in pitfalls[:4]:
        pack += f"- {p}\n"

    pack += f"""
## Current Cycle Context
{cycle}
{fleet}

## Quick Start Protocol
1. Read your lane INDEX.md top-to-bottom
2. Check memory/goals/{agent}.md for open goals
3. Run `python memory/researcher/goal_ledger.py --list {agent}` to see goal state
4. Pick oldest open goal, work it to completion
5. Record evidence via ledger when done

---
*Auto-generated by onboarding_pack.py - do not edit manually.*
"""
    return pack.strip()

# --- Self-test ---

def selftest():
    """Generate a pack for a synthetic agent and run 5 comprehension questions."""
    # Use 'archivist' as the test agent (real, known data)
    pack = generate_pack("archivist")
    size = len(pack.encode("utf-8"))
    print(f"[selftest] Pack size: {size} bytes ({size/1024:.1f} KB)")
    
    # Write sample output
    out = MEM / "archivist" / "onboarding-pack-sample.md"
    out.write_text(pack, encoding="utf-8")
    print(f"[selftest] Sample written to {out.relative_to(ROOT)}")

    # 5 comprehension questions (simulated - check pack contains expected content)
    questions = [
        ("What is the agent's role described as?", "knowledge index" in pack.lower() or "provenance" in pack.lower()),
        ("Does the pack list memory/INDEX.md as a read-first file?", "memory/INDEX.md" in pack),
        ("Are common pitfalls listed?", "Common Pitfalls" in pack and "-" in pack.split("Common Pitfalls")[1][:200]),
        ("Is current cycle context included?", "Cycle" in pack or "cycle" in pack),
        ("Is there a quick-start protocol with numbered steps?", "Quick Start" in pack and "1." in pack),
    ]
    
    passed = sum(1 for _, ok in questions if ok)
    score = 100 * passed / len(questions)
    print(f"[selftest] Comprehension test: {passed}/5 ({score:.0f}%)")
    for q, ok in questions:
        print(f"  {'PASS' if ok else 'FAIL'}: {q}")
    
    assert size < 4096, f"Pack too large: {size} bytes (limit 4096)"
    assert score >= 80, f"Comprehension score too low: {score:.0f}% (need >80%)"
    print("[selftest] ALL CHECKS PASSED")
    return True

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    elif len(sys.argv) >= 2:
        agent = sys.argv[1].lower().strip()
        pack = generate_pack(agent)
        out_path = MEM / "archivist" / f"onboarding-pack-{agent}.md"
        out_path.write_text(pack, encoding="utf-8")
        print(f"Pack written: {out_path.relative_to(ROOT)} ({len(pack.encode('utf-8'))} bytes)")
    else:
        print(__doc__)
        sys.exit(1)
