"""Cycle Retrospective Generator - generates structured retro markdown on cycle close.

Gathers: goals completed/proposed, slippage, patterns, interventions.
Output: memory/scribe/cycle-retro-N.md with >=5 sections.

Usage:
  python memory/scribe/cycle_retro_gen.py --cycle 16     # generate retro for cycle 16
  python memory/scribe/cycle_retro_gen.py --latest       # generate for most recent cycle
  python memory/scribe/cycle_retro_gen.py --selftest     # verify structure + file refs
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
OPS_DIR = os.path.join(ROOT, "memory", "ops")
GOALS_DIR = os.path.join(ROOT, "memory", "goals")
SCRIBE_DIR = HERE


def _read_json(path):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _read_jsonl(path):
    try:
        with open(path, encoding='utf-8') as f:
            return [json.loads(l) for l in f if l.strip()]
    except OSError:
        return []


def get_cycle_history(cycle_num: int) -> dict:
    """Get cycle data from consolidated history."""
    entries = _read_jsonl(os.path.join(OPS_DIR, "cycle-history-consolidated.jsonl"))
    for e in entries:
        if e.get("cycle") == cycle_num:
            return e
    return {"cycle": cycle_num, "duration_hours": None, "completion_pct": 0,
            "intervention_count": 0, "closure_evidence": False, "reliability": "unknown"}


def get_goals_for_cycle(cycle_num: int) -> dict:
    """Gather goals data: completed vs proposed per agent."""
    agents = ['archivist', 'builder', 'designer', 'mechanic', 'orchestrator', 'researcher', 'scribe', 'verifier']
    completed = {}
    total = {}
    for agent in agents:
        fpath = os.path.join(GOALS_DIR, f"{agent}.md")
        if not os.path.exists(fpath):
            continue
        with open(fpath, encoding='utf-8') as f:
            content = f.read()
        # Count verified goals
        verified = len(re.findall(r'\(verified:', content))
        all_goals = len(re.findall(r'^\d+\.\s+\*\*', content, re.MULTILINE))
        completed[agent] = verified
        total[agent] = all_goals
    return {"completed": completed, "total": total}


def get_interventions(cycle_num: int) -> list:
    """Get human interventions for a specific cycle."""
    entries = _read_jsonl(os.path.join(OPS_DIR, "human-interventions.jsonl"))
    return [e for e in entries if e.get("cycle") == cycle_num]


def get_slippage(cycle_num: int) -> list:
    """Identify goals that slipped (not completed despite being proposed)."""
    goals_data = get_goals_for_cycle(cycle_num)
    slips = []
    for agent, total in goals_data["total"].items():
        comp = goals_data["completed"].get(agent, 0)
        if total > comp:
            slips.append({"agent": agent, "proposed": total, "completed": comp, "slipped": total - comp})
    return slips


def get_patterns(cycle_num: int) -> list:
    """Identify cross-agent patterns from available data."""
    patterns = []
    # Check for repeated intervention types
    interventions = get_interventions(cycle_num)
    type_counts = {}
    for i in interventions:
        t = i.get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1
    for t, c in type_counts.items():
        if c >= 2:
            patterns.append(f"Repeated {t} interventions ({c}x) suggest systemic issue")

    # Check completion rate consistency
    goals_data = get_goals_for_cycle(cycle_num)
    rates = []
    for agent in goals_data["total"]:
        total = goals_data["total"][agent]
        comp = goals_data["completed"].get(agent, 0)
        if total > 0:
            rates.append((agent, comp / total))
    if rates:
        high = [a for a, r in rates if r >= 0.7]
        low = [a for a, r in rates if r < 0.3]
        if high:
            patterns.append(f"High performers: {', '.join(high)}")
        if low:
            patterns.append(f"Needs attention: {', '.join(low)} (low completion)")

    return patterns or ["No significant cross-agent patterns detected this cycle"]


def generate_retro(cycle_num: int) -> str:
    """Generate the full retro markdown for a cycle."""
    history = get_cycle_history(cycle_num)
    goals_data = get_goals_for_cycle(cycle_num)
    interventions = get_interventions(cycle_num)
    slippage = get_slippage(cycle_num)
    patterns = get_patterns(cycle_num)

    total_completed = sum(goals_data["completed"].values())
    total_proposed = sum(goals_data["total"].values())
    completion_pct = (total_completed / total_proposed * 100) if total_proposed > 0 else 0

    # Build markdown sections
    lines = []
    lines.append(f"# Cycle {cycle_num} Retrospective")
    lines.append(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")

    # Section 1: Summary
    lines.append("## 1. Summary")
    lines.append(f"- **Completion:** {total_completed}/{total_proposed} goals ({completion_pct:.0f}%)")
    lines.append(f"- **Duration:** {history.get('duration_hours', 'N/A')}h")
    lines.append(f"- **Interventions:** {len(interventions)} human interventions")
    lines.append(f"- **Reliability:** {history.get('reliability', 'unknown')}")
    lines.append("")

    # Section 2: Goals Completed
    lines.append("## 2. Goals Completed")
    if total_completed > 0:
        for agent, count in sorted(goals_data["completed"].items()):
            if count > 0:
                lines.append(f"- **{agent}:** {count}/{goals_data['total'].get(agent, '?')} completed")
    else:
        lines.append("- No goals formally verified this cycle.")
    lines.append("")

    # Section 3: Slippage Analysis
    lines.append("## 3. Slippage Analysis")
    if slippage:
        for s in slippage:
            lines.append(f"- **{s['agent']}:** {s['slipped']} goal(s) slipped (proposed {s['proposed']}, completed {s['completed']})")
    else:
        lines.append("- No slippage detected.")
    lines.append("")

    # Section 4: Patterns Observed
    lines.append("## 4. Patterns Observed")
    for p in patterns:
        lines.append(f"- {p}")
    lines.append("")

    # Section 5: Interventions
    lines.append("## 5. Human Interventions")
    if interventions:
        for i in interventions:
            lines.append(f"- [{i.get('type', '?')}] {i.get('agent', '?')}: {i.get('context', '')[:100]}")
    else:
        lines.append("- No human interventions recorded for this cycle.")
    lines.append("")

    # Section 6: Recommendations
    lines.append("## 6. Recommendations")
    recs = []
    if completion_pct < 50:
        recs.append(f"Completion rate ({completion_pct:.0f}%) is below target - consider reducing scope or increasing passes.")
    if slippage:
        agents_slipped = [s['agent'] for s in slippage]
        recs.append(f"Review goal sizing for: {', '.join(agents_slipped)}.")
    if len(interventions) > 3:
        recs.append(f"High intervention count ({len(interventions)}) - investigate root causes of human involvement.")
    if not recs:
        recs.append("Cycle performed within expected parameters. Maintain current cadence.")
    for r in recs:
        lines.append(f"- {r}")
    lines.append("")

    # Section 7: Data Sources
    lines.append("## 7. Data Sources")
    sources = [
        "memory/ops/cycle-history-consolidated.jsonl",
        "memory/goals/*.md (per-agent goal files)",
        "memory/ops/human-interventions.jsonl",
    ]
    for s in sources:
        lines.append(f"- `{s}`")
    lines.append("")

    return "\n".join(lines)


def write_retro(cycle_num: int) -> str:
    """Generate and write retro to file. Returns the output path."""
    content = generate_retro(cycle_num)
    out_path = os.path.join(SCRIBE_DIR, f"cycle-retro-{cycle_num}.md")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return out_path


def verify_retro(filepath: str) -> dict:
    """Verify a retro file has >=5 sections and all file references resolve."""
    with open(filepath, encoding='utf-8') as f:
        content = f.read()

    # Count sections (## headers)
    sections = re.findall(r'^## .+', content, re.MULTILINE)
    section_count = len(sections)

    # Extract file references (backticked paths)
    file_refs = re.findall(r'`((?:memory|ui|ops)/[\w/\*.\-]+)`', content)
    resolved = 0
    unresolved = []
    for ref in file_refs:
        # Expand wildcards
        if '*' in ref:
            import glob
            matches = glob.glob(os.path.join(ROOT, ref))
            if matches:
                resolved += 1
            else:
                unresolved.append(ref)
        else:
            if os.path.exists(os.path.join(ROOT, ref)):
                resolved += 1
            else:
                unresolved.append(ref)

    return {
        "file": filepath,
        "section_count": section_count,
        "sections": sections,
        "file_refs_total": len(file_refs),
        "file_refs_resolved": resolved,
        "file_refs_unresolved": unresolved,
        "pass": section_count >= 5 and len(unresolved) == 0,
    }


def run_selftest():
    """Selftest: generate cycle-16 retro, verify >=5 sections + file refs resolve."""
    print("=== cycle_retro_gen.py SELFTEST ===")

    # Generate cycle-16 retro
    out_path = write_retro(16)
    print(f"  Generated: {out_path}")

    # Verify structure
    result = verify_retro(out_path)
    print(f"  Sections: {result['section_count']} (need >=5): {[s.strip() for s in result['sections']]}")
    print(f"  File refs: {result['file_refs_resolved']}/{result['file_refs_total']} resolved")

    assert result["section_count"] >= 5, f"Only {result['section_count']} sections, need >=5"
    assert len(result["file_refs_unresolved"]) == 0, f"Unresolved refs: {result['file_refs_unresolved']}"
    assert result["pass"], "Verification failed"

    # Also test cycle 15 for robustness
    out15 = write_retro(15)
    r15 = verify_retro(out15)
    print(f"  Cycle 15: {r15['section_count']} sections, {r15['file_refs_resolved']}/{r15['file_refs_total']} refs")
    assert r15["section_count"] >= 5, f"Cycle 15 only has {r15['section_count']} sections"

    print("\n  SELFTEST PASS: cycle-16 retro has 7 sections, all file refs resolve")
    return True


def main():
    if '--selftest' in sys.argv:
        ok = run_selftest()
        sys.exit(0 if ok else 1)

    if '--cycle' in sys.argv:
        idx = sys.argv.index('--cycle')
        if idx + 1 < len(sys.argv):
            n = int(sys.argv[idx + 1])
            out = write_retro(n)
            print(f"Wrote: {out}")
    elif '--latest' in sys.argv:
        entries = _read_jsonl(os.path.join(OPS_DIR, "cycle-history-consolidated.jsonl"))
        if entries:
            latest = max(e.get("cycle", 0) for e in entries)
            out = write_retro(latest)
            print(f"Wrote: {out} (cycle {latest})")
    else:
        print(__doc__)


if __name__ == '__main__':
    main()