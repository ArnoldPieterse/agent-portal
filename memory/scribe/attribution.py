#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agent Voice Consistency - Attribution Map Generator.

Usage: python memory/scribe/attribution.py <thread_file> [more_files...]

Produces an attribution map: {agent: [claims/decisions/actions]} for each agent
mentioned in the thread(s). Useful for accountability + understanding focus areas.
"""
import sys, re, json, pathlib
from collections import defaultdict

KNOWN_AGENTS = [
    "Orchestrator", "Researcher", "Builder", "Verifier", "Designer",
    "Archivist", "Mechanic", "Scribe"
]

def extract_attributions(text: str) -> dict:
    """Extract agent attributions from a thread/synthesis document."""
    attributions = {agent: [] for agent in KNOWN_AGENTS}
    
    # Pattern 1: [AgentName] at start of line (action items)
    for m in re.finditer(
        r'^\s*\[?(@?)(Orchestrator|Researcher|Builder|Verifier|Designer|Archivist|Mechanic|Scribe)\]?[:\s]*(.+)$',
        text, re.MULTILINE
    ):
        agent = m.group(2)
        claim = m.group(3).strip()
        if claim:
            attributions[agent].append("[action] " + claim)
    
    # Pattern 2: Lines containing agent names (context lines)
    lines = text.split('\n')
    for line in lines:
        stripped = line.strip()
        if not stripped or len(stripped) < 10:
            continue
        for agent in KNOWN_AGENTS:
            if agent in stripped:
                # Skip if already captured by pattern 1
                if re.match(r'^\s*\[?@?' + agent + r'\]?[:\s]', line):
                    continue
                # Clean up the claim
                claim = re.sub(r'^[-*\u2022\u00b7\s]+', '', stripped).strip()
                if len(claim) > 5:
                    attributions[agent].append(claim)
    
    # Deduplicate while preserving order
    for agent in KNOWN_AGENTS:
        seen = set()
        unique = []
        for c in attributions[agent]:
            key = c[:80]
            if key not in seen:
                seen.add(key)
                unique.append(c)
        attributions[agent] = unique
    
    return {k: v for k, v in attributions.items() if v}

def main():
    if len(sys.argv) < 2:
        print("Usage: python memory/scribe/attribution.py <thread_file> [more_files...]")
        sys.exit(1)
    
    all_attributions = defaultdict(list)
    files_processed = []
    
    for fpath in sys.argv[1:]:
        p = pathlib.Path(fpath)
        if not p.exists():
            print("WARNING: " + fpath + " not found, skipping", file=sys.stderr)
            continue
        text = p.read_text(encoding='utf-8', errors='replace')
        attribs = extract_attributions(text)
        files_processed.append(p.name)
        for agent, claims in attribs.items():
            all_attributions[agent].extend(claims)
    
    # Deduplicate across files
    final = {}
    for agent in KNOWN_AGENTS:
        seen = set()
        unique = []
        for c in all_attributions.get(agent, []):
            key = c[:80]
            if key not in seen:
                seen.add(key)
                unique.append(c)
        if unique:
            final[agent] = unique
    
    # Output
    output = {
        "files": files_processed,
        "attribution_map": final,
        "stats": {
            "total_agents": len(final),
            "total_claims": sum(len(v) for v in final.values()),
            "per_agent": {k: len(v) for k, v in final.items()}
        }
    }
    
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
