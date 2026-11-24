"""
idle_waste.py - Idle Waste Quantification
From autoloop.jsonl, quantify:
  (a) total passes where agent received generic menu vs specific task
  (b) productive rate for each type
  (c) estimated wasted compute (passes x avg_duration)
Output: memory/researcher/idle-waste-report.md
"""
import json
import pathlib
from datetime import datetime, timedelta, timezone
from collections import defaultdict

AUTOCLOOP = pathlib.Path('memory/ops/autoloop.jsonl')
DISPATCH_LOG = pathlib.Path('memory/ops/dispatch-history.jsonl')
OUTPUT = pathlib.Path('memory/researcher/idle-waste-report.md')
WINDOW_HOURS = 24

# Signal for generic dispatch: text contains generic markers
GENERIC_MARKERS = ['take ONE concrete next step', 'work your oldest open goal', 'AUTO-LOOP', 'you have been idle']
SPECIFIC_MARKERS = ['Work ONLY YOUR section', 'from idle-maintenance-rotation', 'inject the role-specific task']


def classify_dispatch(detail: str) -> str:
    """Classify a dispatch as 'generic' or 'specific' based on text signals."""
    if not detail:
        return 'unknown'
    lower = detail.lower()
    for marker in SPECIFIC_MARKERS:
        if marker.lower() in lower:
            return 'specific'
    for marker in GENERIC_MARKERS:
        if marker.lower() in lower:
            return 'generic'
    # Default: if it contains a specific task name, it's specific
    return 'generic'


def load_passes(window_h: int = WINDOW_HOURS) -> list:
    """Load autoloop records within time window."""
    if not AUTOCLOOP.exists():
        return []
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=window_h)
    recs = []
    for line in AUTOCLOOP.read_text(encoding='utf-8').strip().split('\n'):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts_str = r.get('timestamp', '')
        try:
            ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            continue
        if ts >= cutoff:
            recs.append(r)
    return recs


def quantify(passes: list) -> dict:
    """Compute waste metrics from classified passes."""
    stats = {'generic': {'total': 0, 'productive': 0, 'durations': []},
             'specific': {'total': 0, 'productive': 0, 'durations': []}}
    
    for p in passes:
        detail = p.get('detail', '') or p.get('task', '') or ''
        dispatch_type = classify_dispatch(detail)
        if dispatch_type not in stats:
            continue
        stats[dispatch_type]['total'] += 1
        if p.get('productive'):
            stats[dispatch_type]['productive'] += 1
        stats[dispatch_type]['durations'].append(p.get('duration_s', 0))
    
    # Compute rates and waste estimates
    result = {}
    for dtype in ['generic', 'specific']:
        s = stats[dtype]
        rate = (s['productive'] / s['total'] * 100) if s['total'] > 0 else None
        avg_dur = sum(s['durations']) / len(s['durations']) if s['durations'] else 0
        # Wasted = non-productive passes x their duration
        wasted_passes = s['total'] - s['productive']
        wasted_compute_s = wasted_passes * avg_dur
        result[dtype] = {
            'total_passes': s['total'],
            'productive_passes': s['productive'],
            'rate_pct': round(rate, 1) if rate is not None else None,
            'avg_duration_s': round(avg_dur, 2),
            'wasted_passes': wasted_passes,
            'wasted_compute_s': round(wasted_compute_s, 2),
        }
    
    # Ratio: specific productive rate vs generic
    generic_rate = result['generic']['rate_pct'] or 0
    specific_rate = result['specific']['rate_pct'] or 0
    ratio = round(specific_rate / generic_rate, 2) if generic_rate > 0 else None
    
    return {
        'generic': result['generic'],
        'specific': result['specific'],
        'specific_to_generic_productivity_ratio': ratio,
        '_meta': {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'window_hours': WINDOW_HOURS,
            'total_passes_analyzed': len(passes)
        }
    }


def write_report(metrics: dict) -> str:
    """Write markdown report."""
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lines = [
        f"# Idle Waste Report ({now})",
        "",
        f"Window: last {WINDOW_HOURS}h | Passes analyzed: {metrics['_meta']['total_passes_analyzed']}",
        "",
        "## Summary",
        "",
        "| Type | Passes | Productive | Rate | Avg Duration | Wasted Compute |",
        "|------|--------|-----------|------|-------------|---------------|",
    ]
    for dtype in ['generic', 'specific']:
        m = metrics[dtype]
        rate_s = f"{m['rate_pct']}%" if m['rate_pct'] is not None else 'N/A'
        lines.append(f"| {dtype} | {m['total_passes']} | {m['productive_passes']} | {rate_s} | {m['avg_duration_s']}s | {m['wasted_compute_s']}s |")
    
    ratio = metrics.get('specific_to_generic_productivity_ratio')
    if ratio is not None:
        lines += [
            "",
            f"## Productivity Ratio: specific vs generic = **{ratio}x**",
            "",
            f"Specific tasks are {'more' if ratio > 1 else 'less'} productive than generic dispatches.",
            f"{'PASS: specific >2x generic' if ratio > 2 else 'NOTE: ratio not yet >2x (insufficient data or mixed results)'}",
        ]
    else:
        lines += ["", "## Productivity Ratio: N/A (no baseline data)"]
    
    lines += [
        "",
        "## Interpretation",
        "",
        "- **Generic dispatch** = agent receives 'take ONE concrete next step' without task specificity",
        "- **Specific dispatch** = agent receives a named task from rotation table or goal list",
        "- Higher specific-to-generic ratio indicates better dispatch quality",
    ]
    
    return '\n'.join(lines)


def main():
    passes = load_passes()
    metrics = quantify(passes)
    report = write_report(metrics)
    OUTPUT.write_text(report, encoding='utf-8')
    print(f"Wrote {OUTPUT}")
    print(f"  Total passes: {metrics['_meta']['total_passes_analyzed']}")
    for dtype in ['generic', 'specific']:
        m = metrics[dtype]
        print(f"  {dtype}: {m['productive_passes']}/{m['total_passes']} ({m['rate_pct']}%)")
    r = metrics.get('specific_to_generic_productivity_ratio')
    if r:
        print(f"  Ratio (specific/generic): {r}x")


def self_test():
    """Verify: on synthetic data with mixed generic/specific, specific has >2x rate; waste is arithmetically correct."""
    # Create synthetic passes
    synthetic = [
        # 10 generic passes, 2 productive (20%)
        *[{'timestamp': '2026-11-24T00:00:00+00:00', 'agent': 'builder', 'productive': i < 2,
           'duration_s': 30.0, 'detail': 'take ONE concrete next step'} for i in range(10)],
        # 5 specific passes, 4 productive (80%)
        *[{'timestamp': '2026-11-24T00:00:00+00:00', 'agent': 'builder', 'productive': i < 4,
           'duration_s': 60.0, 'detail': 'from idle-maintenance-rotation table'} for i in range(5)],
    ]
    
    metrics = quantify(synthetic)
    
    # Check: specific rate (80%) > 2x generic rate (20%)
    assert metrics['specific']['rate_pct'] == 80.0, f"Expected specific=80%, got {metrics['specific']['rate_pct']}"
    assert metrics['generic']['rate_pct'] == 20.0, f"Expected generic=20%, got {metrics['generic']['rate_pct']}"
    ratio = metrics['specific_to_generic_productivity_ratio']
    assert ratio > 2.0, f"Expected ratio >2x, got {ratio}"
    
    # Check: waste arithmetic - generic wasted = (10-2) * 30 = 240s
    assert metrics['generic']['wasted_compute_s'] == 240.0, f"Expected 240s, got {metrics['generic']['wasted_compute_s']}"
    # specific wasted = (5-4) * 60 = 60s
    assert metrics['specific']['wasted_compute_s'] == 60.0, f"Expected 60s, got {metrics['specific']['wasted_compute_s']}"
    
    print(f"SELF-TEST PASSED: specific={metrics['specific']['rate_pct']}%, generic={metrics['generic']['rate_pct']}%, ratio={ratio}x")
    print(f"  Waste arithmetic verified: generic=240s, specific=60s")


if __name__ == '__main__':
    import sys
    if '--test' in sys.argv:
        self_test()
    else:
        main()
