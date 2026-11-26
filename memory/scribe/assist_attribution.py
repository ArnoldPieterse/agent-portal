"""Cross-Lane Assist Attribution - attribute each reached goal to owner + assistants.

Scans evidence files for assist/credit patterns, cross-references with goals files
to find reached goals, and emits attribution JSONL.

Output: memory/scribe/assist-attribution.jsonl
  {cycle, goal, owner, assists[], credit_line}

Also computes per-agent assist-in / assist-out counts.
"""
import json, pathlib, re
from datetime import datetime, timezone
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "memory/scribe/assist-attribution.jsonl"
SUMMARY_OUT = ROOT / "memory/scribe/assist-summary.json"

# Known agent names (for matching)
AGENTS = [
    "Orchestrator", "Researcher", "Builder", "Verifier", "Designer",
    "Scribe", "Archivist", "Mechanic", "Outlet", "Pixel", "Forge",
    "Lumen", "Reel", "Splice"
]

# Patterns that indicate an assist credit in evidence files
ASSIST_PATTERNS = [
    # "Agent: X (assisting Y)" or "Agent: X (assist to Y)"
    re.compile(r'Agent:\s*(\w+)\s*\(assist(?:ing| to)?\s*(\w+)', re.IGNORECASE),
    # "X assist" in title/heading
    re.compile(r'#.*?(\w+)\s+(?:assist|Assist)', re.IGNORECASE),
    # "(assist by X)" or "(Builder assist)"
    re.compile(r'\((?:assist(?:ing)?\s+by\s+)?(\w+)\s+assist\)', re.IGNORECASE),
    # "Verified by: X (assist...)"
    re.compile(r'Verified by:\s*(?:\*\*)?(\w+)(?:\*\*)?\s*\(assist', re.IGNORECASE),
    # "Lane: X (assist...)" or "**Lane:** X (assist...)"
    re.compile(r'(?:\*\*)?Lane(?:\*\*)?:\s*(\w+)\s*\(assist', re.IGNORECASE),
    # "By: X (assist...)"
    re.compile(r'By:\s*(?:\*\*)?(\w+)(?:\*\*)?\s*\(assist', re.IGNORECASE),
]

def is_agent(name):
    """Check if a string matches a known agent name."""
    return name in AGENTS

def parse_assist_from_file(path):
    """Extract assist credits from an evidence file.
    
    Returns list of {assister, owner, credit_line} tuples.
    Only returns entries where BOTH assister and owner are known agents.
    """
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, UnicodeDecodeError):
        return []
    
    credits = []
    lines = content.split("\n")
    
    for line in lines:
        # Pattern 1: "Agent: X (assisting Y)" 
        m = re.search(r'Agent:\s*(\w+)\s*\(assist(?:ing| to)?\s*(\w+)', line, re.IGNORECASE)
        if m and is_agent(m.group(1)) and is_agent(m.group(2)):
            credits.append({"assister": m.group(1), "owner": m.group(2), "credit_line": line.strip()})
            continue
        
        # Pattern 2: "(assist by X)" or "(X assist)" in context of an owner
        m = re.search(r'\((?:assist(?:ing)?\s+by\s+)?(\w+)\s+assist\)', line, re.IGNORECASE)
        if m and is_agent(m.group(1)):
            # Try to find the owner from context (look for "owner" or "goal" nearby)
            owner_match = re.search(r'(?:owner|Owner|goal.*?=|Goal.*?owner).*?(\w+)', line)
            if owner_match and is_agent(owner_match.group(1)):
                credits.append({"assister": m.group(1), "owner": owner_match.group(1), "credit_line": line.strip()})
            else:
                # Try title for owner
                for tline in lines[:5]:
                    tm = re.search(r'(?:Goal|goal)\s*#?\d+.*?(\w+)', tline)
                    if tm and is_agent(tm.group(1)) and tm.group(1) != m.group(1):
                        credits.append({"assister": m.group(1), "owner": tm.group(1), "credit_line": line.strip()})
                        break
        
        # Pattern 3: "Verified by: X (assist...)" with owner in context
        m = re.search(r'Verified by:\s*(?:\*\*)?(\w+)(?:\*\*)?\s*\(assist', line, re.IGNORECASE)
        if m and is_agent(m.group(1)):
            # Find owner from "credit" or "owner" in same or nearby lines
            for ctx_line in lines[max(0, lines.index(line)-2):lines.index(line)+3]:
                om = re.search(r'(?:credit|Credit|Owner|owner).*?(\w+)', ctx_line)
                if om and is_agent(om.group(1)) and om.group(1) != m.group(1):
                    credits.append({"assister": m.group(1), "owner": om.group(1), "credit_line": line.strip()})
                    break
        
        # Pattern 4: "Lane: X (assist...)" - X is the assister, owner from context
        m = re.search(r'(?:\*\*)?Lane(?:\*\*)?:\s*(\w+)\s*\(assist', line, re.IGNORECASE)
        if m and is_agent(m.group(1)):
            # Look for "Owner of goal" or similar
            for ctx_line in lines[max(0, lines.index(line)-3):lines.index(line)+5]:
                om = re.search(r'(?:Owner|owner).*?of.*?(?:goal|Goal).*?(\w+)', ctx_line)
                if om and is_agent(om.group(1)) and om.group(1) != m.group(1):
                    credits.append({"assister": m.group(1), "owner": om.group(1), "credit_line": line.strip()})
                    break
    
    # Deduplicate (same assister+owner pair from same file = 1 credit)
    seen = set()
    unique = []
    for c in credits:
        key = (c["assister"], c["owner"])
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique

def get_reached_goals():
    """Parse all lane goals files for REACHED/verified goals.
    
    Returns list of {lane, goal_num, goal_title, cycle}
    """
    reached = []
    goals_dir = ROOT / "memory/goals"
    
    # Current goals files (not archived)
    for gf in sorted(goals_dir.glob("*.md")):
        if "archive" in str(gf) or "drafts" in str(gf):
            continue
        lane_match = re.match(r'^(\w+)', gf.stem)
        if not lane_match:
            continue
        lane = lane_match.group(1).capitalize()
        if lane not in AGENTS and lane.lower() not in [a.lower() for a in AGENTS]:
            continue
        
        try:
            content = gf.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        
        # Find numbered goals with REACHED or verified markers
        for m in re.finditer(r'(\d+)\.\s*\*\*(.+?)\*\*.*?(?:REACHED|verified:)', content, re.DOTALL):
            goal_num = int(m.group(1))
            title = m.group(2).strip()[:80]
            reached.append({"lane": lane, "goal_num": goal_num, "goal_title": title})
    
    return reached

def main():
    # Step 1: Scan all evidence files for assist credits
    all_credits = []
    md_files = list((ROOT / "memory").rglob("*.md"))
    
    for f in md_files:
        if "archive" in str(f).lower() and "2026-11" not in str(f):
            continue  # Skip old archives
        credits = parse_assist_from_file(f)
        for c in credits:
            c["source_file"] = str(f.relative_to(ROOT))
            all_credits.append(c)
    
    print(f"Scanned {len(md_files)} .md files, found {len(all_credits)} assist credits")
    
    # Step 2: Get reached goals
    reached_goals = get_reached_goals()
    print(f"Found {len(reached_goals)} reached goals in current lane files")
    
    # Step 3: Build attribution entries with precise goal matching
    # Only attribute an assist to a specific goal if the evidence file mentions
    # that goal number or title keyword. Otherwise mark as lane-level.
    attribution = []
    credits_by_owner = defaultdict(list)
    for c in all_credits:
        credits_by_owner[c["owner"]].append(c)
    
    for rg in reached_goals:
        owner = rg["lane"]
        goal_num = rg["goal_num"]
        title_words = set(w.lower() for w in re.findall(r'[a-z]+', rg["goal_title"]) if len(w) > 3)
        
        assists = []
        credit_lines = []
        
        # Find credits where this agent is the owner
        for c in credits_by_owner.get(owner, []):
            if c["assister"] == owner:
                continue  # Don't count self-assist
            
            # Check if evidence file specifically references this goal
            source_file = ROOT / c["source_file"]
            try:
                src_content = source_file.read_text(encoding="utf-8", errors="ignore")
            except (OSError, UnicodeDecodeError):
                src_content = ""
            
            # Goal-specific match: file mentions goal number or key title words
            goal_specific = False
            if re.search(rf'(?:goal|Goal|#)\s*{goal_num}\b', src_content):
                goal_specific = True
            elif title_words and len(title_words & set(w.lower() for w in re.findall(r'[a-z]+', src_content))) >= 2:
                goal_specific = True
            
            if c["assister"] not in assists:
                assists.append(c["assister"])
                specificity = "goal-specific" if goal_specific else "lane-level"
                credit_lines.append(f"assist: {c['assister']} [{specificity}] ({c['source_file']})")
        
        attribution.append({
            "cycle": "current",  # Cycle 26 (active)
            "goal": f"{owner} #{rg['goal_num']}: {rg['goal_title']}",
            "owner": owner,
            "assists": assists,
            "credit_line": "; ".join(credit_lines) if credit_lines else None,
            "source": "evidence file scan"
        })
    
    # Step 4: Compute per-agent assist-in / assist-out
    assist_in = defaultdict(int)
    assist_out = defaultdict(int)
    for c in all_credits:
        assist_in[c["owner"]] += 1
        assist_out[c["assister"]] += 1
    
    summary = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "total_credits_found": len(all_credits),
        "assist_in": dict(assist_in),
        "assist_out": dict(assist_out),
        "net_assist": {a: assist_out[a] - assist_in.get(a, 0) for a in sorted(set(list(assist_in.keys()) + list(assist_out.keys())))}
    }
    
    # Step 5: Write outputs
    OUT.write_text("\n".join(json.dumps(a) for a in attribution) + "\n", encoding="utf-8")
    SUMMARY_OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    
    print(f"\nOK: {len(attribution)} attribution entries -> {OUT.relative_to(ROOT)}")
    print(f"     {len(all_credits)} credits, summary -> {SUMMARY_OUT.relative_to(ROOT)}")
    
    # Show top assistants
    top_out = sorted(assist_out.items(), key=lambda x: -x[1])[:5]
    print(f"     Top assist-out: {top_out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
