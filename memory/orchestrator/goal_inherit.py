"""Cross-Cycle Inheritance Generator - scans closed goals for v1 markers or incomplete scope notes.
Generates v2 goals with inherited context, updated verification, and link to v1.

Usage:
  python memory/orchestrator/goal_inherit.py --scan          # scan all goal files
  python memory/orchestrator/goal_inherit.py --selftest      # run self-test (3 cases)
  python memory/orchestrator/goal_inherit.py --output FILE   # write proposed v2 goals to FILE
"""
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
GOALS_DIR = os.path.normpath(os.path.join(HERE, "..", "goals"))
CLOSED_TOPICS_FILE = os.path.join(GOALS_DIR, "closed_topics.json")
OUTPUT_FILE = os.path.normpath(os.path.join(HERE, "..", "ops", "inheritance-proposals.json"))

# Patterns that indicate a goal has v1 markers or incomplete scope
V1_MARKERS = [
    r'\bv1\b',            # explicit v1 tag
    r'\(incomplete[^)]*\)',  # (incomplete ...)
    r'incomplete scope',
    r'carry[- ]forward',
    r'succeeded by',
    r'partial completion',
    r'scope:.*TODO',
    r'next cycle',
    r'v2 needed',
]

# A goal is "closed" if it has a (verified: ...) marker
CLOSED_PATTERN = re.compile(r'\(verified:\s*[^)]+\)', re.IGNORECASE)


def load_closed_topics():
    """Load closed_topics.json - list of {sig, text, agent, at}."""
    if not os.path.exists(CLOSED_TOPICS_FILE):
        return []
    with open(CLOSED_TOPICS_FILE, encoding='utf-8') as f:
        return json.load(f)


def goal_signature(text: str) -> str:
    """Compute a short signature for a goal text (first 100 chars, sha1[:16])."""
    norm = re.sub(r'\s+', ' ', text.strip()).lower()[:100]
    return hashlib.sha1(norm.encode('utf-8')).hexdigest()[:16]


def parse_goal_lines(content: str):
    """Parse numbered goal lines from a goal file. Returns list of dicts.
    Each dict: {num, title, text, verified, v1_markers_found}.
    """
    goals = []
    # Match lines starting with a number followed by period
    for m in re.finditer(r'^(\d+)\.\s+\*\*(.+?)\*\*\s*-\s+(.*)', content, re.MULTILINE):
        num = int(m.group(1))
        title = m.group(2).strip()
        text = m.group(3).strip()

        # Check if closed (has verified marker)
        is_closed = bool(CLOSED_PATTERN.search(text))

        # Check for v1 markers
        markers_found = []
        for pat in V1_MARKERS:
            if re.search(pat, text, re.IGNORECASE):
                markers_found.append(pat)

        goals.append({
            'num': num,
            'title': title,
            'text': text,
            'verified': is_closed,
            'v1_markers_found': markers_found,
        })
    return goals


def scan_goal_files(goals_dir: str = None):
    """Scan all goal files in the goals directory for closed goals with v1 markers."""
    if goals_dir is None:
        goals_dir = GOALS_DIR

    candidates = []
    for fname in sorted(os.listdir(goals_dir)):
        if not fname.endswith('.md') or fname == 'INDEX.md':
            continue
        fpath = os.path.join(goals_dir, fname)
        with open(fpath, encoding='utf-8') as f:
            content = f.read()
        for g in parse_goal_lines(content):
            if g['verified'] and g['v1_markers_found']:
                candidates.append({
                    'file': fname,
                    **g,
                })
    return candidates


def generate_v2_goal(goal: dict, cycle_num: int = None) -> dict:
    """Generate a v2 goal from a closed v1 goal.
    Returns: {goal_id, title, text, v1_ref, v2_verification, inherited_context}
    """
    if cycle_num is None:
        cycle_num = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    # Extract original verification criteria
    ver_match = re.search(r'Verified:\s*(.+?)(?:\s*\(verified:|$)', goal['text'], re.IGNORECASE)
    orig_verification = ver_match.group(1).strip() if ver_match else 'carry-forward scope'

    # Build v2 goal with inherited context and updated verification
    title_v2 = f"{goal['title']} (v2)"
    text_v2 = (
        f"Inherited from cycle-{goal.get('cycle', '?')} goal #{goal['num']} in {goal.get('file', 'unknown')}. "
        f"Original scope: {goal['text'][:200]}. "
        f"v1 markers detected: {', '.join(goal['v1_markers_found'])}. "
        f"Updated verification: {orig_verification} + confirm v2 scope complete. "
        f"Link to v1: {goal.get('file', 'unknown')}#goal-{goal['num']}"
    )

    return {
        'goal_id': f"v2-{goal['num']}-{goal_signature(goal['title'])[:8]}",
        'title': title_v2,
        'text': text_v2,
        'v1_ref': f"{goal.get('file', 'unknown')}#goal-{goal['num']}",
        'v2_verification': orig_verification + ' + confirm v2 scope complete',
        'inherited_context': goal['text'],
        'cycle': cycle_num,
    }


def check_not_in_closed_topics(v2_goal: dict, closed_topics: list) -> bool:
    """Check that the generated v2 goal is NOT already in closed_topics."""
    sig = goal_signature(v2_goal['title'] + ' ' + v2_goal['text'])
    for ct in closed_topics:
        if ct.get('sig') == sig:
            return False
        # Also check by text prefix
        if v2_goal['title'].lower()[:60] in ct.get('text', '').lower():
            return False
    return True


def run_selftest():
    """Self-test: 3 synthetic cases produce valid v2 goals; none in closed_topics."""
    print("=== goal_inherit.py SELFTEST ===")
    closed_topics = load_closed_topics()
    print(f"  Closed topics loaded: {len(closed_topics)} entries")

    # 3 test cases with v1 markers
    test_cases = [
        {
            'num': 1,
            'title': 'Predictive Probe Cadence',
            'text': 'Extend seat_probe.py to auto-adjust cadence. Verified: mode change triggers within 1 cycle. (v1) carry-forward to next cycle for full implementation.',
            'verified': True,
            'v1_markers_found': [r'\bv1\b', r'carry[- ]forward'],
            'file': 'test-mechanic.md',
        },
        {
            'num': 2,
            'title': 'Convergence Dashboard v1',
            'text': 'Build convergence panel UI. Verified: renders at 1024px. (incomplete scope) Succeeded by v2 with mobile support.',
            'verified': True,
            'v1_markers_found': [r'\(incomplete[^)]*\)', r'succeeded by'],
            'file': 'test-designer.md',
        },
        {
            'num': 3,
            'title': 'Fleet Health Baseline',
            'text': 'Establish baseline metrics for all hosts. Verified: baseline.json written. v1 - next cycle will add trend analysis.',
            'verified': True,
            'v1_markers_found': [r'\bv1\b', r'next cycle'],
            'file': 'test-orchestrator.md',
        },
    ]

    pass_count = 0
    for tc in test_cases:
        v2 = generate_v2_goal(tc)

        # Check: valid structure
        assert 'goal_id' in v2, f"Missing goal_id: {v2}"
        assert 'title' in v2 and '(v2)' in v2['title'], f"Title missing v2 marker: {v2['title']}"
        assert 'v1_ref' in v2 and tc['file'] in v2['v1_ref'], f"Missing/incorrect v1_ref: {v2['v1_ref']}"
        assert 'inherited_context' in v2, "Missing inherited_context"
        assert 'v2_verification' in v2, "Missing v2_verification"

        # Check: not in closed_topics
        is_new = check_not_in_closed_topics(v2, closed_topics)
        assert is_new, f"Goal {v2['goal_id']} already in closed_topics!"

        print(f"  PASS: {v2['title'][:50]} -> v1_ref={v2['v1_ref']}, not in closed_topics")
        pass_count += 1

    assert pass_count == 3, f"Expected 3 passes, got {pass_count}"

    # Also test that scan works (should find at least 0 candidates without error)
    candidates = scan_goal_files()
    print(f"  Live scan: {len(candidates)} closed goals with v1 markers found")

    print("\n  SELFTEST PASS: 3/3 valid v2 goals, 0 in closed_topics")
    return True


def main():
    if '--selftest' in sys.argv:
        ok = run_selftest()
        sys.exit(0 if ok else 1)

    if '--scan' in sys.argv or '--output' in sys.argv:
        candidates = scan_goal_files()
        closed_topics = load_closed_topics()

        proposals = []
        for c in candidates:
            v2 = generate_v2_goal(c)
            if check_not_in_closed_topics(v2, closed_topics):
                proposals.append(v2)

        output = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'source_candidates': len(candidates),
            'proposals': proposals,
        }

        out_file = OUTPUT_FILE
        if '--output' in sys.argv:
            idx = sys.argv.index('--output')
            if idx + 1 < len(sys.argv):
                out_file = sys.argv[idx + 1]

        os.makedirs(os.path.dirname(out_file) or '.', exist_ok=True)
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"Scanned: {len(candidates)} candidates -> {len(proposals)} v2 proposals")
        print(f"Wrote: {out_file}")
    else:
        print(__doc__)


if __name__ == '__main__':
    main()