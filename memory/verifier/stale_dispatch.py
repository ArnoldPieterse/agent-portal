"""
Stale Dispatch Detector
=======================
Scans the dispatch queue and flags entries referencing goals that are:
  - status == "reached" AND reached_at > 1 hour ago (stale)

Usage:
  python memory/verifier/stale_dispatch.py           # scan live + self-test
  python memory/verifier/stale_dispatch.py --selftest # self-test only

Output: memory/verifier/stale-dispatch-report.md
"""
import json, sys, pathlib, tempfile, shutil
from datetime import datetime, timezone, timedelta

ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT = ROOT / "memory" / "verifier" / "stale-dispatch-report.md"
STALE_THRESHOLD_HOURS = 1.0


def parse_iso(ts: str) -> datetime:
    """Parse ISO-8601 timestamp to aware datetime."""
    if ts.endswith('Z'):
        ts = ts[:-1] + '+00:00'
    return datetime.fromisoformat(ts)


def detect_stale(queue: list, now: datetime) -> list:
    """Return list of stale entries from dispatch queue.
    
    An entry is stale if it references a goal with:
      - status == 'reached'
      - reached_at > STALE_THRESHOLD_HOURS before `now`
    """
    stale = []
    threshold = timedelta(hours=STALE_THRESHOLD_HOURS)
    for i, entry in enumerate(queue):
        status = entry.get('status', '').lower()
        if status != 'reached':
            continue
        reached_at_str = entry.get('reached_at')
        if not reached_at_str:
            continue
        try:
            reached_at = parse_iso(reached_at_str)
        except (ValueError, TypeError):
            continue
        age = now - reached_at
        if age > threshold:
            stale.append({
                'index': i,
                'goal_id': entry.get('goal_id', f'entry_{i}'),
                'agent': entry.get('agent', 'unknown'),
                'reached_at': reached_at_str,
                'age_hours': round(age.total_seconds() / 3600, 2),
            })
    return stale


def write_report(stale: list, total: int, now: datetime) -> pathlib.Path:
    """Write markdown report."""
    lines = [
        "# Stale Dispatch Report",
        f"",f"Generated: {now.isoformat()}",f"Threshold: >{STALE_THRESHOLD_HOURS}h since reached",
        f"",f"## Summary",f"",f"- Total dispatch entries scanned: **{total}**",
f"- Stale entries detected: **{len(stale)}**",
    ]
    if stale:
        lines += ["", "## Stale Entries", ""]
        for s in stale:
            lines.append(
                f"| {s['goal_id']} | {s['agent']} | {s['reached_at']} | {s['age_hours']}h |"
            )
    else:
        lines += ["", "No stale entries detected. Dispatch queue is clean."]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding='utf-8')
    return REPORT


def selftest() -> bool:
    """Run self-test with synthetic data. Returns True if all pass."""
    now = datetime(2026, 11, 24, 12, 0, 0, tzinfo=timezone.utc)
    results = []

    # Test 1: clean data -> 0 stale
    clean_queue = [
        {'goal_id': 'g1', 'agent': 'builder', 'status': 'open', 'reached_at': None},
        {'goal_id': 'g2', 'agent': 'verifier', 'status': 'reached',
         'reached_at': (now - timedelta(minutes=30)).isoformat()},  # only 30min -> not stale
        {'goal_id': 'g3', 'agent': 'scribe', 'status': 'open', 'reached_at': None},
    ]
    stale = detect_stale(clean_queue, now)
    r1 = len(stale) == 0
    results.append(('clean_data_0_stale', r1))

    # Test 2: 3 stale entries detected
    dirty_queue = [
        {'goal_id': 'stale-1', 'agent': 'builder', 'status': 'reached',
         'reached_at': (now - timedelta(hours=2)).isoformat()},
        {'goal_id': 'fresh-1', 'agent': 'verifier', 'status': 'reached',
         'reached_at': (now - timedelta(minutes=10)).isoformat()},  # fresh
        {'goal_id': 'stale-2', 'agent': 'scribe', 'status': 'reached',
         'reached_at': (now - timedelta(hours=5)).isoformat()},
        {'goal_id': 'open-1', 'agent': 'researcher', 'status': 'open', 'reached_at': None},
        {'goal_id': 'stale-3', 'agent': 'designer', 'status': 'reached',
         'reached_at': (now - timedelta(hours=24)).isoformat()},
    ]
    stale = detect_stale(dirty_queue, now)
    r2 = len(stale) == 3
    results.append(('dirty_3_stale_detected', r2))

    # Test 3: correct goal IDs in output
    ids = {s['goal_id'] for s in stale}
    r3 = ids == {'stale-1', 'stale-2', 'stale-3'}
    results.append(('correct_ids', r3))

    # Test 4: boundary - exactly 1h is NOT stale (strict >)
    boundary_queue = [
        {'goal_id': 'boundary', 'agent': 'x', 'status': 'reached',
         'reached_at': (now - timedelta(hours=1)).isoformat()},
    ]
    stale_b = detect_stale(boundary_queue, now)
    r4 = len(stale_b) == 0  # exactly 1h is not > 1h
    results.append(('boundary_1h_not_stale', r4))

    # Test 5: just over 1h IS stale
    just_over_queue = [
        {'goal_id': 'just-over', 'agent': 'x', 'status': 'reached',
         'reached_at': (now - timedelta(hours=1, minutes=1)).isoformat()},
    ]
    stale_o = detect_stale(just_over_queue, now)
    r5 = len(stale_o) == 1
    results.append(('just_over_1h_is_stale', r5))

    # Print results
    print("STALE DISPATCH DETECTOR - SELFTEST")
    print("=" * 50)
    all_pass = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"  [{status}] {name}")
    print("-" * 50)
    print(f"RESULT: {'PASS' if all_pass else 'FAIL'} ({sum(1 for _, p in results if p)}/{len(results)} tests)")
    return all_pass


def scan_live() -> bool:
    """Scan live dispatch data (next10.json or goal files)."""
    now = datetime.now(timezone.utc)
    queue = []

    # Try next10.json
    n10_path = ROOT / "memory" / "goals" / "next10.json"
    if n10_path.exists():
        try:
            data = json.loads(n10_path.read_text(encoding='utf-8'))
            items = data.get('next10', [])
            for item in items:
                queue.append({
                    'goal_id': item.get('id', item.get('goal_id', '')),
                    'agent': item.get('lane', item.get('agent', '')),
                    'status': item.get('status', 'open'),
                    'reached_at': item.get('reached_at'),
                })
        except (json.JSONDecodeError, KeyError):
            pass

    # Also scan goal files for reached markers with timestamps
    goals_dir = ROOT / "memory" / "goals"
    if goals_dir.exists():
        for gf in goals_dir.glob('*.md'):
            if gf.name in ('INDEX.md', 'next10.json', 'forecast-latest.md'):
                continue
            text = gf.read_text(encoding='utf-8')
            for line in text.split('\n'):
                if '(verified:' in line and 'reached' not in line.lower():
                    # Extract goal number from line start
                    import re
                    m = re.match(r'^\s*(\d+)\.\s', line)
                    if m:
                        # Parse timestamp from verified marker
                        ts_match = re.search(r'verified:\s*([\d-]+)\s+([\d:]+)', line)
                        if ts_match:
                            try:
                                ts = datetime.fromisoformat(
                                    f"{ts_match.group(1)}T{ts_match.group(2)}"
                                ).replace(tzinfo=timezone.utc)
                                queue.append({
                                    'goal_id': f"{gf.stem}#{m.group(1)}",
                                    'agent': gf.stem,
                                    'status': 'reached',
                                    'reached_at': ts.isoformat(),
                                })
                            except ValueError:
                                pass

    stale = detect_stale(queue, now)
    path = write_report(stale, len(queue), now)
    print(f"LIVE SCAN: {len(queue)} entries scanned, {len(stale)} stale")
    print(f"Report written: {path.relative_to(ROOT)}")
    return True


def main():
    if '--selftest' in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    
    # Default: self-test + live scan
    print("SELF-TEST:")
    ok = selftest()
    if not ok:
        print("\nFATAL: self-test failed, aborting")
        sys.exit(1)
    print("\nLIVE SCAN:")
    scan_live()


if __name__ == '__main__':
    main()
