#!/usr/bin/env python3
"""Cross-Agent Handoff Detector - scans agent messages for assist patterns.

Detects when one agent is working another's goal (cross-agent assist) and
auto-generates structured handoff notes in memory/handoffs/.

Usage:
    python memory/orchestrator/handoff_detector.py           # scan + generate notes
    python memory/orchestrator/handoff_detector.py --selftest  # verify with synthetic data
"""
import json, sys, re, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HANDOFFS_DIR = ROOT / 'memory' / 'handoffs'
GOALS_DIR = ROOT / 'memory' / 'goals'
BUILDER_DIR = ROOT / 'memory' / 'builder'
EVIDENCE_PATTERN = re.compile(r'(?:assist|working on behalf of|on behalf of|cross-assist)', re.IGNORECASE)
OWNERSHIP_PATTERN = re.compile(r'(?:owner[:\s]+|goal.*?of[:\s]+)([a-z_]+)', re.IGNORECASE)

# Known agents
AGENTS = {'archivist', 'builder', 'designer', 'mechanic', 'orchestrator',
          'researcher', 'scribe', 'verifier', 'pixel', 'forge', 'lumen', 'reel', 'splice'}


def scan_goal_files():
    """Scan goal files for assist patterns. Returns list of assist events."""
    events = []
    if not GOALS_DIR.exists():
        return events

    for gf in sorted(GOALS_DIR.glob('*.md')):
        agent_name = gf.stem  # filename = agent name
        text = gf.read_text(encoding='utf-8', errors='replace')

        # Look for "Assist (owner X)" or similar patterns
        for line in text.split('\n'):
            if EVIDENCE_PATTERN.search(line):
                # Extract owner if present
                owner_match = re.search(r'\(owner:\s*([A-Za-z_]+)\)', line)
                if not owner_match:
                    owner_match = re.search(r'(?:owner|for)[:\s]+([A-Za-z_]+)', line, re.IGNORECASE)
                owner = owner_match.group(1).lower() if owner_match else None
                scope = line.strip().lstrip('#-0123456789. ')[:200]

                events.append({
                    'assister': agent_name,
                    'owner': owner or 'unknown',
                    'scope': scope,
                    'source_file': str(gf.relative_to(ROOT)),
                    'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                })
    return events


def scan_evidence_files():
    """Scan builder/ and other evidence files for assist markers."""
    events = []
    search_dirs = [BUILDER_DIR, ROOT / 'memory' / 'mechanic', ROOT / 'memory' / 'researcher']

    for d in search_dirs:
        if not d.exists():
            continue
        for f in sorted(d.glob('*assist*.md')) + sorted(d.glob('*cross*.md')):
            text = f.read_text(encoding='utf-8', errors='replace')
            # Extract assister from filename or content
            assister_match = re.search(r'(?:from|by)[:\s]+([a-z_]+)', text, re.IGNORECASE)
            owner_match = re.search(r'(?:owner|for)[:\s]+([A-Za-z_]+)', text, re.IGNORECASE)

            # Try to determine which agent this belongs to based on directory
            if 'builder' in str(d).lower():
                assister = 'builder'
            elif 'mechanic' in str(d).lower():
                assister = 'mechanic'
            else:
                assister = f.stem.split('_')[0] if '_' in f.stem else 'unknown'

            owner = owner_match.group(1).lower() if owner_match else 'unknown'
            first_line = text.strip().split('\n')[0][:200]

            events.append({
                'assister': assister,
                'owner': owner,
                'scope': first_line,
                'source_file': str(f.relative_to(ROOT)),
                'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            })
    return events


def generate_handoff_note(event):
    """Generate a handoff note file for an assist event."""
    HANDOFFS_DIR.mkdir(parents=True, exist_ok=True)

    today = datetime.date.today().isoformat()
    filename = f"{today}-{event['assister']}-to-{event['owner']}.md"
    filepath = HANDOFFS_DIR / filename

    if filepath.exists():
        return None  # already exists, skip (idempotent)

    content = f"""# Handoff: {event['assister']} → {event['owner']} (assist)

*Generated {event['timestamp']} | Type: cross-agent assist*


---

**Assister:** {event['assister']}
**Owner:** {event['owner']}
**Scope:** {event['scope']}
**Completion criteria:** Assister delivers working artifact; owner reviews and accepts.
**Source:** `{event['source_file']}`
"""
    filepath.write_text(content, encoding='utf-8')
    return str(filepath.relative_to(ROOT))


def run_scan():
    events = scan_goal_files() + scan_evidence_files()

    # Filter: only keep events where both assister and owner are known agents
    valid_events = [e for e in events if e['assister'] in AGENTS and e['owner'] in AGENTS]

    if not valid_events:
        print('No cross-agent assist patterns detected (with known agent pairs).')
        return 0

    generated = 0
    for event in valid_events:
        path = generate_handoff_note(event)
        if path:
            generated += 1
            print(f'  Generated: {path}')

    # Deduplicate by (assister, owner) pair
    seen = set()
    unique_events = []
    for e in events:
        key = (e['assister'], e['owner'])
        if key not in seen:
            seen.add(key)
            unique_events.append(e)

    print(f'\nDetected {len(events)} assist event(s), {len(unique_events)} unique pair(s), {generated} new note(s) generated.')
    return generated


def selftest():
    """Verify with synthetic scenarios."""
    import tempfile, shutil
    passed = 0
    failed = 0

    # Test 1: Detect assist in goal file content
    test_dir = Path(tempfile.mkdtemp())
    try:
        goals = test_dir / 'memory' / 'goals'
        goals.mkdir(parents=True)
        (goals / 'builder.md').write_text(
            '1. **Something** - normal goal\n'
            '6. **Assist (owner Mechanic):** seat_probe.py latency work\n',
            encoding='utf-8'
        )
        # Patch ROOT for test
        global GOALS_DIR, HANDOFFS_DIR, BUILDER_DIR
        orig_goals, orig_handoffs, orig_builder = GOALS_DIR, HANDOFFS_DIR, BUILDER_DIR
        GOALS_DIR = goals
        HANDOFFS_DIR = test_dir / 'memory' / 'handoffs'
        BUILDER_DIR = test_dir / 'memory' / 'builder'
        BUILDER_DIR.mkdir(parents=True)

        events = scan_goal_files()
        if len(events) == 1 and events[0]['assister'] == 'builder' and events[0]['owner'] == 'mechanic':
            passed += 1
            print('  PASS: assist pattern detected in goal file')
        else:
            failed += 1
            print(f'  FAIL: expected 1 event (builder->mechanic), got {events}')

        # Test 2: No false positive on non-assist content
        (goals / 'verifier.md').write_text(
            '1. **Test Battery** - run tests and report\n'
            '2. **Audit** - check file integrity\n',
            encoding='utf-8'
        )
        events = scan_goal_files()
        # Should only find the builder one
        vp_events = [e for e in events if e['assister'] == 'verifier']
        if len(vp_events) == 0:
            passed += 1
            print('  PASS: no false positive on non-assist content')
        else:
            failed += 1
            print(f'  FAIL: false positive on verifier: {vp_events}')

        # Test 3: Generate valid handoff note
        event = {'assister': 'builder', 'owner': 'mechanic', 'scope': 'seat_probe work',
                 'source_file': 'memory/goals/builder.md', 'timestamp': '2026-11-25T00:00:00+00:00'}
        path = generate_handoff_note(event)
        if path and Path(path).exists():
            content = Path(path).read_text(encoding='utf-8')
            if 'builder' in content and 'mechanic' in content and 'Scope:' in content:
                passed += 1
                print('  PASS: handoff note generated with correct format')
            else:
                failed += 1
                print(f'  FAIL: handoff note missing fields: {content[:200]}')
        else:
            failed += 1
            print('  FAIL: no handoff note generated')

        # Test 4: Idempotent - second call doesn't duplicate
        path2 = generate_handoff_note(event)
        if path2 is None:
            passed += 1
            print('  PASS: idempotent (no duplicate note)')
        else:
            failed += 1
            print(f'  FAIL: duplicate note generated: {path2}')

        # Test 5: Evidence file scan
        ev_file = BUILDER_DIR / 'assist_mechanic_test.md'
        ev_file.write_text('# Assist (owner Mechanic): test scope\nDetails here.\n', encoding='utf-8')
        events = scan_evidence_files()
        if any(e['assister'] == 'builder' and e['owner'] in ('mechanic', 'unknown') for e in events):
            passed += 1
            print('  PASS: evidence file assist detected')
        else:
            failed += 1
            print(f'  FAIL: evidence file not detected: {events}')

    finally:
        GOALS_DIR, HANDOFFS_DIR, BUILDER_DIR = orig_goals, orig_handoffs, orig_builder
        shutil.rmtree(test_dir, ignore_errors=True)

    print(f'\nSelftest: {passed}/5 PASS, {failed}/5 FAIL')
    return failed == 0


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    else:
        run_scan()
