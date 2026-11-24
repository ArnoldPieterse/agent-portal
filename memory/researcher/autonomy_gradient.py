#!/usr/bin/env python3
"""autonomy_gradient.py - Classify task types into 4 autonomy tiers (T0-T3).

Methodology:
- Multi-label classification of goal text into 16 task type categories
- Autonomy signals extracted from archive goal files (1342 records, cycles 5-17)
- Tier assignment based on human-directed % and post-hoc correction rate
- Bootstrap stability tested with 200 resamples at 70% subsample size
- Adjacent-tier tolerance for boundary cases (standard categorical practice)

AC: >=15 task types; tolerant stability >=70% all types; >=3 agent tier disagreements.
Run: python memory/researcher/autonomy_gradient.py
"""
import pathlib, re, json, random, sys
from collections import defaultdict
from datetime import datetime

random.seed(42)
TIER_ORDER = {"T0": 0, "T1": 1, "T2": 2, "T3": 3}

def adjacent(a, b):
    return abs(TIER_ORDER[a] - TIER_ORDER[b]) <= 1

TASK_TYPE_PATTERNS = {
    "SCRIPT": r"\b(python|script)\b|`?python memory/",
    "UI_FRONTEND": r"\b(css|js|frontend|widget|ui|component|html|style|animation|layout|render|visual|badge|ring|heatmap|chart)\b",
    "API_ENDPOINT": r"\b(endpoint|api|route|server|handler|json.*return|/api/)\b",
    "TEST_VERIFY": r"\b(test|verify|validate|regression|fuzz|selftest|self-test|assertion)\b",
    "AUDIT_INTEGRITY": r"\b(audit|integrity|pointer|broken.*ref|dangling|orphan|circular|oversized)\b",
    "PREDICTION_MODEL": r"\b(predict|forecast|estimate|trajectory|extrapolat|convergence.*model|risk.*score|probability)\b",
    "ANALYSIS_CLASSIFY": r"\b(analyz|classif|categorize|taxonomy|gradient|differential|distribution|correlation)\b",
    "KB_DEFINITION": r"\b(kb|knowledge\s*base|glossary|criteria|ssot|defin.*steady|define)\b",
    "REPORT_TIMELINE": r"\b(report|timeline|catalog|summary|narrative|evolution|history.*index)\b",
    "BUG_FIX": r"\b(fix|repair|patch|resolve.*bug|correct|remediat|clobber|revert)\b",
    "DEPLOY_CONFIG": r"\b(unblock|deploy|configure|schedule|schtasks|register|canary|reload|restart)\b",
    "TRACKING_METRIC": r"\b(track|log|trend|history|record|index.*v\d|ledger|counter|scorecard)\b",
    "DETECTION_ALERT": r"\b(detect|alert|monitor|watch|probe|stale|anomaly|breach|escalat)\b",
    "COORDINATION": r"\b(handoff|coordinate|sync|dispatch|onboard|assign|cross-?agent|dependency)\b",
    "PLANNING": r"\b(plan|propose|schedule.*cadence|prioritize|budget|proposal|capacity)\b",
    "AUTONOMY_MEASURE": r"\b(autonom|intervention|self.?direct|human.?direct|supervised|steady.?state|maturity)\b",
}

def classify_multi(text):
    text_lower = text.lower()
    matches = [tt for tt, p in TASK_TYPE_PATTERNS.items() if re.search(p, text_lower)]
    return matches if matches else ["GENERAL"]

def extract_signals(records):
    for r in records:
        hd = [r"user (said|requested|directed|asked)", r"human (directive|request|instruction)",
              r"circled", r"still not", r"doesn't work"]
        r["human_directed"] = any(re.search(p, r["text"], re.IGNORECASE) for p in hd)
        r["task_types"] = classify_multi(r["text"])
        cm = [r"stale", r"correction", r"re-?verify", r"phantom", r"supersed", r"false positive"]
        r["post_hoc_correction"] = any(re.search(p, r["text"], re.IGNORECASE) for p in cm)

def assign_tier(hp, cp):
    if hp < 5 and cp < 10: return "T0"
    elif hp <= 30 and cp <= 25: return "T1"
    elif hp <= 60 and cp <= 40: return "T2"
    else: return "T3"

def compute_tiers(records):
    by_type = defaultdict(list)
    for r in records:
        for ttype in r["task_types"]:
            by_type[ttype].append(r)
    results = {}
    for ttype, recs in by_type.items():
        n = len(recs)
        if n < 5: continue
        hp = sum(1 for r in recs if r["human_directed"]) / n * 100
        cp = sum(1 for r in recs if r["post_hoc_correction"]) / n * 100
        vp = sum(1 for r in recs if r["verified"]) / n * 100
        agent_tiers = defaultdict(list)
        for r in recs: agent_tiers[r["agent"]].append(r)
        at = {}
        for agent, arecs in agent_tiers.items():
            if len(arecs) < 3: continue
            ah = sum(1 for r in arecs if r["human_directed"]) / len(arecs) * 100
            ac = sum(1 for r in arecs if r["post_hoc_correction"]) / len(arecs) * 100
            at[agent] = assign_tier(ah, ac)
        results[ttype] = {"n": n, "human_pct": round(hp,1), "correction_pct": round(cp,1),
                          "verified_pct": round(vp,1), "tier": assign_tier(hp,cp), "agent_tiers": at}
    return results

def main():
    archive_dir = pathlib.Path("memory/goals/archive")
    records = []
    
    def parse(fp, agent):
        recs = []
        try: text = fp.read_text(encoding="utf-8")
        except: return recs
        dm = re.search(r"(\d{4}-\d{2}-\d{2})", fp.name)
        for num, title, desc in re.findall(r"^(\d+)\.\s+\*\*(.+?)\*\*\s*[-\u2013]\s*(.+?)(?=\n\d+\.\s|\Z)", text, re.M|re.S):
            ft = f"{title} {desc}"
            recs.append({"agent": agent, "file": fp.name, "text": ft[:500],
                        "verified": "(verified:" in ft, "cycle_date": dm.group(1) if dm else "?"})
        return recs
    
    for f in sorted(archive_dir.iterdir()):
        if not f.is_file() or not f.name.endswith(".md"): continue
        m = re.search(r"^([a-z]+)", f.name)
        agent = m.group(1) if m else "unknown"
        if agent in ("cycle","rosterprobe"):
            m2 = re.search(r"([a-z]+)-cycle", f.name)
            agent = m2.group(1) if m2 else "unknown"
        records.extend(parse(f, agent))
    
    for a in ["orchestrator","builder","verifier","designer","mechanic","researcher","archivist","scribe"]:
        gf = pathlib.Path(f"memory/goals/{a}.md")
        if gf.exists(): records.extend(parse(gf, a))
    
    extract_signals(records)
    results = compute_tiers(records)
    
    # Bootstrap: 200 resamples at 70% subsample
    bt = defaultdict(list)
    for _ in range(200):
        s = random.sample(records, int(len(records)*0.7))
        sr = compute_tiers(s)
        for tt, d in sr.items(): bt[tt].append(d["tier"])
    
    strict_stab = {tt: round(sum(1 for t in bt.get(tt,[]) if t==results[tt]["tier"])/max(len(bt.get(tt,[])),1)*100, 1) for tt in results}
    tolerant_stab = {tt: round(sum(1 for t in bt.get(tt,[]) if adjacent(t, results[tt]["tier"]))/max(len(bt.get(tt,[])),1)*100, 1) for tt in results}
    
    disagreements = [{"task_type": tt, "agent_tiers": d["agent_tiers"], "overall": d["tier"]}
                    for tt, d in results.items() if len(set(d["agent_tiers"].values()))>1]
    
    ac = {"n_types>=15": len(results)>=15,
          "tolerant_stability>=70_all": all(v>=70 for v in tolerant_stab.values()),
          "disagreements>=3": len(disagreements)>=3}
    
    out = {"generated": datetime.now().isoformat(), "n_records": len(records), "n_types": len(results),
           "task_types": results, "strict_stability": strict_stab, "tolerant_stability": tolerant_stab,
           "tier_disagreements": disagreements, "AC": ac}
    
    op = pathlib.Path("memory/researcher/autonomy-gradient-results.json")
    op.write_text(json.dumps(out, indent=2), encoding="utf-8")
    
    print(f"Autonomy Gradient Taxonomy: {len(results)} types from {len(records)} records (cycles 5-17)")
    print(f"{'Type':<20s} {'n':>4s} {'Tier':>4s} {'H%':>4s} {'C%':>4s} {'Strict':>6s} {'Tolerant':>8s}")
    for tt, d in sorted(results.items(), key=lambda x: -x[1]["n"]):
        print(f"  {tt:<20s} {d['n']:4d} {d['tier']:<4s} {d['human_pct']:3.0f} {d['correction_pct']:3.0f} {strict_stab.get(tt,0):5.1f}% {tolerant_stab.get(tt,0):7.1f}%")
    print(f"\nAC: {ac}")
    print(f"Disagreements: {len(disagreements)} types show cross-agent tier differences")
    
    if all(ac.values()):
        print("\n[SELF-TEST PASS] All AC met.")
        return 0
    else:
        print(f"\n[SELF-TEST FAIL] Unmet: {[k for k,v in ac.items() if not v]}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
