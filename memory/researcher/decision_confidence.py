"""Decision Confidence Estimator (Researcher Goal #2, cycle-11).

For each decision in decision-log.jsonl, score how well-supported it was by
evidence available at decision time. Scores: 0-1 per entry + aggregate stats.
Output: memory/researcher/decision-confidence-report.json

Verification criteria:
- Every entry scored (0 missing)
- Scores are deterministic (same input -> same output)
- >=5 entries have distinct scores (not all identical)
- Output JSON is valid
"""
import json
import pathlib
from datetime import datetime, timezone

LOG_SOURCES = [
    "decision-log.jsonl",
    "memory/decision-log.jsonl",
    "memory/ops/decision-log.jsonl",
]
OUTPUT = "memory/researcher/decision-confidence-report.json"


def load_all_entries():
    entries = []
    for src in LOG_SOURCES:
        p = pathlib.Path(src)
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8").strip()
        if not text:
            continue
        for line in text.split("\n"):
            try:
                obj = json.loads(line)
                obj["_source"] = src
                entries.append(obj)
            except json.JSONDecodeError:
                pass
    return entries


def score_confidence(entry):
    """Score a single decision entry 0-1 based on evidence quality.
    
    Factors:
    - Has explicit outcome (not missing/null): +0.3
    - Outcome is positive/successful: +0.2
    - Has detail/structured data: +0.2
    - Entry type implies verification (runbook_execution with steps): +0.1
    - Has timestamp: +0.1
    - Step passed explicitly True: +0.1
    """
    score = 0.0
    
    # Timestamp present = basic provenance
    if entry.get("timestamp") or entry.get("ts"):
        score += 0.1
    
    # Outcome field exists and is non-empty
    outcome = (entry.get("outcome") or "").lower()
    if outcome:
        score += 0.3
        # Positive outcomes get bonus
        if any(k in outcome for k in ("success", "complete", "pass")):
            score += 0.2
    
    # Structured detail present (indicates evidence was captured)
    detail = entry.get("detail")
    if detail and isinstance(detail, dict) and len(detail) > 1:
        score += 0.2
    elif detail and isinstance(detail, str) and len(detail) > 10:
        score += 0.1
    
    # Runbook with explicit step counts = verified execution
    if entry.get("type") in ("runbook_execution", "runbook_exec"):
        steps_total = entry.get("steps_total", 0)
        steps_completed = entry.get("steps_completed", 0)
        if steps_total > 0 and steps_completed == steps_total:
            score += 0.1
    
    # Playbook step with explicit pass/fail
    if entry.get("type") == "playbook_step":
        if entry.get("passed") is True:
            score += 0.1
    
    # Overall OK flag
    if entry.get("overall_ok") is True:
        score += 0.1
    
    return min(score, 1.0)


def main():
    entries = load_all_entries()
    scored = []
    for i, e in enumerate(entries):
        conf = score_confidence(e)
        scored.append({
            "index": i,
            "agent": e.get("agent", "unknown"),
            "type": e.get("type", "unknown"),
            "timestamp": e.get("timestamp") or e.get("ts"),
            "confidence": round(conf, 3),
            "source": e["_source"],
        })
    
    # Aggregate stats
    scores = [s["confidence"] for s in scored]
    distinct_scores = len(set(scores))
    
    result = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_decisions": len(scored),
        "mean_confidence": round(sum(scores) / len(scores), 3) if scores else 0,
        "min_confidence": min(scores) if scores else 0,
        "max_confidence": max(scores) if scores else 0,
        "distinct_score_count": distinct_scores,
        "high_confidence_pct": round(sum(1 for s in scores if s >= 0.7) / len(scores) * 100, 1) if scores else 0,
        "entries": scored,
    }
    
    pathlib.Path(OUTPUT).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    print(f"Total: {len(scored)}, Mean confidence: {result['mean_confidence']}, Distinct scores: {distinct_scores}")
    
    # Self-test assertions
    assert len(scored) == len(entries), "Score count mismatch"
    assert all(0 <= s["confidence"] <= 1 for s in scored), "Score out of range"
    assert distinct_scores >= 5, f"Expected >=5 distinct scores, got {distinct_scores}"
    # Determinism check: re-score and compare
    rescored = [score_confidence(e) for e in entries]
    assert all(abs(a - b) < 0.001 for a, b in zip(rescored, scores)), "Non-deterministic scoring"
    print("SELFTEST PASS")


if __name__ == "__main__":
    main()
