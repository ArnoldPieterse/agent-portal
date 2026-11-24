#!/usr/bin/env python3
"""Idle Pass Daily Digest (Scribe goal #3, cycle 15).

At end of each day, summarizes idle passes:
- Total idle passes
- Tasks assigned (by agent)
- Productive rate
- Top 3 waste sources (most frequent non-productive task types)

Usage: python memory/scribe/idle_digest.py [--date YYYY-MM-DD] [--simulate N]
Output: memory/ops/idle-digest-{date}.md
"""
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
AUTOLOOP = BASE / "memory" / "ops" / "autoloop.jsonl"
OPS_DIR = BASE / "memory" / "ops"


def load_passes(date_str: str) -> list[dict]:
    """Load passes from autoloop.jsonl for a given date."""
    if not AUTOLOOP.exists():
        return []
    out = []
    decoder = json.JSONDecoder()
    for line in AUTOLOOP.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        idx = 0
        while idx < len(line):
            try:
                obj, end = decoder.raw_decode(line, idx)
                out.append(obj)
                idx = end
                while idx < len(line) and line[idx] in ' \t':
                    idx += 1
            except json.JSONDecodeError:
                break
    # Filter by date
    filtered = []
    for p in out:
        ts = p.get("ts", "")
        if ts.startswith(date_str):
            filtered.append(p)
    return filtered


def generate_digest(passes: list[dict], date_str: str) -> str:
    """Generate the idle digest markdown."""
    total = len(passes)
    if total == 0:
        return f"# Idle Digest {date_str}\n\nNo idle passes recorded.\n"

    # Classify passes
    productive = [p for p in passes if p.get("productive", False)]
    non_productive = [p for p in passes if not p.get("productive", False)]
    rate = (len(productive) / total * 100) if total > 0 else 0

    # Tasks by agent
    by_agent = Counter(p.get("agent", "unknown") for p in passes)

    # Waste sources: task types of non-productive passes
    waste_types = Counter(p.get("task_type", "generic_menu") for p in non_productive)
    top3_waste = waste_types.most_common(3)

    lines = []
    lines.append(f"# Idle Digest {date_str}")
    lines.append("")
    lines.append(f"**Total idle passes:** {total}")
    lines.append(f"**Productive:** {len(productive)} ({rate:.0f}%)")
    lines.append(f"**Non-productive:** {len(non_productive)}")
    lines.append("")

    lines.append("## Tasks by Agent")
    lines.append("")
    for agent, count in by_agent.most_common():
        prod_count = sum(1 for p in passes if p.get("agent") == agent and p.get("productive"))
        lines.append(f"- {agent}: {count} passes ({prod_count} productive)")
    lines.append("")

    lines.append("## Top 3 Waste Sources")
    lines.append("")
    if top3_waste:
        for i, (wtype, count) in enumerate(top3_waste, 1):
            lines.append(f"{i}. {wtype} ({count} occurrences)")
    else:
        lines.append("- No waste sources (all passes productive)")
    lines.append("")

    # Per-pass detail
    lines.append("## All Passes")
    lines.append("")
    for i, p in enumerate(passes, 1):
        agent = p.get("agent", "?")
        task = p.get("task_type", "generic_menu")
        prod = "Y" if p.get("productive") else "N"
        ts = p.get("ts", "")[11:16]  # HH:MM
        lines.append(f"{i}. {ts} {agent}: {task} [{prod}]")
    lines.append("")

    return "\n".join(lines)


def simulate(n: int, date_str: str) -> list[dict]:
    """Generate synthetic idle passes for testing."""
    import random
    agents = ["orchestrator", "researcher", "verifier", "scribe", "designer", "builder", "archivist", "mechanic"]
    task_types = ["generic_menu", "stale_claim_scan", "file_cleanup", "kb_reindex", "log_rotation", "none"]
    random.seed(42)
    passes = []
    for i in range(n):
        hour = 8 + (i % 12)
        minute = (i * 7) % 60
        ts = f"{date_str}T{hour:02d}:{minute:02d}:00Z"
        agent = random.choice(agents)
        task = random.choice(task_types)
        # 60% productive rate
        prod = random.random() < 0.6
        passes.append({
            "ts": ts,
            "agent": agent,
            "task_type": task,
            "productive": prod,
        })
    return passes


def main():
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    simulate_count = 0

    if "--date" in sys.argv:
        idx = sys.argv.index("--date")
        if idx + 1 < len(sys.argv):
            date_str = sys.argv[idx + 1]

    if "--simulate" in sys.argv:
        idx = sys.argv.index("--simulate")
        if idx + 1 < len(sys.argv):
            simulate_count = int(sys.argv[idx + 1])

    if simulate_count > 0:
        print(f"[simulate] generating {simulate_count} synthetic idle passes...")
        passes = simulate(simulate_count, date_str)
    else:
        passes = load_passes(date_str)

    digest = generate_digest(passes, date_str)

    OPS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OPS_DIR / f"idle-digest-{date_str}.md"
    out_path.write_text(digest, encoding="utf-8")

    print(f"[idle_digest] wrote {out_path.relative_to(BASE)} ({len(digest)} bytes)")
    total = len(passes)
    prod = sum(1 for p in passes if p.get("productive"))
    print(f"  Total: {total}, Productive: {prod} ({(prod/total*100) if total else 0:.0f}%)")


if __name__ == "__main__":
    main()
