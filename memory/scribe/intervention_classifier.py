"""intervention_classifier.py - Classify human interventions into patterns.

Patterns: misdiagnosis, preference_override, new_requirement, edge_case, tool_gap
Output: memory/scribe/intervention-patterns.jsonl (one entry per intervention)
        + summary with per-pattern counts and trend direction.

Usage: python memory/scribe/intervention_classifier.py
"""
import json, pathlib
from collections import Counter
from datetime import datetime, timezone

INTERVENTIONS_FILE = pathlib.Path("memory/ops/human-interventions.jsonl")
OUTPUT_FILE = pathlib.Path("memory/scribe/intervention-patterns.jsonl")
SUMMARY_FILE = pathlib.Path("memory/scribe/intervention-pattern-summary.json")

# Classification heuristics based on intervention type + context keywords
def classify(intervention: dict) -> str:
    """Classify a single intervention into a pattern."""
    ctx = intervention.get("context", "").lower()
    itype = intervention.get("type", "")
    
    # Preference override: user specifying aesthetic/design preferences
    if any(kw in ctx for kw in ["looks right", "sizing", "placement", "button", "ui fix", "preference"]):
        return "preference_override"
    
    # New requirement: user adding something not previously in scope
    if any(kw in ctx for kw in ["work together", "new feature", "add", "build", "convergence ui"]):
        return "new_requirement"
    
    # Edge case: unexpected situation requiring judgment
    if any(kw in ctx for kw in ["relocated", "treat as normal", "model loaded on", "continue fleet ops"]):
        return "edge_case"
    
    # Tool gap: user fixing something the tools should handle
    if any(kw in ctx for kw in ["fix the", "still not", "clobber", "mirror revert"]):
        return "tool_gap"
    
    # Misdiagnosis: user correcting a wrong assumption
    misdiag_keywords = ["wrong", "incorrect", "actually", "no, that"]
    if any(kw in ctx for kw in misdiag_keywords):
        return "misdiagnosis"
    
    # Default by type
    if itype == "approve":
        return "new_requirement"  # approval = ratifying new direction
    elif itype == "redirect":
        return "new_requirement"
    elif itype == "unblock":
        return "edge_case"
    
    return "edge_case"

def main():
    if not INTERVENTIONS_FILE.exists():
        print(f"ERROR: {INTERVENTIONS_FILE} not found")
        return
    
    interventions = []
    for line in INTERVENTIONS_FILE.read_text(encoding="utf-8").strip().splitlines():
        if line.strip():
            interventions.append(json.loads(line))
    
    # Classify each
    classified = []
    for iv in interventions:
        pattern = classify(iv)
        entry = {
            "ts": iv.get("ts", ""),
            "cycle": iv.get("cycle"),
            "agent": iv.get("agent", ""),
            "type": iv.get("type", ""),
            "context": iv.get("context", "")[:100],
            "pattern": pattern,
        }
        classified.append(entry)
    
    # Write per-intervention classifications
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for e in classified:
            f.write(json.dumps(e) + "\n")
    
    # Compute summary
    counts = Counter(e["pattern"] for e in classified)
    total = len(classified)
    
    # Trend: compare first half vs second half
    mid = total // 2
    first_half = Counter(e["pattern"] for e in classified[:mid])
    second_half = Counter(e["pattern"] for e in classified[mid:])
    
    trends = {}
    all_patterns = set(list(first_half.keys()) + list(second_half.keys()))
    for p in all_patterns:
        f_count = first_half.get(p, 0) / max(mid, 1)
        s_count = second_half.get(p, 0) / max(total - mid, 1)
        if f_count == 0 and s_count == 0:
            direction = "stable"
        elif s_count > f_count:
            direction = "increasing"
        elif s_count < f_count:
            direction = "decreasing"
        else:
            direction = "stable"
        trends[p] = {"first_half_rate": round(f_count, 3), "second_half_rate": round(s_count, 3), "direction": direction}
    
    summary = {
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "total_interventions": total,
        "pattern_counts": dict(counts),
        "trends": trends,
        "classification_rules": "keyword-based heuristics on context + type; see classify() in script",
    }
    
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
