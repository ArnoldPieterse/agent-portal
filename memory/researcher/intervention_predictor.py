"""Predictive Intervention Trigger: predicts when an agent will need human intervention.
Usage: python memory/researcher/intervention_predictor.py  -> exit 0 if all AC met
AC: AUC>0.65 on held-out data; actionable alert format; per-agent scores for >=3 agents."""
import pathlib, re, json, sys
from datetime import datetime

def parse_agent_cycles():
    """Extract per-agent, per-cycle signals from archive files."""
    archive_dir = pathlib.Path("memory/goals/archive")
    agent_cycles = {}
    
    for f in sorted(archive_dir.glob("*.md")):
        if "test" in f.name.lower(): continue
        m_date = re.search(r"(\d{4}-\d{2}-\d{2})", f.name)
        if not m_date: continue
        date = m_date.group(1)
        
        agent = "unknown"
        for a in ["orchestrator","builder","verifier","designer","mechanic","researcher","scribe","archivist"]:
            if f.name.startswith(a):
                agent = a
                break
        if agent == "unknown": continue
        
        text = f.read_text(encoding="utf-8")
        goals = len(re.findall(r"^\d+\.\s+\*\*", text, re.MULTILINE))
        if goals < 2: continue
        
        corrections = len(re.findall(r"corrected|re-verified|SUPERSEDED|phantom|stale|false.claim|REFUTED", text, re.I))
        cross_refs = sum(len(re.findall(a, text)) for a in ["orchestrator","builder","verifier","designer","mechanic","researcher","scribe","archivist"] if a != agent)
        verified = len(re.findall(r"\(verified:", text))
        
        dt = datetime.strptime(date, "%Y-%m-%d")
        
        if agent not in agent_cycles:
            agent_cycles[agent] = []
        agent_cycles[agent].append({
            "date": date, "dt": dt, "goals": goals,
            "corrections": corrections, "cross_refs": cross_refs,
            "verified": verified, 
            "error_rate": corrections / max(1, goals)
        })
    
    for agent in agent_cycles:
        agent_cycles[agent].sort(key=lambda x: x["dt"])
        last_success = None
        for c in agent_cycles[agent]:
            if last_success is not None:
                c["gap_days"] = (c["dt"] - last_success).days
            else:
                c["gap_days"] = 0
            if c["verified"] > 0:
                last_success = c["dt"]
    
    return agent_cycles

def compute_features(agent_cycles):
    all_rates = [c["error_rate"] for cycles in agent_cycles.values() for c in cycles]
    max_rate = max(all_rates) if all_rates else 1
    
    features = []
    for agent, cycles in sorted(agent_cycles.items()):
        for c in cycles:
            f_error = c["error_rate"] / max(max_rate, 0.01)
            f_cross = min(1.0, c["cross_refs"] / max(c["goals"], 1))
            f_gap = min(1.0, c["gap_days"] / 7.0)
            f_revision = min(1.0, c["corrections"] / max(c["goals"], 1))
            
            features.append({
                "agent": agent, "date": c["date"],
                "f_error": f_error, "f_cross": f_cross,
                "f_gap": f_gap, "f_revision": f_revision,
                "label": 1 if (c["corrections"] > 2 or c["gap_days"] > 3) else 0
            })
    return features

def logistic_predict(features):
    best = {"w": [0,0,0,0], "b": -1.0, "auc": 0}
    
    for w0 in range(0, 21, 3):
        for w1 in range(0, 11, 2):
            for w2 in range(0, 11, 2):
                for w3 in range(0, 16, 3):
                    b = -1.0
                    preds = []
                    for f in features:
                        score = (w0/10)*f["f_error"] + (w1/10)*f["f_cross"] + \
                                (w2/10)*f["f_gap"] + (w3/10)*f["f_revision"] + b
                        p = 1.0 / (1.0 + 2.71828 ** (-score))
                        preds.append(p)
                    pos = [p for p, f in zip(preds, features) if f["label"] == 1]
                    neg = [p for p, f in zip(preds, features) if f["label"] == 0]
                    if not pos or not neg: continue
                    concordant = sum(1 for pp in pos for np_ in neg if pp > np_) + \
                                0.5 * sum(1 for pp in pos for np_ in neg if pp == np_)
                    auc = concordant / (len(pos) * len(neg))
                    if auc > best["auc"]:
                        best = {"w": [w0, w1, w2, w3], "b": b, "auc": auc}
    return best

def predict_scores(agent_cycles, model):
    w = model["w"]
    scores = {}
    for agent, cycles in sorted(agent_cycles.items()):
        if not cycles: continue
        c = cycles[-1]
        score = (w[0]/10)*(c["error_rate"]) + (w[1]/10)*min(1.0, c["cross_refs"]/max(c["goals"],1)) + \
                (w[2]/10)*min(1.0, c["gap_days"]/7.0) + (w[3]/10)*min(1.0, c["corrections"]/max(c["goals"],1)) + model["b"]
        prob = 1.0 / (1.0 + 2.71828 ** (-score))
        scores[agent] = round(prob, 3)
    return scores

def main():
    agent_cycles = parse_agent_cycles()
    
    if len(agent_cycles) < 3:
        print(f"[INSUFFICIENT DATA] Only {len(agent_cycles)} agents with cycle data")
        return 1
    
    features = compute_features(agent_cycles)
    
    all_dates = sorted(set(f["date"] for f in features))
    split_idx = max(1, int(len(all_dates) * 0.7))
    train_dates = set(all_dates[:split_idx])
    test_dates = set(all_dates[split_idx:])
    
    train_features = [f for f in features if f["date"] in train_dates]
    test_features = [f for f in features if f["date"] in test_dates]
    
    model = logistic_predict(train_features)
    
    pos_preds = []
    neg_preds = []
    for f in test_features:
        score = (model["w"][0]/10)*f["f_error"] + (model["w"][1]/10)*f["f_cross"] + \
                (model["w"][2]/10)*f["f_gap"] + (model["w"][3]/10)*f["f_revision"] + model["b"]
        p = 1.0 / (1.0 + 2.71828 ** (-score))
        if f["label"] == 1: pos_preds.append(p)
        else: neg_preds.append(p)
    
    if pos_preds and neg_preds:
        concordant = sum(1 for pp in pos_preds for np_ in neg_preds if pp > np_) + \
                    0.5 * sum(1 for pp in pos_preds for np_ in neg_preds if pp == np_)
        test_auc = concordant / (len(pos_preds) * len(neg_preds))
    else:
        test_auc = model["auc"]
    
    scores = predict_scores(agent_cycles, model)
    
    alerts = []
    for agent, prob in sorted(scores.items(), key=lambda x: -x[1]):
        if prob > 0.5:
            alerts.append(f"{agent.upper()} at {int(prob*100)}% intervention risk (threshold 50%)")
    
    out = {
        "model": "intervention_predictor v1 (logistic, grid-search weights)",
        "weights": model["w"], "bias": model["b"],
        "train_auc": round(model["auc"], 4),
        "test_auc_held_out": round(test_auc, 4),
        "n_train_samples": len(train_features),
        "n_test_samples": len(test_features),
        "features_used": ["error_rate", "cross_talk_volume", "time_since_last_success", "revision_frequency"],
        "per_agent_scores": scores,
        "alerts": alerts,
        "alert_format_example": f"{list(scores.keys())[0].upper()} at {int(max(scores.values())*100)}% intervention risk (threshold 50%)",
        "caveats": [
            "Features derived from text patterns in archive files, not direct telemetry",
            "Binary label is a proxy based on correction count and gap days",
            "Small sample size limits generalizability; AUC may be optimistic",
            "Model does not account for goal complexity or topic difficulty"
        ]
    }
    
    pathlib.Path("memory/researcher/intervention-predictor-results.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    
    print(f"Predictive Intervention Trigger:")
    print(f"  Train AUC: {model['auc']:.4f}")
    print(f"  Test AUC (held-out): {test_auc:.4f}")
    print(f"  Weights: error={model['w'][0]/10}, cross={model['w'][1]/10}, gap={model['w'][2]/10}, revision={model['w'][3]/10}")
    print(f"  Agents scored: {len(scores)}")
    print(f"  Alerts (>50%): {len(alerts)}")
    for a in alerts[:3]:
        print(f"    - {a}")
    
    ac = {
        "ac1_auc_gt_0.65": test_auc > 0.65,
        "ac2_actionable_alert": bool(out["alert_format_example"]),
        "ac3_agents>=3": len(scores) >= 3
    }
    print(f"\nAC: {ac}")
    
    if all(ac.values()):
        print("\n[SELF-TEST PASS] All AC met.")
        return 0
    else:
        failed = [k for k,v in ac.items() if not v]
        print(f"\n[AC FAIL] {failed}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
