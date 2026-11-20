"""Knowledge Distillation Pipeline - Scribe Goal 5
Usage: python memory/scribe/distill.py --topic <text>
Gathers all memory/ files mentioning the topic, extracts key facts,
and produces a 1-page reference card at memory/scribe/cards/<slug>.md
"""
import os, re, json, argparse
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path("memory")
CARDS_DIR = MEMORY_DIR / "scribe" / "cards"
CARDS_DIR.mkdir(parents=True, exist_ok=True)

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')[:60]

def scan_files(topic):
    """Find all memory files that mention the topic. Prioritize .md prose."""
    matches = []
    topic_lower = topic.lower()
    for root, dirs, files in os.walk(MEMORY_DIR):
        dirs[:] = [d for d in dirs if d not in ('__pycache__', 'test-handoffs', '_test_gate', 'cards')]
        for f in files:
            fp = Path(root) / f
            # Score file type: .md=3, .jsonl=1, .json=0.5
            if f.endswith('.md'):
                weight = 3
            elif f.endswith('.jsonl'):
                weight = 1
            elif f.endswith('.json'):
                weight = 0.5
            else:
                continue
            try:
                content = fp.read_text(encoding='utf-8', errors='skip')
            except Exception:
                continue
            count = content.lower().count(topic_lower)
            if count > 0:
                matches.append({'path': str(fp), 'count': count, 'weight': weight, 'content': content})
    # Sort by weighted relevance
    for m in matches:
        m['score'] = m['count'] * m['weight']
    return sorted(matches, key=lambda x: -x['score'])

def extract_facts(content, topic):
    """Extract meaningful fact lines. Aggressive noise filtering."""
    # Lines that are pure metadata / file paths / JSON fragments
    noise_patterns = [
        r'^\s*#',                          # headers
        r'^\s*[-*]\s*\[?PROGRESS',       # progress markers
        r'^\s*[-*]\s*\[?BLOCKED',        # blocked markers
        r'^\s*TODO',                       # TODO lines
        r'this pass',                       # auto-loop noise
        r'idle \d+',                       # idle time
        r'^\s*"path"\s*:',                # JSON path fields
        r'^\s*"memory/',                   # JSON path values
        r'^\s*\|.*\|.*\|',              # table rows (usually metadata)
        r'^\s*\d+\.\d+',                # float values from JSON
        r'^\s*\{',                        # JSON objects
        r'^\s*"\w[^"]*":',               # JSON key-value pairs
        r'SPLIT:',                          # hygiene report splits
        r'^\s*[-*]\s*`memory/',           # file path bullets
    ]
    
    facts = []
    lines = content.split('\n')
    topic_lower = topic.lower()
    
    for line in lines:
        if topic_lower not in line.lower():
            continue
        is_noise = any(re.search(p, line) for p in noise_patterns)
        if is_noise:
            continue
        # Must have actual words (not just paths/symbols)
        words = re.findall(r'[a-zA-Z]{3,}', line)
        if len(words) < 4:
            continue
        clean = re.sub(r'\*\*(.+?)\*\*', r'\1', line).strip()
        clean = re.sub(r'^\s*[-*]\s+', '', clean).strip()
        clean = re.sub(r'^\s*\d+\.\s*', '', clean).strip()  # strip list numbering
        if len(clean) > 30:
            facts.append(clean[:250])
    return facts

def generate_card(topic, matches):
    """Generate the reference card with quality filtering."""
    slug = slugify(topic)
    card_path = CARDS_DIR / f"{slug}.md"
    
    all_facts = {}
    total_facts = 0
    
    for m in matches[:25]:
        facts = extract_facts(m['content'], topic)
        if facts:
            all_facts[m['path']] = facts
            total_facts += len(facts)
    
    now = datetime.now().strftime('%Y-%m-%d')
    
    lines = [
        f"# {topic} - Reference Card",
        f"",
        f"_Generated: {now} | Sources: {len(all_facts)} files | Key facts: {total_facts}_",
        f"",
        f"## Key Facts",
        f""
    ]
    
    fact_num = 0
    # Prioritize .md sources first, then others
    sorted_sources = sorted(all_facts.items(), key=lambda x: (not x[0].endswith('.md'), -len(x[1])))
    for path, facts in sorted_sources:
        if fact_num >= 25:
            break
        for f in facts[:3]:
            if fact_num >= 25:
                break
            fact_num += 1
            lines.append(f"{fact_num}. {f}")
            lines.append(f"   _Source: `{path}`_")
            lines.append("")
    
    if fact_num == 0:
        lines.append("_No substantive facts extracted. Topic may only appear in metadata files._")
        lines.append("")
    
    lines.append("## Sources (by relevance)")
    lines.append("")
    for path in sorted(all_facts.keys(), key=lambda p: -len(all_facts[p])):
        lines.append(f"- `{path}` ({len(all_facts[path])} facts)")
    
    card_content = '\n'.join(lines)
    card_path.write_text(card_content, encoding='utf-8')
    
    return {
        'card_path': str(card_path),
        'sources': len(all_facts),
        'facts_extracted': fact_num,
        'total_available': total_facts
    }

def main():
    parser = argparse.ArgumentParser(description='Knowledge distillation: topic -> 1-page reference card')
    parser.add_argument('--topic', required=True, help='Topic to distill (e.g. "hotload")')
    args = parser.parse_args()
    print(f"Scanning memory/ for '{args.topic}'...")
    matches = scan_files(args.topic)
    print(f"Found {len(matches)} files mentioning '{args.topic}'")
    if not matches:
        print("No matches found. Nothing to distill.")
        return
    result = generate_card(args.topic, matches)
    print(f"\nCard written: {result['card_path']}")
    print(f"  Sources: {result['sources']} files with substantive facts")
    print(f"  Facts extracted: {result['facts_extracted']} (of {result['total_available']} available)")

if __name__ == '__main__':
    main()
