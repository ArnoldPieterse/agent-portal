"""
idle_productivity.py - Productivity Baseline Measurement
Measures per-agent productive-pass rate over last 24h.
Sources: autoloop.jsonl (pass records), git log (file changes as corroboration).
Output: memory/ops/productivity-baseline-YYYY-MM-DD.json
"""
import json
import pathlib
import subprocess
from datetime import datetime, timedelta, timezone
from collections import defaultdict

AUTOCLOOP = pathlib.Path('memory/ops/autoloop.jsonl')
OUTPUT_DIR = pathlib.Path('memory/ops')
AGENT_NAMES = ["orchestrator", "researcher", "verifier", "scribe", "designer", "builder", "archivist", "mechanic"]


def parse_iso(ts: str) -> datetime:
    """Parse ISO-8601 timestamp string to aware datetime."""
    try:
        # Handle +00:00 and Z suffixes
        ts_clean = ts.replace('Z', '+00:00')
        return datetime.fromisoformat(ts_clean)
    except (ValueError, AttributeError):
        return None


def load_autoloop(window_h: int = 24) -> list:
    """Load autoloop records within the time window."""
    if not AUTOCLOOP.exists():
        return []
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=window_h)
    records = []
    for line in AUTOCLOOP.read_text(encoding='utf-8').strip().split('\n'):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = parse_iso(rec.get('timestamp', ''))
        if ts and ts >= cutoff:
            records.append(rec)
    return records


def count_git_changes(window_h: int = 24) -> dict:
    """Count file changes per agent from git log (best-effort)."""
    try:
        since = f'{window_h} hours ago'
        result = subprocess.run(
            ['git', 'log', f'--since={since}', '--format=%an|%ae'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return {}
        authors = defaultdict(int)
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                name = line.split('|')[0].strip().lower()
                authors[name] += 1
        # Map to agent names
        changes = {}
        for agent in AGENT_NAMES:
            changes[agent] = authors.get(agent, 0)
        return changes
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return {}


def measure(window_h: int = 24) -> dict:
    """Main measurement: per-agent productive pass rate."""
    records = load_autoloop(window_h)
    git_changes = count_git_changes(window_h)

    # Aggregate from autoloop.jsonl
    stats = defaultdict(lambda: {'total': 0, 'productive': 0, 'evidence_files': 0})
    for rec in records:
        agent = rec.get('agent', 'unknown').lower()
        if agent not in AGENT_NAMES:
            continue
        stats[agent]['total'] += 1
        if rec.get('productive'):
            stats[agent]['productive'] += 1
        stats[agent]['evidence_files'] += len(rec.get('evidence_files', []))

    # Build output - include all agents even if 0 passes (rate=null means no data)
    baseline = {}
    now_iso = datetime.now(timezone.utc).isoformat()
    for agent in AGENT_NAMES:
        s = stats[agent]
        rate = round(s['productive'] / s['total'] * 100, 1) if s['total'] > 0 else None
        entry = {
            'rate': rate,
            'total_passes': s['total'],
            'productive_passes': s['productive'],
            'evidence_files': s['evidence_files'],
            'git_commits_24h': git_changes.get(agent, 0),
        }
        # Mark source: real if autoloop has data for this agent, simulated otherwise
        entry['source'] = 'measured' if s['total'] > 0 else 'no_data'
        baseline[agent] = entry

    return {
        '_meta': {
            'generated_at': now_iso,
            'window_hours': window_h,
            'autoloop_records_in_window': len(records),
            'note': 'rate=null means no passes recorded for agent in window'
        },
        **baseline
    }


def check_flag(agent: str, current_rate) -> bool:
    """Flag if agent rate <30% for 2+ consecutive days (check prior day baseline)."""
    if current_rate is None or current_rate >= 30.0:
        return False
    # Check yesterday's baseline
    yest = datetime.now(timezone.utc) - timedelta(days=1)
    yest_str = yest.strftime('%Y-%m-%d')
    yest_path = OUTPUT_DIR / f'productivity-baseline-{yest_str}.json'
    if not yest_path.exists():
        return False
    try:
        prev = json.loads(yest_path.read_text(encoding='utf-8'))
        prev_rate = prev.get(agent, {}).get('rate')
        if prev_rate is None or prev_rate >= 30.0:
            return False
        # Check day-before-yesterday too (need 2+ consecutive)
        dbt = datetime.now(timezone.utc) - timedelta(days=2)
        dbt_str = dbt.strftime('%Y-%m-%d')
        dbt_path = OUTPUT_DIR / f'productivity-baseline-{dbt_str}.json'
        if dbt_path.exists():
            prev2 = json.loads(dbt_path.read_text(encoding='utf-8'))
            if prev2.get(agent, {}).get('rate') is not None and prev2[agent]['rate'] < 30.0:
                return True
        # If yesterday was also below threshold but we only have 2 days of data,
        # that's enough for "2+ consecutive"
        return True
    except (json.JSONDecodeError, KeyError):
        return False


def main():
    result = measure()
    # Add flag field per agent
    for agent in AGENT_NAMES:
        result[agent]['flag'] = check_flag(agent, result[agent]['rate'])

    date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    out_path = OUTPUT_DIR / f'productivity-baseline-{date_str}.json'
    out_path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    # Also write canonical path
    canonical = OUTPUT_DIR / 'productivity-baseline.json'
    canonical.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(f"Wrote {out_path}")
    print(f"  autoloop records in window: {result['_meta']['autoloop_records_in_window']}")
    for agent in AGENT_NAMES:
        e = result[agent]
        r = f"{e['rate']}%" if e['rate'] is not None else 'N/A'
        flag_s = " **FLAGGED**" if e.get('flag') else ""
        print(f"  {agent}: {r} ({e['productive_passes']}/{e['total_passes']} passes){flag_s}")


def self_test():
    """Self-test: verify flags work on synthetic data with known below-threshold agents."""
    import tempfile, os, shutil
    test_dir = pathlib.Path(tempfile.mkdtemp())
    ops_dir = test_dir / 'ops'
    ops_dir.mkdir()
    
    # Simulate 3 days of low productivity for 'builder' (rate=10%)
    for days_ago in range(3):
        dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
        ds = dt.strftime('%Y-%m-%d')
        data = {
            '_meta': {'generated_at': dt.isoformat()},
            'builder': {'rate': 10.0, 'total_passes': 20, 'productive_passes': 2},
            'verifier': {'rate': 80.0, 'total_passes': 10, 'productive_passes': 8},
        }
        (ops_dir / f'productivity-baseline-{ds}.json').write_text(json.dumps(data), encoding='utf-8')
    
    # Now test: builder should be flagged (3 days < 30%), verifier should not
    # We need to monkey-patch OUTPUT_DIR temporarily
    global OUTPUT_DIR
    orig_dir = OUTPUT_DIR
    OUTPUT_DIR = ops_dir
    
    result = measure()  # Will read empty autoloop -> all rates null
    for agent in AGENT_NAMES:
        if agent not in result:
            result[agent] = {'rate': None, 'total_passes': 0, 'productive_passes': 0}
    # Manually set rates to simulate
    result['builder'] = {'rate': 15.0, 'total_passes': 20, 'productive_passes': 3}
    result['verifier'] = {'rate': 75.0, 'total_passes': 10, 'productive_passes': 7.5}
    
    builder_flag = check_flag('builder', 15.0)
    verifier_flag = check_flag('verifier', 75.0)
    
    OUTPUT_DIR = orig_dir
    shutil.rmtree(test_dir, ignore_errors=True)
    
    assert builder_flag == True, f"Expected builder flagged, got {builder_flag}"
    assert verifier_flag == False, f"Expected verifier NOT flagged, got {verifier_flag}"
    print("SELF-TEST PASSED: flags correct on synthetic data")


if __name__ == '__main__':
    import sys
    if '--test' in sys.argv:
        self_test()
    else:
        main()


if __name__ == '__main__':
    main()
