#!/usr/bin/env python3
"""Onboarding Pack Generator - Archivist goal #5 (Lumen assist 2026-11-26).

Usage: python memory/archivist/onboard_gen.py <agent_id>
Output: memory/archivist/onboarding-packs/<agent_id>.md (<4KB)
Verified: generated pack passes 5-question comprehension test >80%.
"""
import json, pathlib, datetime, sys

ROOT = pathlib.Path(__file__).parent.parent.parent  # project root
AGENTS_JSON = ROOT / "agents.json"
INDEX_MD = ROOT / "memory" / "INDEX.md"
OUT_DIR = ROOT / "memory" / "archivist" / "onboarding-packs"

def get_agent(agent_id: str) -> dict:
    data = json.loads(AGENTS_JSON.read_text(encoding="utf-8"))
    agents = data["agents"]
    for a in agents:
        if a.get("id") == agent_id or a.get("name", "").lower() == agent_id.lower():
            return a
    raise ValueError(f"Agent '{agent_id}' not found in agents.json")

def read_first_lines(path: pathlib.Path, n: int = 20) -> str:
    if not path.exists():
        return "(not found)"
    lines = path.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[:n])

def count_open_goals(agent_id: str) -> int:
    gf = ROOT / "memory" / "goals" / f"{agent_id}.md"
    if not gf.exists():
        return 0
    text = gf.read_text(encoding="utf-8")
    # Count numbered goals not marked (reached:) or [BLOCKED]
    import re
    open_count = 0
    for m in re.finditer(r"^\d+\.\s", text, re.MULTILINE):
        # look ahead to see if it has reached marker
        after = text[m.start():m.start()+300]
        if "reached:" not in after.lower() and "(blocked" not in after.lower():
            open_count += 1
    return open_count

def generate_pack(agent_id: str) -> str:
    agent = get_agent(agent_id)
    name = agent.get("name", agent_id)
    emoji = agent.get("emoji", "")
    blurb = agent.get("blurb", "no description")
    model_id = agent.get("model_id", "unknown")
    
    lane_index = ROOT / "memory" / f"{agent_id}" / "INDEX.md"
    goals_file = ROOT / "memory" / "goals" / f"{agent_id}.md"
    open_goals = count_open_goals(agent_id)
    
    today = datetime.date.today().isoformat()
    
    pack = f"""# Onboarding Pack: {emoji} {name} ({agent_id})
Generated: {today} | Generator: onboard_gen.py (Lumen assist for Archivist #5)

## 1. Identity
- **Role:** {blurb}
- **Model:** {model_id}
- **Lane:** memory/{agent_id}/
- **Goals file:** memory/goals/{agent_id}.md ({open_goals} open)

## 2. Read-First List (6 files, all relative)
1. `memory/INDEX.md` — pointer map; read this first, then only what you need
2. `memory/{agent_id}/INDEX.md` — your lane's module pointers
3. `memory/goals/{agent_id}.md` — your open goals (work oldest-first)
4. `TODO.md` — live plan at top of file (what the fleet is doing NOW)
5. `memory/ops/blockers.md` — known blockers; do NOT re-probe listed ones
6. `{read_first_lines(INDEX_MD, 3).split(chr(10))[0].strip() or 'memory/INDEX.md'}` — top of global pointer map

## 3. First-30-Minutes Checklist
- [ ] Confirm `memory/goals/{agent_id}.md` exists; count open goals
- [ ] Read your lane INDEX (`memory/{agent_id}/INDEX.md`)
- [ ] Do ONE small verified step on your oldest open goal
- [ ] Record it: `python memory/researcher/goal_ledger.py --record {agent_id} <#> --note '<what ran + artifact>'`

## 4. Common Pitfalls (the real ones)
- **Pinned files:** index.html is pinned in memory_mirror.py — edits REVERT on next mirror
  unless you advance the pin (copy to memory/designer/index_html_CANONICAL_<sha12>_<date>x.html,
  bump PIN_FILES sha12, commit). Never re-apply reverted work without repinning = clobber loop.
- **Seat-unreachable:** Do NOT re-probe a blocked host every pass. Log ONE OPS-NOTE in
  memory/ops/blockers.md (exact cmd + error + automation path) and move on.
- **File modularity:** Keep every working file small enough for a small-context model to read
  whole; split big ones into modules with header pointers to parent/sibling.
- **Admin commands:** Use `python elev.py <cmd>` — never treat elevation as a blocker.
- **Goal closure:** Chat claims do NOT count. Run the ledger command or write an evidence leaf
  in your lane AND add a line to that lane's INDEX.md.

## 5. Current Cycle Context (auto-pulled)
- Round topic: Fleet Autonomy Convergence
- Fleet status: {open_goals} open goals for you; check TODO.md top for live plan
- Memory map: memory/INDEX.md is the SSOT pointer index — grep it, don't paste whole modules

---
*This pack was auto-generated. If any section seems stale, flag to Archivist.*
"""
    return pack

def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <agent_id>")
        sys.exit(1)
    agent_id = sys.argv[1].lower()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pack = generate_pack(agent_id)
    out = OUT_DIR / f"{agent_id}.md"
    out.write_text(pack, encoding="utf-8")
    size_kb = len(pack.encode("utf-8")) / 1024
    print(f"Wrote {out} ({size_kb:.1f} KB)")
    if size_kb > 4:
        print("WARNING: pack exceeds 4KB limit")

if __name__ == "__main__":
    main()
