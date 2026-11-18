#!/usr/bin/env python3
"""Agent Voice Consistency: Attribution Map Generator.

Parses a multi-agent thread/synthesis document and produces an attribution map:
  {agent: [claims made]}

Usage: python memory/scribe/attribution_map.py <thread_file> [--json]
Exit 0 = success; exit 1 = no agents found.
"""
import re, sys, json
from pathlib import Path
from collections import defaultdict

# Known agent names (case-insensitive match in text)
AGENTS = [
    "Orchestrator", "Researcher", "Builder", "Verifier",
    "Designer", "Archivist", "Scribe", "Mechanic"
]

# Patterns that indicate an agent is making a claim:
# 1. "Agent msg:" / "Agent said" / "per Agent"
# 2. Direct quotes attributed: 'Agent msg: "..."'
# 3. Bullet points starting with agent name: "- Agent: ..."
RE_AGENT_QUOTE = re.compile(
    r'([A-Z][a-z]+)\s+(?:msg|said|states?|reports?|claims?|noted|wrote):[\s]*(".*?"|[^\n]{0,200})',
    re.IGNORECASE
)
RE_AGENT_BULLET = re.compile(
    r'^[-*]\s+([A-Z][a-z]+)\s*(?:msg|said|states?|reports?|claims?)?\s*[:—–-]?\s*(.+)',
    re.MULTILINE | re.IGNORECASE
)
RE_AGENT_PARAGRAPH = re.compile(
    r'([A-Z][a-z]+)\s+(?:argues?|proposes?|suggests?|identifies?|flags?|attributes?)\s+([^\n]{0,250})',
    re.IGNORECASE
)

def extract_claims(text: str) -> dict:
    """Extract agent claims from text. Returns {agent: [claims]}"""
    claims = defaultdict(list)

    # Pattern 1: "Agent msg:" / "Agent said" etc.
    for m in RE_AGENT_QUOTE.finditer(text):
        agent = m.group(1).capitalize()
        if agent in AGENTS:
            claim = m.group(2).strip().strip('"')
            if claim and len(claim) > 3:
                claims[agent].append(claim[:200])

    # Pattern 2: Bullet points with agent attribution
    for m in RE_AGENT_BULLET.finditer(text):
        agent = m.group(1).capitalize()
        if agent in AGENTS:
            claim = m.group(2).strip()
            if claim and len(claim) > 3:
                claims[agent].append(claim[:200])

    # Pattern 3: "Agent argues/proposes/suggests..."
    for m in RE_AGENT_PARAGRAPH.finditer(text):
        agent = m.group(1).capitalize()
        if agent in AGENTS:
            claim = m.group(2).strip()
            if claim and len(claim) > 3:
                claims[agent].append(f"argues: {claim[:180]}")

    # Deduplicate per agent (keep first occurrence)
    for agent in claims:
        seen = set()
        unique = []
        for c in claims[agent]:
            key = c.lower()[:80]
            if key not in seen:
                seen.add(key)
                unique.append(c)
        claims[agent] = unique

    return dict(claims)

def main():
    if len(sys.argv) < 2:
        print("Usage: python memory/scribe/attribution_map.py <thread_file> [--json]")
        sys.exit(1)

    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f"ERROR: {filepath} not found")
        sys.exit(1)

    text = filepath.read_text(encoding='utf-8', errors='replace')
    claims = extract_claims(text)

    if not claims:
        print(f"[WARN] No agent attributions found in {filepath.name}")
        sys.exit(1)

    output_json = '--json' in sys.argv

    if output_json:
        print(json.dumps({"file": filepath.name, "attribution_map": claims}, indent=2))
    else:
        print(f"Attribution Map: {filepath.name}")
        print(f"{'='*60}")
        for agent in sorted(claims.keys()):
            items = claims[agent]
            print(f"\n{agent} ({len(items)} claim(s)):")
            for i, c in enumerate(items, 1):
                print(f"  {i}. {c}")
        total = sum(len(v) for v in claims.values())
        print(f"\n{'='*60}")
        print(f"Total: {len(claims)} agents, {total} claims")

    sys.exit(0)

if __name__ == '__main__':
    main()