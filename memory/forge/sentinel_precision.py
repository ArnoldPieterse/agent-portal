"""
sentinel_precision.py - Regression Sentinel Precision Test (Forge goal #5, cycle 19)

Drives the REAL orchestrator/convergence_sentinel.run() over N synthetic cycles
and measures precision/recall/FPR of its regression detector against DESIGNED
ground truth (not re-derived from the same threshold, so it is not tautological).

Ground-truth design (fixed seed -> reproducible):
  - TRUE regressions : score drop in [6, 14] pts (clearly above the 5pt threshold)
                       -> detector MUST fire. Recall target = 1.0.
  - NOISE            : rises/flat (delta >= 0) OR small drops in [0, 4.5] pts
                       (below threshold) -> detector must stay SILENT.
                       FPR target < 0.1.
A separate boundary table documents behavior at the exact threshold edge
(4.9 / 5.0 / 5.1) using the sentinel's own `drop > 5` rule as ground truth there.

Acceptance: recall == 1.0 on true regressions; FPR < 0.1 on noise; a report is written.

Usage:
  python memory/forge/sentinel_precision.py            # run, write report, exit 0/1
  python memory/forge/sentinel_precision.py --cycles 20 --seed 42
"""
import argparse
import importlib.util
import json
import os
import random
import sys
import tempfile
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SENTINEL_PATH = os.path.join(HERE, 'memory', 'orchestrator', 'convergence_sentinel.py')
REPORT_JSON = os.path.join(HERE, 'memory', 'forge', 'sentinel-precision-report.json')
REPORT_MD = os.path.join(HERE, 'memory', 'forge', 'sentinel-precision-report.md')
THRESHOLD = 5.0
COMPS = ['pass_autonomy', 'duration_score', 'rework_score', 'trend_score']
LANE_MAP = {'pass_autonomy': 'orchestrator', 'duration_score': 'mechanic',
            'rework_score': 'builder', 'trend_score': 'scribe'}


def _load_sentinel():
    spec = importlib.util.spec_from_file_location('convergence_sentinel', SENTINEL_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _mk_breakdown(rng, base, drop_component=None, drop_mag=0.0):
    """Build a component breakdown; optionally drop one component by drop_mag."""
    cb = {}
    for c in COMPS:
        val = base + rng.uniform(-3, 3)
        if c == drop_component:
            val -= drop_mag
        cb[c] = round(max(0.0, min(100.0, val)), 2)
    return cb


def _scenario(rng, kind):
    """Return (prev_score, curr_score, prev_cb, curr_cb, label) for one cycle."""
    base = rng.uniform(55, 80)
    prev_score = round(base, 2)
    if kind == 'regression':
        drop = rng.uniform(6.0, 14.0)
        curr_score = round(prev_score - drop, 2)
        worst = rng.choice(COMPS)
        # push the total drop into a single component so attribution is clean
        comp_drop = min(drop, 30.0)
        prev_cb = _mk_breakdown(rng, base)
        curr_cb = _mk_breakdown(rng, base - drop * 0.15, drop_component=worst, drop_mag=comp_drop)
        label = True
    else:  # noise
        r = rng.random()
        if r < 0.5:
            delta = rng.uniform(0.0, 8.0)      # rise / flat (acceleration or stable)
        else:
            delta = -rng.uniform(0.0, 4.5)     # small drop, below threshold
        curr_score = round(prev_score + delta, 2)
        prev_cb = _mk_breakdown(rng, base)
        curr_cb = _mk_breakdown(rng, base + delta * 0.2)
        label = False
    return prev_score, curr_score, prev_cb, curr_cb, label


def _run_one(sentinel, prev_score, curr_score, prev_cb, curr_cb):
    """Feed one cycle through the real sentinel.run(); return (fired, status)."""
    with tempfile.TemporaryDirectory() as tmp:
        import pathlib
        tf = pathlib.Path(tmp) / 'trend.jsonl'
        cf = pathlib.Path(tmp) / 'current.json'
        af = pathlib.Path(tmp) / 'alerts.jsonl'
        gd = pathlib.Path(tmp) / 'goals'
        gd.mkdir()
        # ensure the responsible lane's goals file exists so goal-open can succeed
        for lane in LANE_MAP.values():
            (gd / f'{lane}.md').write_text(f'# {lane} Goals\n\n1. **seed** - x\n', encoding='utf-8')
        tf.write_text(json.dumps({'cycle': 1, 'score': prev_score,
                                  'component_breakdown': prev_cb}) + '\n', encoding='utf-8')
        cf.write_text(json.dumps({'score': curr_score, 'components': curr_cb}), encoding='utf-8')
        res = sentinel.run(tf, cf, af, gd, threshold=THRESHOLD)
        fired = (res.get('status') == 'regression_detected')
        return fired, res.get('status'), res.get('event', {}).get('responsible_lane')


def main():
    ap = argparse.ArgumentParser(description='Regression Sentinel Precision Test')
    ap.add_argument('--cycles', type=int, default=20)
    ap.add_argument('--seed', type=int, default=42)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    sentinel = _load_sentinel()

    # Build N scenarios: half regressions, half noise (interleaved, shuffled order).
    n = args.cycles
    n_reg = n // 2
    kinds = ['regression'] * n_reg + ['noise'] * (n - n_reg)
    rng.shuffle(kinds)

    tp = fp = fn = tn = 0
    rows = []
    for i, kind in enumerate(kinds):
        prev_score, curr_score, prev_cb, curr_cb, label = _scenario(rng, kind)
        fired, status, lane = _run_one(sentinel, prev_score, curr_score, prev_cb, curr_cb)
        drop = round(prev_score - curr_score, 2)
        if label and fired:
            tp += 1
        elif (not label) and fired:
            fp += 1
        elif label and not fired:
            fn += 1
        else:
            tn += 1
        rows.append({'idx': i, 'kind': kind, 'prev': prev_score, 'curr': curr_score,
                     'drop_pts': drop, 'label_regression': label, 'fired': fired,
                     'status': status, 'attributed_lane': lane})

    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    accuracy = (tp + tn) / n if n else 0.0

    # Boundary behavior at the exact threshold edge (ground truth = sentinel's own >5 rule).
    boundary = []
    for d in (4.9, 5.0, 5.1):
        ps = 70.0
        cs = round(ps - d, 2)
        pcb = _mk_breakdown(random.Random(1), 70.0)
        ccb = _mk_breakdown(random.Random(1), 70.0, drop_component='pass_autonomy', drop_mag=d)
        fired, status, lane = _run_one(sentinel, ps, cs, pcb, ccb)
        gt_fire = d > THRESHOLD
        boundary.append({'drop': d, 'fired': fired, 'ground_truth_fire': gt_fire,
                         'correct': fired == gt_fire})
    boundary_ok = all(b['correct'] for b in boundary)

    report = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'sentinel': 'memory/orchestrator/convergence_sentinel.py',
        'threshold': THRESHOLD,
        'seed': args.seed,
        'cycles': n,
        'confusion': {'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn},
        'precision': round(precision, 4),
        'recall': round(recall, 4),
        'fpr': round(fpr, 4),
        'accuracy': round(accuracy, 4),
        'boundary': boundary,
        'boundary_ok': boundary_ok,
        'acceptance': {
            'recall_eq_1.0': recall == 1.0,
            'fpr_lt_0.1': fpr < 0.1,
            'pass': (recall == 1.0 and fpr < 0.1),
        },
        'rows': rows,
    }

    os.makedirs(os.path.dirname(REPORT_JSON), exist_ok=True)
    with open(REPORT_JSON, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    md = [
        '# Regression Sentinel Precision Test - report (2026-11-26)',
        '',
        f'Sentinel under test: `{report["sentinel"]}` (real run(), threshold={THRESHOLD})',
        f'Seed={args.seed}, cycles={n} ({n_reg} true regressions + {n - n_reg} noise).',
        '',
        '## Metrics',
        f'- Confusion: TP={tp} FP={fp} FN={fn} TN={tn}',
        f'- Precision = {precision:.4f}',
        f'- Recall    = {recall:.4f}',
        f'- FPR       = {fpr:.4f}',
        f'- Accuracy  = {accuracy:.4f}',
        '',
        '## Boundary behavior (ground truth = sentinel\'s own `drop > 5` rule)',
        '| drop_pts | fired | ground_truth | correct |',
        '|---|---|---|---|',
    ] + [f'| {b["drop"]} | {b["fired"]} | {b["ground_truth_fire"]} | {b["correct"]} |' for b in boundary] + [
        '',
        f'## Acceptance: recall==1.0 -> {report["acceptance"]["recall_eq_1.0"]}; '
        f'FPR<0.1 -> {report["acceptance"]["fpr_lt_0.1"]}; PASS -> {report["acceptance"]["pass"]}',
        '',
    ]
    with open(REPORT_MD, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))

    print('=== sentinel_precision.py ===')
    print(f'  cycles={n} seed={args.seed} threshold={THRESHOLD}')
    print(f'  confusion TP={tp} FP={fp} FN={fn} TN={tn}')
    print(f'  precision={precision:.4f} recall={recall:.4f} fpr={fpr:.4f} accuracy={accuracy:.4f}')
    for b in boundary:
        print(f'  boundary drop={b["drop"]}: fired={b["fired"]} gt={b["ground_truth_fire"]} {"OK" if b["correct"] else "MISMATCH"}')
    ok = report['acceptance']['pass'] and boundary_ok
    print(f'  reports: {os.path.relpath(REPORT_JSON, HERE)} + ' + os.path.relpath(REPORT_MD, HERE))
    print(f'RESULT: {"ALL PASS" if ok else "FAILURES PRESENT"}')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
