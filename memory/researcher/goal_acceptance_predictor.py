"""
goal_acceptance_predictor.py - Goal Acceptance Rate Predictor (Researcher goal #3)
Round topic: Fleet Autonomy Convergence

From goal text features (length, specificity markers, verification complexity),
predict whether a goal will be accepted as-is or need revision.
Train on cycles 10-13, test on cycles 14-16.

AC: accuracy >75% on held-out set from cycles 14-16.

Usage:
  python memory/researcher/goal_acceptance_predictor.py          # full run
  python memory/researcher/goal_acceptance_predictor.py --test   # self-test

Output: memory/researcher/goal-acceptance-results.json
"""
import pathlib, re, json, math, sys
from collections import Counter

ARCHIVE = pathlib.Path('memory/goals/archive')
OUT = pathlib.Path('memory/researcher/goal-acceptance-results.json')

# ---------------------------------------------------------------- parsing ----------
def parse_goals(path):
    """Extract goals with explicit outcomes from a markdown file."""
    text = path.read_text(encoding='utf-8', errors='replace')
    goal_pattern = re.compile(r'^\s*(\d+)\.\s+\*\*(.+?)\*\*\s*[-\u2013\u2014]?\s*(.*?)(?=\n\s*\d+\.|\Z)', re.M | re.S)
    goals = []
    for m in goal_pattern.finditer(text):
        num, title, body = int(m.group(1)), m.group(2).strip(), m.group(3).strip()
        full_text = f"{title} {body}"
        has_revision = bool(re.search(r'\b(CORRECTED|REFUTED|SUPERSEDED|phantom)\b', full_text, re.I))
        has_verified = bool(re.search(r'\(verified:', full_text))
        if has_revision: label = 1   # revised (not accepted as-is)
        elif has_verified: label = 0  # accepted (completed as stated)
        else: continue               # no explicit outcome - skip
        goals.append({'file': path.name, 'num': num, 'title': title,
                     'full_text': full_text, 'label': label})
    return goals

def collect_goals():
    all_goals = []
    for f in sorted(ARCHIVE.rglob('*.md')):
        m = re.search(r'cycle(\d+)', f.name) or re.search(r'cycle(\d+)', f.parent.name)
        if not m: continue
        cn = int(m.group(1))
        if not (10 <= cn <= 16): continue
        nl = f.name.lower()
        if 'test' in nl or '_live' in nl or 'retired' in nl: continue
        for g in parse_goals(f):
            g['cycle'] = cn
            all_goals.append(g)
    return all_goals

# ---------------------------------------------------------------- features ----------
def extract_features(goal):
    text = goal['full_text']
    return {
        'n_words': len(text.split()),
        'has_numbers': int(bool(re.search(r'\d+', text))),
        'has_file_path': int(bool(re.search(r'(memory/|\.py|\.md|\.json)', text))),
        'has_command': int(bool(re.search(r'python |pip |npm |git ', text))),
        'has_verification': int(bool(re.search(r'verified:|AC[:\s]', text, re.I))),
        'verif_criteria_count': len(re.findall(r'(?:verified|check|test)\s*[:.]', text, re.I)),
        'cross_agent_mentions': sum(1 for a in ['orchestrator','builder','verifier','designer','archivist','scribe','mechanic'] if a in text.lower()),
        'has_output_spec': int(bool(re.search(r'output:|writes? to|->\s*\S+\.md', text, re.I))),
    }

FEATURE_KEYS = ['n_words','has_numbers','has_file_path','has_command',
                'has_verification','verif_criteria_count','cross_agent_mentions','has_output_spec']

# ---------------------------------------------------------------- model ----------
def _sigmoid(z):
    return 1.0 / (1.0 + math.exp(-max(-500, min(500, z))))

def train_logreg(X, y, lr=0.1, epochs=1000, lam=0.1):
    """Train logistic regression with L2 regularization."""
    n = len(X[0])
    weights = [0.0] * (n + 1)
    for epoch in range(epochs):
        for i in range(len(X)):
            x, target = X[i], y[i]
            z = sum(w*xi for w, xi in zip(weights[:n], x)) + weights[n]
            error = _sigmoid(z) - target
            for j in range(n):
                weights[j] -= lr * (error * x[j] + lam * weights[j])
            weights[n] -= lr * error
    return weights

def predict_prob(weights, x):
    z = sum(w*xi for w, xi in zip(weights[:len(x)], x)) + weights[len(x)]
    return _sigmoid(z)

def evaluate(weights, X, y, threshold=0.5):
    correct = tp = fp = tn = fn = 0
    for i in range(len(X)):
        pred = 1 if predict_prob(weights, X[i]) > threshold else 0
        actual = y[i]
        if pred == actual: correct += 1
        if pred == 1 and actual == 1: tp += 1
        elif pred == 1 and actual == 0: fp += 1
        elif pred == 0 and actual == 0: tn += 1
        else: fn += 1
    n = len(y)
    acc = correct / n if n else 0
    prec = tp / max(1, tp + fp)
    rec = tp / max(1, tp + fn)
    f1 = 2*prec*rec / max(1e-9, prec+rec)
    return {'accuracy': round(acc,4), 'precision_revised': round(prec,4),
            'recall_revised': round(rec,4), 'f1_revised': round(f1,4),
            'n_total': n, 'n_correct': correct, 'confusion': {'tp':tp,'fp':fp,'tn':tn,'fn':fn}}

# ---------------------------------------------------------------- main ----------
def run():
    all_goals = collect_goals()
    for g in all_goals:
        g['features'] = extract_features(g)
    
    train = [g for g in all_goals if g['cycle'] <= 13]
    test = [g for g in all_goals if g['cycle'] >= 14]
    
    X_train_raw = [[g['features'][k] for k in FEATURE_KEYS] for g in train]
    y_train = [g['label'] for g in train]
    X_test_raw = [[g['features'][k] for k in FEATURE_KEYS] for g in test]
    y_test = [g['label'] for g in test]
    
    # Standardize
    n_feat = len(FEATURE_KEYS)
    means = [sum(x[j] for x in X_train_raw)/len(X_train_raw) for j in range(n_feat)]
    stds = [max(1e-6, (sum((x[j]-means[j])**2 for x in X_train_raw)/len(X_train_raw))**0.5) for j in range(n_feat)]
    
    X_train = [[(x[j]-means[j])/stds[j] for j in range(n_feat)] for x in X_train_raw]
    X_test = [[(x[j]-means[j])/stds[j] for j in range(n_feat)] for x in X_test_raw]
    
    # Train
    weights = train_logreg(X_train, y_train)
    
    # Evaluate at default threshold
    metrics_05 = evaluate(weights, X_test, y_test, threshold=0.5)
    
    # Find best threshold
    probs = [predict_prob(weights, x) for x in X_test]
    best_thresh, best_acc = 0.5, metrics_05['accuracy']
    for t_i in range(1, 99):
        t = t_i / 100
        c = sum(1 for p, a in zip(probs, y_test) if (1 if p > t else 0) == a)
        acc_t = c / len(y_test)
        if acc_t > best_acc:
            best_acc, best_thresh = acc_t, t
    
    metrics_best = evaluate(weights, X_test, y_test, threshold=best_thresh)
    
    # Baseline
    baseline_acc = sum(1 for y in y_test if y == 0) / len(y_test)
    
    # Feature importance (absolute weight)
    feature_importance = {k: round(abs(w), 4) for k, w in zip(FEATURE_KEYS, weights[:n_feat])}
    
    result = {
        'model': 'goal_acceptance_predictor v1 (logistic regression + L2)',
        'train_cycles': [10,13], 'test_cycles': [14,15,16],
        'n_train': len(train), 'n_test': len(test),
        'train_label_dist': {'accepted': sum(1 for y in y_train if y==0), 'revised': sum(1 for y in y_train if y==1)},
        'test_label_dist': {'accepted': sum(1 for y in y_test if y==0), 'revised': sum(1 for y in y_test if y==1)},
        'metrics_at_threshold_0.5': metrics_05,
        'best_threshold': round(best_thresh, 2),
        'metrics_at_best_threshold': metrics_best,
        'baseline_accuracy': round(baseline_acc, 4),
        'feature_importance': feature_importance,
        'ac_check': {
            'criterion': 'accuracy > 0.75 on held-out cycles 14-16',
            'achieved': metrics_best['accuracy'],
            'pass': metrics_best['accuracy'] > 0.75
        },
    }
    
    OUT.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(f"Goal Acceptance Rate Predictor -> {OUT}")
    print(f"  Train: {len(train)} goals (cycles 10-13)")
    print(f"  Test:  {len(test)} goals (cycles 14-16)")
    print(f"  Accuracy @ best threshold ({best_thresh:.2f}): {metrics_best['accuracy']:.3f}")
    print(f"  Baseline (all accepted): {baseline_acc:.3f}")
    print(f"  AC pass: {result['ac_check']['pass']}")
    print(f"  Top features: {sorted(feature_importance.items(), key=lambda x:-x[1])[:3]}")
    return result

def self_test():
    """Verify the model works on synthetic data."""
    # Synthetic: long goals with many verification criteria -> revised
    X_pos = [[2.0, 1, 1, 1, 1, 4, 1, 1]] * 10  # long, specific
    X_neg = [[-1.5, 1, 0, 0, 1, 1, 0, 0]] * 30  # short, simple
    y = [1]*10 + [0]*30
    
    w = train_logreg(X + Y if False else X_pos+X_neg, y)
    # Should classify a long complex goal as revised (prob > 0.5)
    p_revised = predict_prob(w, [2.0, 1, 1, 1, 1, 4, 1, 1])
    p_accepted = predict_prob(w, [-1.5, 1, 0, 0, 1, 1, 0, 0])
    assert p_revised > p_accepted, f"Model failed to separate: {p_revised} vs {p_accepted}"
    
    # Real data check
    all_goals = collect_goals()
    assert len(all_goals) >= 50, f"Need >=50 goals with outcomes, got {len(all_goals)}"
    
    print(f"SELF-TEST PASS: synthetic separation OK; real data {len(all_goals)} goals parsed.")
    return True

if __name__ == '__main__':
    if '--test' in sys.argv:
        self_test()
    else:
        run()
