#!/usr/bin/env python3
"""Goal Acceptance Rate Predictor - v2
Predicts whether a goal will be accepted as-is or need revision based on text features.
Uses Gaussian Naive Bayes over handcrafted features.
Label: first_attempt (0 progress notes) vs iterated (1+ progress notes).
"""
import re, json, math, random
from pathlib import Path
from collections import Counter

archive = Path("memory/goals/archive")

def get_cycle(fname):
    m = re.search(r"cycle(\d+)", fname)
    return int(m.group(1)) if m else None

def parse_goals(content):
    """Parse goals from markdown - handles both **bold** and plain formats."""
    goals = []
    for g in re.finditer(r"(?m)^(\d+)\.\s+(.+?)(?=^\d+\.\s+|^$)", content, re.DOTALL):
        text = g.group(2).strip()
        # Extract title: before first ' - ' or first 50 chars
        if ' - ' in text:
            title = text.split(' - ')[0].replace('**', '').strip()
        else:
            title = text[:50].replace('**', '').strip()
        progress_count = len(re.findall(r"\[PROGRESS", text))
        goals.append({"title": title, "full_text": text, "progress": progress_count})
    return goals

# Build dataset: use ALL files with PROGRESS markers as labeled data
# Label: 0=accepted (0 progress notes), 1=iterated/revised (1+ progress notes)
samples = []
files = sorted(archive.glob("*.md"))
for f in files:
    if f.name in ("INDEX.md", "README.md"): continue
    try: content = f.read_text(encoding="utf-8")
    except Exception: continue
    cycle = get_cycle(f.name)
    agent_m = re.match(r"([a-z]+)", f.name)
    agent = agent_m.group(1) if agent_m else "unknown"
    for g in parse_goals(content):
        label = 0 if g["progress"] == 0 else 1
        # Strip PROGRESS notes to get original goal text only (avoid circular signal)
        orig_text = re.split(r"\[PROGRESS", g["full_text"])[0].strip()
        samples.append({"agent": agent, "cycle": cycle or 0, "title": g["title"],
                       "text": orig_text, "label": label, "progress": g["progress"],
                       "file": f.name})

print(f"Total samples: {len(samples)}")
print(f"Labels: first_attempt={sum(1 for s in samples if s['label']==0)}, iterated={sum(1 for s in samples if s['label']==1)}")

# Feature extraction
def extract_features(text, title):
    words = re.findall(r"[a-zA-Z]+", text.lower())
    title_words = len(title.split())
    return {
        "char_len": len(text),
        "word_count": len(words),
        "title_words": title_words,
        "backticks": text.count("`"),
        "file_refs": len(re.findall(r"memory/[a-z_/]+\.\w+", text)),
        "numbers": len(re.findall(r"\d+", text)),
        "percent": len(re.findall(r"\d+\s*%", text)),
        "has_cmd": 1 if re.search(r"`python |`elev|`schtasks", text) else 0,
        "has_output": 1 if re.search(r"Output:|output:|\.json|\.md|\.py", text) else 0,
        "verified_kw": 1 if re.search(r"Verified:|AC:|Acceptance", text) else 0,
        "specificity": len(re.findall(r"[a-z_]+\.\w+|\d+[A-Za-z]*%|>\s*\d+|>=\s*\d+", text)),
        "breadth": len(re.findall(r"all |every |each |any |multiple|various", text.lower())),
        "vague": len(re.findall(r"some |a few|several|etc|approximately|roughly", text.lower())),
    }

# Build feature matrix + vocabulary for NB
FEATURES = ["char_len","word_count","title_words","backticks","file_refs","numbers",
            "percent","has_cmd","has_output","verified_kw","specificity","breadth","vague"]

X_all = []
y_all = []
vocab_counter = Counter()  # for NB word-level features
for s in samples:
    feats = extract_features(s["text"], s["title"])
    X_all.append(feats)
    y_all.append(s["label"])
    # Collect words for NB
    for w in re.findall(r"[a-z]{4,}", s["text"].lower()):
        vocab_counter[(w, s["label"])] += 1

# Naive Bayes with both numeric (Gaussian) and word-level features
def nb_predict(feats, text):
    """Log-likelihood ratio: P(class=1|features) vs P(class=0|features)"""
    log_ratios = [0.0] * len(FEATURES)
    for i, fn in enumerate(FEATURES):
        v = feats[fn]
        # Gaussian NB per feature
        c0 = [X_all[j][fn] for j in range(len(X_all)) if y_all[j]==0]
        c1 = [X_all[j][fn] for j in range(len(X_all)) if y_all[j]==1]
        m0, m1 = sum(c0)/len(c0), sum(c1)/len(c1)
        s0 = (sum((x-m0)**2 for x in c0)/len(c0) + 1e-6)**0.5
        s1 = (sum((x-m1)**2 for x in c1)/len(c1) + 1e-6)**0.5
        # log P(x|c1) - log P(x|c0)
        lr1 = -math.log(s1) - (v-m1)**2/(2*s1*s1)
        lr0 = -math.log(s0) - (v-m0)**2/(2*s0*s0)
        log_ratios[i] = lr1 - lr0
    # Prior
    p1 = sum(y_all)/len(y_all)
    log_prior = math.log(p1/(1-p1))
    total = log_prior + sum(log_ratios)
    return 1 if total > 0 else 0

# But computing per-sample is slow; let me precompute class stats
c0_vals = {fn: [X_all[j][fn] for j in range(len(X_all)) if y_all[j]==0] for fn in FEATURES}
c1_vals = {fn: [X_all[j][fn] for j in range(len(X_all)) if y_all[j]==1] for fn in FEATURES}
stats = {}
for fn in FEATURES:
    m0, m1 = sum(c0_vals[fn])/len(c0_vals[fn]), sum(c1_vals[fn])/len(c1_vals[fn])
    v0 = sum((x-m0)**2 for x in c0_vals[fn])/len(c0_vals[fn]) + 1e-6
    v1 = sum((x-m1)**2 for x in c1_vals[fn])/len(c1_vals[fn]) + 1e-6
    stats[fn] = (m0, m1, v0**0.5, v1**0.5)

p1 = sum(y_all)/len(y_all)
log_prior = math.log(p1/(1-p1))

def predict(feats):
    total = log_prior
    for fn in FEATURES:
        m0, m1, s0, s1 = stats[fn]
        v = feats[fn]
        lr1 = -math.log(s1) - (v-m1)**2/(2*s1*s1)
        lr0 = -math.log(s0) - (v-m0)**2/(2*s0*s0)
        total += lr1 - lr0
    return 1 if total > 0 else 0

# Evaluate with stratified random split
import random
random.seed(42)
indices = list(range(len(X_all)))
random.shuffle(indices)
split = int(len(indices)*0.7)
train_idx, test_idx = indices[:split], indices[split:]

train_correct = sum(1 for i in train_idx if predict(X_all[i]) == y_all[i])
test_correct = sum(1 for i in test_idx if predict(X_all[i]) == y_all[i])
print(f"\nGaussian NB:")
print(f"  Train: {train_correct}/{len(train_idx)} = {100*train_correct/len(train_idx):.1f}%")
print(f"  Test:  {test_correct}/{len(test_idx)} = {100*test_correct/len(test_idx):.1f}%")

# Also try: just use progress-based proxy features that are predictive of revision
# Key insight: goals with MORE specific verification criteria tend to be accepted (less iteration needed)
# Goals with broad scope / vague language tend to need more iteration
print("\nPer-feature separation (mean diff):")
for fn in FEATURES:
    m0 = sum(c0_vals[fn])/len(c0_vals[fn])
    m1 = sum(c1_vals[fn])/len(c1_vals[fn])
    print(f"  {fn:15s}: acc={m0:.3f} iter={m1:.3f} delta={m1-m0:.3f}")

# Save the model + dataset
model_data = {
    "features": FEATURES,
    "class_stats": {fn: list(stats[fn]) for fn in FEATURES},
    "log_prior": log_prior,
    "n_samples": len(samples),
    "label_distribution": {"first_attempt": sum(1 for y in y_all if y==0), "iterated": sum(1 for y in y_all if y==1)},
    "train_acc": 100*train_correct/len(train_idx),
    "test_acc": 100*test_correct/len(test_idx),
}
Path("memory/researcher/goal-acceptance-model.json").write_text(json.dumps(model_data, indent=2))
print("\nModel saved to memory/researcher/goal-acceptance-model.json")
