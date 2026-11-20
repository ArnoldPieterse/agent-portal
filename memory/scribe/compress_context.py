#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compress_context.py - Scribe goal #3 (cycle-7): Context Compression for New Agents.

Takes the full memory/ relevant to an agent's role and compresses it into a
<2000-token briefing: key decisions, current state, open threads, gotchas.

Usage:
    python memory/scribe/compress_context.py --agent <name> [--dry-run]

Output: memory/scribe/briefings/<agent>-briefing.md
"""
import os, re, json, argparse
from datetime import date

ROOT = "."
BRIEFINGS_DIR = "memory/scribe/briefings"


def get_agent_goals(agent):
    """Read the agent's goal file and extract open + verified goals."""
    path = os.path.join(ROOT, "memory", "goals", f"{agent.lower()}.md")
    if not os.path.exists(path):
        return {"open": [], "verified": []}
    text = open(path, encoding="utf-8", errors="replace").read()
    open_goals, verified_goals = [], []
    for m in re.finditer(r"^\d+\. (.+?)(?=\n\d+\. |\Z)", text, re.M | re.S):
        goal_text = m.group(1).strip()
        title = goal_text.split(" - ")[0].split(" **")[0].strip().rstrip("*").strip()
        if re.search(r"\(verified:\s*\d{4}-\d{2}-\d{2}|\*\*verified:?\*\*", goal_text):
            verified_goals.append(title[:80])
        else:
            open_goals.append(title[:80])
    return {"open": open_goals, "verified": verified_goals}


def get_key_decisions(agent):
    """Pull decisions from decisions.jsonl where owner matches or agent is mentioned."""
    path = os.path.join(ROOT, "memory", "synthesis", "decisions.jsonl")
    if not os.path.exists(path):
        return []
    results = []
    for line in open(path, encoding="utf-8"):
        try:
            d = json.loads(line.strip())
        except Exception:
            continue
        owner = (d.get("owner", "") or "").lower()
        context = (d.get("context", "") or "").lower()
        decision = (d.get("decision", "") or "").lower()
        if agent.lower() in owner or agent.lower() in context or agent.lower() in decision:
            results.append(d)
    return results[-5:]  # most recent 5


def get_gotchas(agent):
    """Find correction/stale-claim/overclaim patterns relevant to this agent."""
    gotchas = []
    scribe_dir = os.path.join(ROOT, "memory", "scribe")
    if not os.path.isdir(scribe_dir):
        return gotchas
    patterns = re.compile(r"(stale|correction|overclaim|discrepancy|contradiction|fix.*applied)", re.I)
    for fname in sorted(os.listdir(scribe_dir)):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(scribe_dir, fname)
        try:
            text = open(fpath, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        if agent.lower() in text.lower() and patterns.search(text):
            for line in text.split("\n"):
                line = line.strip().lstrip("-# ").strip()
                if len(line) > 20 and not line.startswith("Gotchas") and not line.startswith("**What"):
                    gotchas.append(f"[{fname}] {line[:120]}")
                    break
        if len(gotchas) >= 5:
            break
    return gotchas


def get_current_state(agent):
    """Extract current state from TODO.md (top section)."""
    path = os.path.join(ROOT, "TODO.md")
    if not os.path.exists(path):
        return ""
    text = open(path, encoding="utf-8", errors="replace").read()
    m = re.search(r"^## (.+?)(?=\n## |\Z)", text, re.M | re.S)
    if m:
        return m.group(0)[:500].strip()
    return text[:300]


def estimate_tokens(text):
    """Rough token estimate: ~4 chars per token for English."""
    return len(text) // 4


def generate_briefing(agent):
    agent = agent.capitalize()
    goals = get_agent_goals(agent)
    decisions = get_key_decisions(agent)
    gotchas = get_gotchas(agent)
    state = get_current_state(agent)

    lines = [f"# {agent} Briefing (auto-generated {date.today().isoformat()})", ""]

    lines.append("## Current State")
    lines.append(state[:400] if state else "(TODO.md not available)")
    lines.append("")

    lines.append(f"## Open Goals ({len(goals['open'])})")
    for g in goals["open"][:5]:
        lines.append(f"- {g}")
    if len(goals["verified"]) > 0:
        lines.append(f"\nVerified this cycle: {len(goals['verified'])} goals")
    lines.append("")

    if decisions:
        lines.append("## Key Decisions (relevant to you)")
        for d in decisions[:3]:
            lines.append(f"- [{d.get('date','?')}] {d.get('decision','?')[:100]}")
        lines.append("")

    lines.append(f"## Gotchas ({len(gotchas)})")
    for g in gotchas[:4]:
        lines.append(f"- {g}")
    lines.append("")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True, help="Agent name (e.g. Researcher)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    agent = args.agent.lower()
    briefing = generate_briefing(agent)
    tokens = estimate_tokens(briefing)
    print(briefing)
    print(f"\n---\nEstimated tokens: {tokens} (limit: 2000)")
    print(f"TOKEN CHECK: {'PASS' if tokens < 2000 else 'FAIL'}")

    gotcha_count = len(re.findall(r"^- \[", briefing, re.M))
    print(f"GOTCHA COUNT: {gotcha_count} (need >=3): {'PASS' if gotcha_count >= 3 else 'WARN'}")

    if not args.dry_run:
        os.makedirs(BRIEFINGS_DIR, exist_ok=True)
        out_path = os.path.join(BRIEFINGS_DIR, f"{agent}-briefing.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(briefing)
        print(f"[WRITTEN] -> {os.path.relpath(out_path, ROOT)}")


if __name__ == "__main__":
    main()
