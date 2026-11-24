"""
goal_proposer.py - Goal Proposal Auto-Generator
Scans decision-log.jsonl + blockers.md + hot notes for recurring patterns (>3 occurrences).
Generates draft cycle proposal (markdown) with one goal per pattern, pre-filled with verification criteria.
Checks against closed_topics.json to avoid duplicates.
Output: memory/researcher/goal-proposals-draft.md
"""
import json
import pathlib
import re
from collections import defaultdict
from datetime import datetime, timezone

DECISION_LOG = pathlib.Path('memory/ops/decision-log.jsonl')
BLOCKERS = pathlib.Path('memory/ops/blockers.md')
HOT_NOTES = pathlib.Path('memory.md')  # shared memory with hot notes
CLOSED_TOPICS = pathlib.Path('memory/goals/closed_topics.json')
OUTPUT = pathlib.Path('memory/researcher/goal-proposals-draft.md')
THRESHOLD = 3  # >3 occurrences = recurring


def load_decision_log() -> list:
    if not DECISION_LOG.exists():
        return []
    recs = []
    for line in DECISION_LOG.read_text(encoding='utf-8').strip().split('\n'):
        if line.strip():
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return recs


def extract_patterns_from_decisions(recs: list) -> dict:
    """Extract recurring patterns from decision log: type+runbook combos, agent actions, keywords in detail."""
    patterns = defaultdict(lambda: {'count': 0, 'agents': set(), 'examples': []})
    # Keyword tracking across all entries
    keyword_counts = defaultdict(int)
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'for', 'and', 'or', 'to', 'in', 'on', 'at', 'by', 'with', 'from', 'this', 'that', 'it', 'not', 'no', 'has', 'have', 'had', 'will', 'would', 'can', 'could'}
    
    for r in recs:
        rtype = r.get('type', 'unknown')
        runbook = r.get('runbook', '')
        agent = r.get('agent', '?')
        # Use type+runbook as pattern key when runbook present, else just type
        key = f"{rtype}:{runbook}" if runbook else rtype
        patterns[key]['count'] += 1
        patterns[key]['agents'].add(agent)
        if len(patterns[key]['examples']) < 2:
            patterns[key]['examples'].append(r.get('ts', '')[:16])
        
        # Also extract keywords from all string fields
        for field in ['detail', 'reason', 'error', 'note', 'message', 'description', 'fault', 'action_taken']:
            val = r.get(field, '')
            if isinstance(val, str) and len(val) > 5:
                words = re.findall(r'[a-z_]+', val.lower())
                for w in words:
                    if w not in stop_words and len(w) > 3:
                        keyword_counts[w] += 1
    
    # Add keyword patterns that exceed threshold
    for kw, count in keyword_counts.items():
        if count > THRESHOLD:
            key = f"keyword:{kw}"
            if key not in patterns:
                patterns[key]['count'] = count
                patterns[key]['agents'].add('multiple')
                patterns[key]['examples'].append(f"{count} occurrences in text fields")
    
    return patterns


def extract_patterns_from_blockers(text: str) -> dict:
    """Extract recurring issue classes from blockers.md headings."""
    patterns = defaultdict(lambda: {'count': 0, 'agents': set(), 'examples': []})
    # Look for [OPS-NOTE] and [NEEDS-HUMAN] entries - extract class/keyword
    notes = re.findall(r'\[(?:OPS-NOTE|NEEDS-HUMAN)\s+([\d-]+)\]\s+(\w+):(.+)', text)
    for date, agent, title in notes:
        # Extract first meaningful keyword from title
        words = re.findall(r'[a-z]+', title.lower())
        # Skip generic words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'for', 'and', 'or', 'to', 'in', 'on', 'at', 'by', 'with', 'from'}
        meaningful = [w for w in words if w not in stop_words and len(w) > 2]
        key = f"blocker:{meaningful[0] if meaningful else 'unknown'}"
        patterns[key]['count'] += 1
        patterns[key]['agents'].add(agent)
        patterns[key]['examples'].append(f"{date}: {title[:60]}")
    return patterns


def extract_patterns_from_hot_notes(text: str) -> dict:
    """Look for recurring keywords in hot notes section."""
    patterns = defaultdict(lambda: {'count': 0, 'agents': set(), 'examples': []})
    # Hot notes are lines starting with '- '
    note_lines = [l.strip() for l in text.split('\n') if l.strip().startswith('- ') and len(l) > 20]
    # Count agent mentions
    agents_mentioned = defaultdict(int)
    for line in note_lines:
        for agent in ['orchestrator', 'researcher', 'verifier', 'scribe', 'designer', 'builder', 'archivist', 'mechanic']:
            if agent.lower() in line.lower():
                agents_mentioned[agent] += 1
    for agent, count in agents_mentioned.items():
        if count > THRESHOLD:
            patterns[f"hot_notes:{agent}_mentions"]['count'] = count
            patterns[f"hot_notes:{agent}_mentions"]['agents'].add(agent)
            patterns[f"hot_notes:{agent}_mentions"]['examples'].append(f"{count} mentions in hot notes")
    return patterns


def load_closed_topics() -> set:
    if not CLOSED_TOPICS.exists():
        return set()
    try:
        topics = json.loads(CLOSED_TOPICS.read_text(encoding='utf-8'))
        return {t.get('sig', '') for t in topics}
    except (json.JSONDecodeError, TypeError):
        return set()


def is_duplicate(pattern_key: str, closed_sigs: set) -> bool:
    """Check if a proposed goal matches a closed topic by keyword overlap."""
    if not CLOSED_TOPICS.exists():
        return False
    try:
        topics = json.loads(CLOSED_TOPICS.read_text(encoding='utf-8'))
        for t in topics:
            text_lower = t.get('text', '').lower()
            # Check if the pattern key's main keyword appears in closed topic text
            keywords = re.findall(r'[a-z_]+', pattern_key.lower())
            overlap = sum(1 for kw in keywords if kw in text_lower and len(kw) > 4)
            if overlap >= 2:
                return True
    except (json.JSONDecodeError, TypeError):
        pass
    return False


def generate_proposal(patterns: dict, closed_sigs: set) -> str:
    """Generate markdown proposal with one goal per recurring pattern."""
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lines = [
        f"# Draft Cycle Proposal (Auto-Generated {now})",
        "",
        f"Source: recurring patterns (>={THRESHOLD+1} occurrences) in decision-log, blockers, hot notes.",
        "",
    ]
    
    proposals = []
    for key, info in sorted(patterns.items(), key=lambda x: -x[1]['count']):
        if info['count'] <= THRESHOLD:
            continue
        if is_duplicate(key, closed_sigs):
            lines.append(f"~~{key}~~ (duplicate of closed topic - skipped)")
            continue
        proposals.append((key, info))
    
    num = 1
    for key, info in proposals:
        agents = ', '.join(sorted(info['agents'])) if info['agents'] else 'unknown'
        examples = '; '.join(info['examples'][:2]) if info['examples'] else ''
        lines += [
            f"## Goal {num}: Address recurring pattern `{key}`",
            "",
            f"- **Pattern:** {key} ({info['count']} occurrences)",
            f"- **Agents affected:** {agents}",
            f"- **Evidence:** {examples}",
            f"- **Proposed goal:** Create targeted remediation for `{key}` to reduce recurrence",
            f"- **Verification:** Script exists and runs; on next cycle, occurrence count drops by >=50% vs baseline of {info['count']}",
            "",
        ]
        num += 1
    
    if not proposals:
        lines.append("No new recurring patterns above threshold (all either below threshold or duplicates).")
    
    return '\n'.join(lines)


def main():
    # Gather all pattern sources
    recs = load_decision_log()
    dec_patterns = extract_patterns_from_decisions(recs)
    
    blk_text = BLOCKERS.read_text(encoding='utf-8') if BLOCKERS.exists() else ''
    blk_patterns = extract_patterns_from_blockers(blk_text)
    
    hn_text = HOT_NOTES.read_text(encoding='utf-8') if HOT_NOTES.exists() else ''
    hn_patterns = extract_patterns_from_hot_notes(hn_text)
    
    # Merge all patterns
    all_patterns = defaultdict(lambda: {'count': 0, 'agents': set(), 'examples': []})
    for source in [dec_patterns, blk_patterns, hn_patterns]:
        for key, info in source.items():
            all_patterns[key]['count'] += info['count']
            all_patterns[key]['agents'].update(info['agents'])
            all_patterns[key]['examples'].extend(info['examples'][:2])
    
    closed_sigs = load_closed_topics()
    proposal = generate_proposal(dict(all_patterns), closed_sigs)
    OUTPUT.write_text(proposal, encoding='utf-8')
    
    # Count valid proposals
    n_goals = len(re.findall(r'^## Goal \d+', proposal, re.MULTILINE))
    print(f"Wrote {OUTPUT}")
    print(f"  Proposals generated: {n_goals}")
    print(f"  Patterns scanned: {len(all_patterns)} total, {sum(1 for p in all_patterns.values() if p['count'] > THRESHOLD)} above threshold")
    
    # Self-verify: >=3 proposals with testable AC
    assert n_goals >= 3 or sum(1 for p in all_patterns.values() if p['count'] > THRESHOLD) < 3, \
        f"Expected >=3 proposals (or insufficient data); got {n_goals}"
    print("  PASS: goal count meets threshold")


if __name__ == '__main__':
    main()
