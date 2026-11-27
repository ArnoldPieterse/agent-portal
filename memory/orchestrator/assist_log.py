#!/usr/bin/env python3
"""assist_log.py — build a real cross-lane assist graph from on-disk assist records.

Scans memory/**/assist-*.md (and *assist*.md) evidence files. Each file is one record of
ONE agent helping ANOTHER agent's goal. The owner lane directory = the assisting agent;
the target agent is parsed from the filename token(s) after 'assist-'.

Output: memory/orchestrator/assist-log.json  (consumed by ui/cockpit-assist-graph.js via /api/file/raw)
Schema:
  { generated, cycle, total_assists, agents:[{name,count}], edges:[{from,to,count}] }
Run: python memory/orchestrator/assist_log.py
"""
import pathlib, glob, re, json, datetime, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]  # C:\Projects\AgentPortal

# lane dir -> canonical agent name (also covers sub-lanes)
LANE_TO_AGENT = {
    "orchestrator": "Orchestrator", "researcher": "Researcher", "verifier": "Verifier",
    "scribe": "Scribe", "designer": "Designer", "lumen": "Lumen", "reel": "Reel",
    "splice": "Splice", "builder": "Builder", "pixel": "Pixel", "forge": "Forge",
    "archivist": "Archivist", "mechanic": "Mechanic", "outlet": "Outlet",
}
# known agent spellings incl. common typos seen in filenames
AGENT_ALIASES = {
    "orchestrator": "Orchestrator", "researcher": "Researcher", "verifier": "Verifier",
    "scribe": "Scribe", "designer": "Designer", "lumen": "Lumen", "reel": "Reel",
    "splice": "Splice", "builder": "Builder", "pixel": "Pixel", "forge": "Forge",
    "archivist": "Archivist", "mechanic": "Mechanic", "mechic": "Mechanic", "mechnic": "Mechanic",
    "outlet": "Outlet", "white": "White", "pale": "Pale",
}

def agent_from_tokens(tokens):
    """Pick the first token that maps to a known agent (longest-prefix match)."""
    for tok in tokens:
        low = tok.lower().strip("-_.")
        if not low: continue
        if low in AGENT_ALIASES:
            return AGENT_ALIASES[low]
        # prefix match (e.g. 'scribe-goal2' handled by earlier token; try startswith)
        for alias, name in sorted(AGENT_ALIASES.items(), key=lambda kv: -len(kv[0])):
            if low.startswith(alias) and len(alias) >= 5:
                return name
    return None

def parse_file(fp):
    rel = fp.relative_to(ROOT).as_posix()
    parts = rel.split("/")
    # owner lane = first subdir under memory/ that maps to an agent
    owner = None
    for seg in parts[1:]:  # skip leading 'memory'
        if seg.lower() in LANE_TO_AGENT:
            owner = LANE_TO_AGENT[seg.lower()]; break
    if owner is None:
        return None
    fname = parts[-1].lower()
    m = re.search(r"assist-([a-z0-9-]+)", fname)
    if not m:
        # fallback: 'auto-assist' / 'evidence-assist' etc. -> scan whole name for agent token
        target = agent_from_tokens(re.split(r"[-_.]", fname))
    else:
        target = agent_from_tokens(m.group(1).split("-"))
    if target is None or target == owner:
        return None  # self-assist / unparseable -> skip
    return (owner, target)

def main():
    files = set()
    for pat in ["memory/**/assist-*.md", "memory/*/assist-*.md"]:
        files.update(glob.glob(str(ROOT / pat), recursive=True))
    edges = {}
    parsed = skipped = 0
    for fp in sorted(files):
        r = parse_file(pathlib.Path(fp))
        if r is None:
            skipped += 1; continue
        frm, to = r
        key = (frm, to)
        edges[key] = edges.get(key, 0) + 1
        parsed += 1
    agents = {}
    for (f, t), c in edges.items():
        agents[f] = agents.get(f, 0) + c
        agents[t] = agents.get(t, 0) + c
    out = {
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "cycle": "current",
        "source": "memory/**/assist-*.md evidence files",
        "total_assists": parsed,
        "records_parsed": parsed,
        "records_skipped": skipped,
        "agents": [{"name": k, "count": v} for k, v in sorted(agents.items(), key=lambda kv: (-kv[1], kv[0]))],
        "edges": [{"from": f, "to": t, "count": c}
                  for (f, t), c in sorted(edges.items(), key=lambda kv: (-kv[1], kv[0][0], kv[0][1]))],
    }
    dest = ROOT / "memory" / "orchestrator" / "assist-log.json"
    dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("WROTE", dest.relative_to(ROOT), "edges=%d agents=%d parsed=%d skipped=%d total_assists=%d" % (
        len(edges), len(agents), parsed, skipped, parsed))
    for e in out["edges"][:12]:
        print("   %s -> %s  x%d" % (e["from"], e["to"], e["count"]))
    return 0

if __name__ == "__main__":
    sys.exit(main())
