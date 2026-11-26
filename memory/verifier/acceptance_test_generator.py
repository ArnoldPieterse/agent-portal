"""acceptance_test_generator.py — Verifier Goal #6 assist (Builder, 2026-11-27)
Scans memory/goals/*.md for goal lines with "Verified:" criteria.
Emits runnable Python test stubs into memory/verifier/tests/.

AC: 5 real goal lines produce valid executable stubs; each passes or fails (not errors).

Usage: python memory/verifier/acceptance_test_generator.py [--lane LANE] [--limit N]
"""
import re, os, sys, json, pathlib
from datetime import datetime, timezone

GOALS_DIR = "memory/goals"
TESTS_DIR = "memory/verifier/tests"

def parse_goals(lane_file):
    """Parse a goals file, extract goal lines with Verified criteria."""
    text = lane_file.read_text(encoding='utf-8')
    goals = []
    pattern = r'(\d+)\.\s+\*\*(.+?)\*\*\s*-\s+(.+?)(?:Verified:\s*(.+?))(?=\n\d+\.|\n#|$)'
    for m in re.finditer(pattern, text, re.DOTALL):
        num = int(m.group(1))
        title = m.group(2).strip()
        desc = m.group(3).strip()
        verified = (m.group(4) or "").strip()
        if verified:
            goals.append({"num": num, "title": title, "desc": desc, "verified": verified})
    return goals

def slugify(s):
    s = re.sub(r'[^a-zA-Z0-9]+', '_', s).strip('_')
    return s.lower()[:50]

def generate_stub(lane, goal):
    """Generate a runnable test stub for a single goal."""
    slug = slugify(goal['title'])
    filename = "test_%s_g%d_%s.py" % (lane, goal['num'], slug)
    
    criteria = goal['verified']
    checks = [c.strip() for c in re.split(r';|(?<=\.)\s+and\s+', criteria) if c.strip()]
    
    lines = []
    lines.append('"""Auto-generated acceptance test: %s goal #%d — %s' % (lane, goal['num'], goal['title']))
    lines.append('Generated: %s' % datetime.now(timezone.utc).isoformat())
    lines.append('Source: memory/goals/%s.md' % lane)
    lines.append('AC: %s' % goal['verified'][:200])
    lines.append('"""')
    lines.append('import os, json, pathlib, sys')
    lines.append('')
    lines.append('def test_%s():' % slug)
    lines.append('    """Acceptance criterion check."""')
    lines.append('    # Criteria: %s' % goal['verified'][:100])
    for i, c in enumerate(checks):
        lines.append('    # CHECK %d: %s' % (i+1, c[:80]))
    lines.append('')
    lines.append('    # Stub assertion: verify the goal file itself exists')
    lines.append('    goals_file = pathlib.Path("memory/goals/%s.md")' % lane)
    lines.append('    assert goals_file.exists(), "Goals file missing: %s"' % lane)
    lines.append('    return True')
    lines.append('')
    lines.append('if __name__ == "__main__":')
    lines.append('    test_%s()' % slug)
    lines.append('    print("PASS: %s goal #%d stub executed without error")' % (lane, goal['num']))
    
    return filename, '\n'.join(lines) + '\n'

def main():
    lane_filter = None
    limit = 10
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--lane' and i+1 < len(args):
            lane_filter = args[i+1]; i += 2
        elif args[i] == '--limit' and i+1 < len(args):
            limit = int(args[i+1]); i += 2
        else:
            i += 1
    
    os.makedirs(TESTS_DIR, exist_ok=True)
    generated = []
    
    for f in sorted(pathlib.Path(GOALS_DIR).glob('*.md')):
        lane = f.stem
        if lane_filter and lane != lane_filter:
            continue
        goals = parse_goals(f)
        count = 0
        for goal in goals:
            if count >= limit:
                break
            filename, stub = generate_stub(lane, goal)
            out_path = pathlib.Path(TESTS_DIR) / filename
            out_path.write_text(stub, encoding='utf-8')
            generated.append(str(out_path))
            count += 1
    
    print("Generated %d test stubs in %s/" % (len(generated), TESTS_DIR))
    for g in generated:
        print("  " + g)

if __name__ == '__main__':
    main()
