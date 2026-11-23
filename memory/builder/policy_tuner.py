#!/usr/bin/env python3
"""Adaptive Policy Tuner — Builder cycle-14 goal #2.

Reads loop-scores.jsonl (output of loop_scorer.py) and proposes threshold
adjustments based on patterns in low-scoring loops.

Logic:
  - Group low-score loops (<0.5) by agent and failing stage
  - If an agent has >=3 loops with timeliness<0.5, propose tightening their SLA
  - If a stage fails (ok=False) in >=2 loops, propose adding a pre-check for it
  - If overall avg score < 0.6, propose increasing loop frequency (shorter detection window)

Output: memory/builder/policy-proposals.json
Selftest: synthetic data produces correct proposals for each rule.
"""
import json, sys, os, datetime

SCORES_FILE = "memory/builder/loop-scores.jsonl"
OUTPUT_FILE = "memory/builder/policy-proposals.json"
LOW_THRESHOLD = 0.5
AVG_THRESHOLD = 0.6
MIN_SAMPLES = 3


def load_scores(path=SCORES_FILE):
    if not os.path.exists(path):
        return []
    entries = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


def analyze(scores):
    """Identify patterns and generate proposals."""
    proposals = []
    low_loops = [s for s in scores if s.get("score", 1) < LOW_THRESHOLD]

    # Rule 1: Agent with consistently poor timeliness -> tighten SLA
    agent_timeliness = {}
    for s in scores:
        agent = s.get("agent", "unknown")
        tl = s.get("timeliness", 1)
        agent_timeliness.setdefault(agent, []).append(tl)

    for agent, tls in sorted(agent_timeliness.items()):
        if len(tls) >= MIN_SAMPLES:
            avg_tl = sum(tls) / len(tls)
            if avg_tl < 0.5:
                proposals.append({
                    "type": "tighten_sla",
                    "agent": agent,
                    "current_sla_s": 300,
                    "proposed_sla_s": max(60, int(300 * avg_tl)),
                    "rationale": f"avg timeliness {avg_tl:.2f} over {len(tls)} loops",
                    "confidence": min(1.0, len(tls) / 5),
                })

    # Rule 2: Stage that frequently fails -> add pre-check
    stage_failures = {}
    for s in scores:
        for st in s.get("failed_stages", []):
            stage_failures[st] = stage_failures.get(st, 0) + 1

    for stage, count in sorted(stage_failures.items()):
        if count >= 2:
            proposals.append({
                "type": "add_precheck",
                "stage": stage,
                "failure_count": count,
                "rationale": f"stage '{stage}' failed in {count} loops",
                "suggested_check": f"pre-{stage}-validation",
                "confidence": min(1.0, count / 4),
            })

    # Rule 3: Overall avg < threshold -> increase detection frequency
    if scores:
        avg_score = sum(s.get("score", 0) for s in scores) / len(scores)
        if avg_score < AVG_THRESHOLD:
            proposals.append({
                "type": "increase_detection_frequency",
                "current_interval_s": 300,
                "proposed_interval_s": max(60, int(300 * avg_score)),
                "rationale": f"avg loop score {avg_score:.2f} < {AVG_THRESHOLD}",
                "confidence": min(1.0, len(scores) / 5),
            })

    return proposals


def emit(proposals):
    out = {
        "generated": datetime.datetime.now().isoformat(),
        "source": SCORES_FILE,
        "total_proposals": len(proposals),
        "proposals": proposals,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    return out


def selftest():
    print("=" * 60)
    print("policy_tuner.py - SELFTEST")
    print("=" * 60)
    passed = 0

    # AC1: Agent with 3+ low-timeliness loops -> tighten_sla proposal
    scores_tl = [
        {"agent": "slow_agent", "score": 0.4, "timeliness": 0.2, "failed_stages": []},
        {"agent": "slow_agent", "score": 0.3, "timeliness": 0.1, "failed_stages": []},
        {"agent": "slow_agent", "score": 0.45, "timeliness": 0.3, "failed_stages": []},
    ]
    props = analyze(scores_tl)
    sla_prop = [p for p in props if p["type"] == "tighten_sla" and p["agent"] == "slow_agent"]
    ac1 = len(sla_prop) == 1 and sla_prop[0]["proposed_sla_s"] < 300
    print(f"AC1: tighten_sla for slow agent -> {'PASS' if ac1 else 'FAIL'}")
    passed += ac1

    # AC2: Stage failing in 2+ loops -> add_precheck proposal
    scores_stage = [
        {"agent": "a", "score": 0.4, "timeliness": 0.9, "failed_stages": ["remediate"]},
        {"agent": "b", "score": 0.45, "timeliness": 0.9, "failed_stages": ["remediate"]},
    ]
    props = analyze(scores_stage)
    precheck = [p for p in props if p["type"] == "add_precheck" and p["stage"] == "remediate"]
    ac2 = len(precheck) == 1
    print(f"AC2: add_precheck for remediate -> {'PASS' if ac2 else 'FAIL'}")
    passed += ac2

    # AC3: Overall avg < 0.6 -> increase_detection_frequency
    scores_avg = [
        {"agent": "x", "score": 0.4, "timeliness": 0.8, "failed_stages": []},
        {"agent": "y", "score": 0.5, "timeliness": 0.7, "failed_stages": []},
    ]
    props = analyze(scores_avg)
    freq = [p for p in props if p["type"] == "increase_detection_frequency"]
    ac3 = len(freq) == 1 and freq[0]["proposed_interval_s"] < 300
    print(f"AC3: increase frequency when avg<0.6 -> {'PASS' if ac3 else 'FAIL'}")
    passed += ac3

    # AC4: High scores produce no proposals
    scores_good = [
        {"agent": "good", "score": 0.9, "timeliness": 0.95, "failed_stages": []},
        {"agent": "good", "score": 0.85, "timeliness": 0.9, "failed_stages": []},
    ]
    props = analyze(scores_good)
    ac4 = len(props) == 0
    print(f"AC4: no proposals for healthy data -> {'PASS' if ac4 else 'FAIL'}")
    passed += ac4

    # AC5: Output file is valid JSON with expected schema
    out = emit(analyze(scores_tl + scores_stage))
    with open(OUTPUT_FILE, encoding="utf-8") as fh:
        loaded = json.load(fh)
    ac5 = "proposals" in loaded and "generated" in loaded and loaded["total_proposals"] >= 1
    print(f"AC5: output valid JSON -> {'PASS' if ac5 else 'FAIL'}")
    passed += ac5

    print(f"\nRESULT: {passed}/5 ACs PASSED")
    return 0 if passed == 5 else 1


def main():
    if "--selftest" in sys.argv:
        return selftest()
    scores = load_scores()
    if not scores:
        print(f"No scores found at {SCORES_FILE}. Run loop_scorer.py first.")
        return 1
    proposals = analyze(scores)
    out = emit(proposals)
    print(f"Analyzed {len(scores)} loops -> {len(proposals)} proposals")
    for p in proposals:
        print(f"  [{p['type']}] {p.get('agent', p.get('stage', 'fleet-wide'))}: {p['rationale']}")
    print(f"Output: {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
