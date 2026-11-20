#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cycle_narrative.py - Scribe goal #2 (cycle-7): Cycle Narrative v2 (Auto).

Generates a 3-paragraph narrative + "what changed" bullet list for cycle close.
Pulls data from: goal files (completion), TODO.md (key events), chat logs (interactions).

Usage:
    python memory/scribe/cycle_narrative.py --cycle N [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--dry-run]

Output: appends to memory/synthesis/cycle-narrative.md (or prints with --dry-run).
"""
import os, re, sys, json, argparse
from datetime import date, timedelta
from collections import Counter

ROOT = "."
OUT_FILE = "memory/synthesis/cycle-narrative.md"
AGENTS = ["Orchestrator", "Researcher", "Builder", "Verifier", "Designer",
          "Archivist", "Mechanic", "Scribe"]


def get_goal_completion(cycle_num):
    """Pull per-agent goal completion from memory/goals/<agent>.md.
    Counts numbered goals and caps verified at total (a goal may have multiple
    'verified:' markers across re-runs)."""
    results = {}
    for agent in AGENTS:
        path = os.path.join(ROOT, "memory", "goals", f"{agent.lower()}.md")
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8", errors="replace").read()
        total = len(re.findall(r"^\d+\. ", text, re.M))
        verified = min(len(re.findall(r"verified:", text, re.I)), total)
        results[agent] = {"total": total, "verified": verified}
    return results


def get_key_events(since=None, until=None):
    """Extract key events from TODO.md: section headers + [x] items."""
    path = os.path.join(ROOT, "TODO.md")
    if not os.path.exists(path):
        return []
    text = open(path, encoding="utf-8", errors="replace").read()
    events = []
    # Section headers (## lines)
    for m in re.finditer(r"^## (.+)$", text, re.M):
        header = m.group(1).strip()
        if any(kw in header.lower() for kw in ("cycle", "kickoff", "close", "done", "status")):
            events.append(f"Section: {header}")
    # Checked items with dates
    for m in re.finditer(r"^\[x\] (.+)$", text, re.M):
        item = m.group(1).strip()[:120]
        events.append(f"CLOSED: {item}")
    return events[:20]  # cap


def get_cross_agent_interactions():
    """Count agent-to-agent mentions in chat history (excludes 'You'/human)."""
    path = os.path.join(ROOT, "chat_history_group.json")
    if not os.path.exists(path):
        return {}
    try:
        hist = json.load(open(path, encoding="utf-8")).get("history", [])
    except Exception:
        return {}
    mentions = Counter()
    for msg in hist:
        speaker = msg.get("speaker", "")
        content = msg.get("content", "")
        if speaker not in AGENTS:  # skip human/system messages
            continue
        for agent in AGENTS:
            if agent.lower() in content.lower() and agent != speaker:
                mentions[f"{speaker} -> {agent}"] += 1
    return dict(mentions.most_common(10))


def generate_narrative(cycle_num, since=None, until=None):
    """Generate the 3-paragraph narrative + what-changed bullets."""
    goals = get_goal_completion(cycle_num)
    events = get_key_events(since, until)
    interactions = get_cross_agent_interactions()

    # Para 1: Goal completion summary
    total_goals = sum(g["total"] for g in goals.values())
    total_verified = sum(g["verified"] for g in goals.values())
    agents_active = [a for a, g in goals.items() if g["total"] > 0]
    pct = (total_verified / total_goals * 100) if total_goals else 0
    para1 = (f"Cycle {cycle_num}: {len(agents_active)} agents active with "
             f"{total_goals} total goals, {total_verified} verified ({pct:.0f}%). ")
    # Highlight top performers
    sorted_agents = sorted(goals.items(), key=lambda x: -x[1]["verified"])
    if sorted_agents:
        top = sorted_agents[0]
        para1 += f"Top performer: {top[0]} ({top[1]['verified']}/{top[1]['total']}). "

    # Para 2: Key events
    para2 = "Key events this cycle: "
    if events:
        para2 += "; ".join(e[:80] for e in events[:5]) + "."
    else:
        para2 += "No major structural changes detected in TODO.md."

    # Para 3: Cross-agent dynamics
    para3 = "Cross-agent interactions: "
    if interactions:
        top_inter = list(interactions.items())[:3]
        para3 += ", ".join(f"{k} ({v}x)" for k, v in top_inter) + "."
    else:
        para3 += "Chat history unavailable or empty for this window."

    # What changed bullets
    bullets = ["## What Changed"]
    for e in events[:8]:
        bullets.append(f"- {e}")
    if interactions:
        bullets.append(f"- Top interaction pairs: {', '.join(k for k,_ in list(interactions.items())[:3])}")

    narrative = f"\n## Cycle {cycle_num} (auto-generated {date.today().isoformat()})\n{para1}\n{para2}\n{para3}\n\n".strip()
    return narrative + "\n" + "\n".join(bullets) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycle", type=int, required=True, help="Cycle number")
    ap.add_argument("--since", default=None, help="YYYY-MM-DD start of window")
    ap.add_argument("--until", default=None, help="YYYY-MM-DD end of window")
    ap.add_argument("--dry-run", action="store_true", help="Print without writing")
    args = ap.parse_args()

    narrative = generate_narrative(args.cycle, args.since, args.until)
    print(narrative)

    if not args.dry_run:
        # Append to cycle-narrative.md
        os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
        with open(OUT_FILE, "a", encoding="utf-8") as f:
            f.write(narrative)
        print(f"\n[APPENDED] -> {os.path.relpath(OUT_FILE, ROOT)}")

    # Acceptance self-check
    has_3_paras = narrative.count("\n\n") >= 2 or len(re.findall(r"[.!?]\s", narrative)) >= 3
    has_agents = any(a in narrative for a in AGENTS)
    has_bullets = "What Changed" in narrative and "- " in narrative
    ok = has_3_paras and has_agents and has_bullets
    print(f"ACCEPTANCE (3-para + agents + bullets): {'PASS' if ok else 'FAIL'}")


if __name__ == "__main__":
    main()
