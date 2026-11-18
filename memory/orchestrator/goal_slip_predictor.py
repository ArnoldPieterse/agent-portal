#!/usr/bin/env python3
"""goal_slip_predictor.py - Predict P(slip > 3 days) for fleet goals.

Features: goal type (measurement/build/verify/research/ops), agent, dependency depth.
Method: weighted Naive Bayes with Laplace smoothing + threshold search.
Validation: 5-fold CV on combined cycle-1+2 data (cycle-3 used for prediction only).

Usage:
    python goal_slip_predictor.py              # train + validate + print prediction table
    python goal_slip_predictor.py --predict    # predict slip risk for all currently-open goals
"""
import json, pathlib, re, random, sys
from collections import Counter

VALID_AGENTS = {'archivist', 'builder', 'designer', 'mechanic',
                'orchestrator', 'researcher', 'scribe', 'verifier'}

# Dependency depth from cycle-2 dependency map (agent, goal_num) -> depth
DEP_DEPTH_MAP = {
    # Chain 1: SLO pipeline (depth 1)
    ('mechanic', 4): 1, ('builder', 8): 1, ('verifier', 4): 1,
    # Chain 2: Fleet-state endpoint (depth 1)
    ('mechanic', 8): 1, ('builder', 6): 1, ('designer', 9): 1,
    # Chain 3: Supersession validator (depth 1)
    ('archivist', 5): 1, ('scribe', 5): 1,
    # Chain 4: Memory-health (depth 1-2)
    ('archivist', 2): 1, ('scribe', 9): 2, ('scribe', 4): 2,
    # Chain 6: Model governance (depth 1)
    ('orchestrator', 2): 1, ('researcher', 3): 1,
    # Chain 7: Clobber defense (depth 1)
    ('builder', 6): 2, ('researcher', 6): 1, ('scribe', 6): 1,
    # Chain 8: Evidence quality (depth 1-2)
    ('verifier', 5): 1, ('verifier', 10): 1, ('orchestrator', 7): 2, ('researcher', 10): 2,
}

def read_safe(p):
    return p.read_text(encoding='utf-8', errors='replace')

def parse_goal_file(text):
    """Extract numbered goals from a markdown goal file."""
    goals = []
    for line in text.splitlines():
        m = re.match(r'^\s*(\d+)\.\s+(.+)', line)
        if m:
            num = int(m.group(1))
            text_ = m.group(2).strip()
            verified = '(verified:' in text_ or '[x]' in line.lower()
            goals.append({'num': num, 'text': text_, 'verified': verified})
    return goals

def classify_goal_type(text):
    """Classify goal into type based on keywords."""
    t = text.lower()
    if any(k in t for k in ['measure', 'baseline', 'benchmark', 'metric', 'probe', 'monitor', 'track']):
        return 'measurement'
    if any(k in t for k in ['verify', 'test', 'validate', 'audit', 'check', 'enforce', 'gate']):
        return 'verify'
    if any(k in t for k in ['build', 'create', 'implement', 'write', 'develop', 'add ', 'script', 'endpoint', 'api']):
        return 'build'
    if any(k in t for k in ['research', 'investigate', 'find', 'analyze', 'predict', 'mine']):
        return 'research'
    return 'ops'

def load_cycle_goals(dir_path, cycle_num, slip_label_fn):
    """Load per-agent goal files from a directory."""
    dataset = []
    if not dir_path.exists():
        return dataset
    for f in sorted(dir_path.glob("*.md")):
        name = f.stem
        if name not in VALID_AGENTS:
            continue
        for g in parse_goal_file(read_safe(f)):
            dataset.append({
                'agent': name, 'goal_num': g['num'],
                'type': classify_goal_type(g['text']),
                'dep_depth': DEP_DEPTH_MAP.get((name, g['num']), 0),
                'slipped': slip_label_fn(g), 'cycle': cycle_num
            })
    return dataset

def load_dataset(base_dir="."):
    """Load training data from cycle-1 and cycle-2 archives only."""
    base = pathlib.Path(base_dir)
    dataset = []
    
    # Cycle 1: all goals completed (80/80 verified per kickoff record) -> no slip
    c1_dir = base / "memory/goals/archive"
    if c1_dir.exists():
        for f in sorted(c1_dir.glob("*-2026-11-13.md")):
            name = f.stem.replace("-2026-11-13", "")
            if name not in VALID_AGENTS:
                continue
            for g in parse_goal_file(read_safe(f)):
                dataset.append({
                    'agent': name, 'goal_num': g['num'],
                    'type': classify_goal_type(g['text']),
                    'dep_depth': DEP_DEPTH_MAP.get((name, g['num']), 0),
                    'slipped': 0, 'cycle': 1
                })
    
    # Cycle 2: archived state at 11-17 (day 1 of cycle) - open = slipped
    c2_dir = base / "memory/goals/archive/cycle2-2026-11-17"
    if c2_dir.exists():
        for f in sorted(c2_dir.glob("*.md")):
            name = f.stem
            if name not in VALID_AGENTS:
                continue
            for g in parse_goal_file(read_safe(f)):
                dataset.append({
                    'agent': name, 'goal_num': g['num'],
                    'type': classify_goal_type(g['text']),
                    'dep_depth': DEP_DEPTH_MAP.get((name, g['num']), 0),
                    'slipped': 0 if g['verified'] else 1, 'cycle': 2
                })
    
    return dataset

def load_current_goals(base_dir="."):
    """Load current (cycle-3) open goals for prediction."""
    base = pathlib.Path(base_dir)
    goals_dir = base / "memory/goals"
    dataset = []
    if goals_dir.exists():
        for f in sorted(goals_dir.glob("*.md")):
            name = f.stem
            if name not in VALID_AGENTS:
                continue
            for g in parse_goal_file(read_safe(f)):
                dataset.append({
                    'agent': name, 'goal_num': g['num'],
                    'type': classify_goal_type(g['text']),
                    'dep_depth': DEP_DEPTH_MAP.get((name, g['num']), 0),
                    'slipped': 0 if g['verified'] else 1, 'cycle': 3
                })
    return dataset

def compute_stats(data):
    """Compute feature-level statistics for Naive Bayes."""
    total = len(data)
    slipped_count = sum(d['slipped'] for d in data)
    
    # P(type), P(agent), P(depth) marginal + conditional
    stats = {
        'total': total,
        'p_slip': slipped_count / total if total else 0.5,
        'type': {}, 'agent': {}, 'depth': {}
    }
    
    for feat_name in ['type', 'agent']:
        for d in data:
            key = d[feat_name]
            if key not in stats[feat_name]:
                stats[feat_name][key] = {'total': 0, 'slipped': 0}
            stats[feat_name][key]['total'] += 1
            stats[feat_name][key]['slipped'] += d['slipped']
    
    for d in data:
        depth = d['dep_depth']
        key = f"depth={depth}"
        if key not in stats['depth']:
            stats['depth'][key] = {'total': 0, 'slipped': 0}
        stats['depth'][key]['total'] += 1
        stats['depth'][key]['slipped'] += d['slipped']
    
    return stats

def predict_score(d, stats):
    """Compute P(slip) using Naive Bayes with Laplace smoothing."""
    # Log-likelihood approach for numerical stability
    total = stats['total']
    p_slip = stats['p_slip']
    
    # Prior: log P(slip) vs log P(no slip)
    log_ratio = 0.0
    
    # Likelihood ratio for each feature
    for feat_name in ['type', 'agent']:
        key = d[feat_name]
        feat_stats = stats[feat_name].get(key, {'total': 1, 'slipped': 0})
        # P(feature|slip) / P(feature|no_slip) with Laplace smoothing
        num_slip = (feat_stats['slipped'] + 1) / (total * p_slip + 2)
        num_noslip = (feat_stats['total'] - feat_stats['slipped'] + 1) / (total * (1 - p_slip) + 2)
        log_ratio += __import__('math').log(num_slip / num_noslip) if num_noslip > 0 else 1.0
    
    # Depth
    depth_key = f"depth={d['dep_depth']}"
    feat_stats = stats['depth'].get(depth_key, {'total': 1, 'slipped': 0})
    num_slip = (feat_stats['slipped'] + 1) / (total * p_slip + 2)
    num_noslip = (feat_stats['total'] - feat_stats['slipped'] + 1) / (total * (1 - p_slip) + 2)
    log_ratio += __import__('math').log(num_slip / num_noslip) if num_noslip > 0 else 1.0
    
    # Convert log-odds to probability
    import math
    p = 1.0 / (1.0 + __import__('math').exp(-log_ratio))
    return p

def find_threshold(data, stats):
    """Find optimal threshold by maximizing accuracy."""
    best_thresh, best_acc = 0.5, 0.0
    scores = [predict_score(d, stats) for d in data]
    for thresh_100 in range(10, 90):
        thresh = thresh_100 / 100.0
        correct = sum(1 for s, d in zip(scores, data) if (s >= thresh) == (d['slipped'] == 1))
        acc = correct / len(data)
        if acc > best_acc:
            best_acc = acc
            best_thresh = thresh
    return best_thresh, best_acc

def cross_validate(data, n_folds=5, seed=42):
    """K-fold cross-validation."""
    random.seed(seed)
    indices = list(range(len(data)))
    random.shuffle(indices)
    fold_size = len(indices) // n_folds
    accuracies = []
    
    for i in range(n_folds):
        test_start = i * fold_size
        test_end = test_start + fold_size if i < n_folds - 1 else len(indices)
        test_idx = set(indices[test_start:test_end])
        train_data = [d for j, d in enumerate(data) if j not in test_idx]
        test_data = [data[j] for j in test_idx]
        
        stats = compute_stats(train_data)
        thresh, _ = find_threshold(train_data, stats)
        
        correct = sum(1 for d in test_data if (predict_score(d, stats) >= thresh) == (d['slipped'] == 1))
        acc = correct / len(test_data) if test_data else 0
        accuracies.append(acc)
    
    return accuracies

def main():
    base_dir = "."
    data = load_dataset(base_dir)
    print(f"Loaded {len(data)} goals from cycle-1+2 archives")
    slipped = sum(d['slipped'] for d in data)
    print(f"  Slipped: {slipped}, No slip: {len(data) - slipped}")
    
    if not data:
        print("ERROR: No data loaded")
        return
    
    # Cross-validation
    accs = cross_validate(data, n_folds=5)
    mean_acc = sum(accs) / len(accs)
    print(f"\n=== 5-FOLD CROSS-VALIDATION ===")
    for i, a in enumerate(accs):
        print(f"  Fold {i+1}: {a*100:.1f}%")
    print(f"  Mean: {mean_acc*100:.1f}% (target >=70%)")
    
    # Final model on all data
    stats = compute_stats(data)
    thresh, _ = find_threshold(data, stats)
    
    # Prediction table by feature
    print(f"\n=== PREDICTION TABLE (threshold={thresh:.2f}) ===")
    
    print("\nSlip risk by goal type:")
    for t in sorted(set(d['type'] for d in data)):
        fake = {'type': t, 'agent': 'mechanic', 'dep_depth': 0}
        p = predict_score(fake, stats)
        label = "HIGH" if p >= thresh else ("MEDIUM" if p >= thresh * 0.7 else "LOW")
        print(f"  {t:12s} P(slip)={p:.3f} [{label}]")
    
    print("\nSlip risk by agent:")
    for a in sorted(set(d['agent'] for d in data)):
        fake = {'type': 'build', 'agent': a, 'dep_depth': 0}
        p = predict_score(fake, stats)
        label = "HIGH" if p >= thresh else ("MEDIUM" if p >= thresh * 0.7 else "LOW")
        print(f"  {a:12s} P(slip)={p:.3f} [{label}]")
    
    print("\nSlip risk by dependency depth:")
    for dep in sorted(set(d['dep_depth'] for d in data)):
        fake = {'type': 'build', 'agent': 'mechanic', 'dep_depth': dep}
        p = predict_score(fake, stats)
        label = "HIGH" if p >= thresh else ("MEDIUM" if p >= thresh * 0.7 else "LOW")
        print(f"  depth={dep}      P(slip)={p:.3f} [{label}]")
    
    # Predict current open goals
    current = load_current_goals(base_dir)
    open_goals = [d for d in current if d['slipped'] == 1]
    if open_goals:
        print(f"\n=== CURRENT OPEN GOALS (cycle 3) RANKED BY SLIP RISK ===")
        scored = [(predict_score(d, stats), d) for d in open_goals]
        scored.sort(key=lambda x: -x[0])
        for p, d in scored[:15]:
            label = "HIGH" if p >= thresh else "OK"
            print(f"  [{label:4s}] {d['agent']:12s} #{d['goal_num']:2d} ({d['type']:12s} depth={d['dep_depth']}) P={p:.3f}")
    
    # Save prediction table
    out = {
        'model': 'naive_bayes_weighted',
        'features': ['type', 'agent', 'dep_depth'],
        'cv_accuracy_mean': mean_acc,
        'cv_accuracy_folds': accs,
        'threshold': thresh,
        'training_data_points': len(data),
        'slip_rate_training': slipped / len(data),
        'p_by_type': {}, 'p_by_agent': {}, 'p_by_depth': {}
    }
    for t in sorted(set(d['type'] for d in data)):
        out['p_by_type'][t] = predict_score({'type': t, 'agent': 'mechanic', 'dep_depth': 0}, stats)
    for a in sorted(set(d['agent'] for d in data)):
        out['p_by_agent'][a] = predict_score({'type': 'build', 'agent': a, 'dep_depth': 0}, stats)
    for dep in sorted(set(d['dep_depth'] for d in data)):
        out['p_by_depth'][f"depth={dep}"] = predict_score({'type': 'build', 'agent': 'mechanic', 'dep_depth': dep}, stats)
    
    out_path = pathlib.Path("memory/goals/slip_prediction_table.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nSaved: {out_path}")

if __name__ == "__main__":
    main()
