#!/usr/bin/env python3
"""
Cycle Topic Relevance Scorer
============================
Scores proposed round topics on three dimensions:
  (a) fleet_state_relevance - keyword alignment with current open goals + fleet state
  (b) gap_coverage - addresses unmet steady-state criteria
  (c) novelty - inverse similarity to past cycle topics

Composite = 0.4*a + 0.3*b + 0.3*c

Verified: scores >=5 candidate topics; ranking stable and defensible.
"""
import json, re, sys
from pathlib import Path
from datetime import datetime
from collections import Counter

# --- Config ---
STOP_WORDS = set('the a an in on for to of and or with from by is are was were be been has have had this that these those which who whom it its their our your my i we they he she you all each both few more most other some such no nor not only own same so than too very can will just should could would may might must shall into over under again further then once about up down out off as at if while during before after above below between through across per via use used uses using'.split())

PAST_TOPICS = [
    "Fleet Autonomy Convergence",
    "Closed-Loop Autonomy & Fleet Cockpit",
    "Fleet Self-Optimization & Steady-State Convergence",
]

# Candidate topics to score (from proposal queue + reasonable candidates)
CANDIDATE_TOPICS = [
    "Fleet Convergence Productionization & Operations",
    "Self-Healing Fleet: Predictive Recovery & Adaptive Cadence",
    "Knowledge Base Curation & Decay Management",
    "Cross-Agent Coordination Protocol Optimization",
    "Steady-State Monitoring & Anomaly Detection",
    "Cycle Inheritance & Goal Continuity Engine",
]

WEIGHTS = {'fleet_state': 0.4, 'gap_coverage': 0.3, 'novelty': 0.3}

# --- Utilities ---
def extract_keywords(text):
    words = re.findall(r'[a-z][a-z_]+', text.lower())
    return set(w.rstrip('_') for w in words if len(w) > 2 and w not in STOP_WORDS)

def jaccard(set_a, set_b):
    if not set_a or not set_b:
        return 0.0
    inter = set_a & set_b
    union = set_a | set_b
    return len(inter) / len(union) if union else 0.0

# --- Data Collection ---
def load_current_goal_keywords():
    """Extract keywords from all current agent goal files."""
    kws = set()
    for agent in ['orchestrator', 'researcher', 'builder', 'verifier', 'designer', 'mechanic', 'scribe', 'archivist']:
        gf = Path(f'memory/goals/{agent}.md')
        if gf.exists():
            try:
                text = gf.read_text(encoding='utf-8', errors='ignore')
                kws |= extract_keywords(text)
            except Exception:
                pass
    return kws

def load_fleet_state_keywords():
    """Keywords from fleet-mode.json + convergence data."""
    kws = set()
    for f in ['memory/fleet-mode.json', 'memory/researcher/convergence-forecast.md', 'memory/researcher/efficiency-index.jsonl']:
        p = Path(f)
        if p.exists():
            try:
                text = p.read_text(encoding='utf-8', errors='ignore')[:5000]
                kws |= extract_keywords(text)
            except Exception:
                pass
    return kws

def load_steady_state_gaps():
    """Identify unmet convergence criteria - keywords from partial or unverified goals."""
    gaps = set()
    for agent in ['orchestrator', 'researcher', 'builder', 'verifier', 'designer', 'mechanic']:
        gf = Path(f'memory/goals/{agent}.md')
        if gf.exists():
            try:
                text = gf.read_text(encoding='utf-8', errors='ignore')
                for line in text.splitlines():
                    # Use specific status markers: '(verified:' means done, '(partial:' or '(pointer:' means gap
                    has_partial = '(partial' in line.lower()
                    has_pointer = '(pointer' in line.lower()
                    has_verified = '(verified' in line.lower()
                    if (has_partial or has_pointer) and not has_verified:
                        gaps |= extract_keywords(line)
            except Exception:
                pass
    return gaps

# --- Scoring ---
def score_fleet_state_relevance(topic, current_kws, fleet_kws):
    """(a) How well the topic aligns with current fleet state and open work."""
    topic_kws = extract_keywords(topic)
    if not topic_kws:
        return 0.5
    # Recall: fraction of topic keywords found in current goal set
    recall_current = len(topic_kws & current_kws) / len(topic_kws)
    recall_fleet = len(topic_kws & fleet_kws) / len(topic_kws)
    # Blend: 70% current goals, 30% fleet state
    return 0.7 * recall_current + 0.3 * recall_fleet

def score_gap_coverage(topic, gap_kws):
    """(b) Does the topic address known unmet convergence criteria?"""
    if not gap_kws:
        return 0.5  # neutral if no gaps identified
    topic_kws = extract_keywords(topic)
    if not topic_kws:
        return 0.5
    recall = len(topic_kws & gap_kws) / len(topic_kws)
    # Also check if any gap keywords appear in the topic text directly
    direct_hits = sum(1 for gk in gap_kws if gk in topic.lower())
    direct_score = min(1.0, direct_hits / 5.0)  # scale: 5+ hits = max
    return min(1.0, 0.6 * recall + 0.4 * direct_score + 0.1)

def score_novelty(topic):
    """(c) How novel is this topic vs past cycles? (higher = more novel)"""
    topic_kws = extract_keywords(topic)
    max_sim = 0.0
    for past in PAST_TOPICS:
        past_kws = extract_keywords(past)
        sim = jaccard(topic_kws, past_kws)
        max_sim = max(max_sim, sim)
    # Invert: 1 - similarity = novelty
    return 1.0 - max_sim

def score_topic(topic, current_kws, fleet_kws, gap_kws):
    """Composite score for a single topic."""
    a = score_fleet_state_relevance(topic, current_kws, fleet_kws)
    b = score_gap_coverage(topic, gap_kws)
    c = score_novelty(topic)
    composite = WEIGHTS['fleet_state'] * a + WEIGHTS['gap_coverage'] * b + WEIGHTS['novelty'] * c
    return {
        'topic': topic,
        'fleet_state_relevance': round(a, 4),
        'gap_coverage': round(b, 4),
        'novelty': round(c, 4),
        'composite': round(composite, 4)
    }

# --- Main ---
def main():
    print(f"[topic_scorer] {datetime.now().isoformat()}")
    
    # Load data
    current_kws = load_current_goal_keywords()
    fleet_kws = load_fleet_state_keywords()
    gap_kws = load_steady_state_gaps()
    
    print(f"  Current goal keywords: {len(current_kws)}")
    print(f"  Fleet state keywords: {len(fleet_kws)}")
    print(f"  Gap keywords (unmet criteria): {len(gap_kws)}")
    print(f"  Past topics in novelty baseline: {len(PAST_TOPICS)}")
    
    # Score all candidates
    results = []
    for topic in CANDIDATE_TOPICS:
        r = score_topic(topic, current_kws, fleet_kws, gap_kws)
        results.append(r)
    
    # Sort by composite (descending)
    results.sort(key=lambda x: x['composite'], reverse=True)
    
    print(f"\n{'='*70}")
    print(f"TOPIC RANKING ({len(results)} candidates scored)\n{'='*70}")
    for i, r in enumerate(results, 1):
        print(f"  #{i} [{r['composite']:.3f}] {r['topic']}")
        print(f"       state={r['fleet_state_relevance']:.3f} gap={r['gap_coverage']:.3f} novelty={r['novelty']:.3f}")
    
    # Output JSON
    output = {
        'generated': datetime.now().isoformat(),
        'weights': WEIGHTS,
        'past_topics_baseline': PAST_TOPICS,
        'data_stats': {
            'current_goal_keywords': len(current_kws),
            'fleet_state_keywords': len(fleet_kws),
            'gap_keywords': len(gap_kws)
        },
        'rankings': results,
        'top_pick': results[0]['topic'] if results else None
    }
    
    out_path = Path('memory/researcher/topic-scores.json')
    out_path.write_text(json.dumps(output, indent=2), encoding='utf-8')
    print(f"\n  Output: {out_path}")
    print(f"  Top pick: '{results[0]['topic']}' (composite={results[0]['composite']:.3f})")
    
    # Write markdown summary
    md = ['# Cycle Topic Relevance Scores', '']
    md.append(f"Generated: {datetime.now().isoformat()}")
    md.append(f"\nWeights: fleet_state={WEIGHTS['fleet_state']}, gap_coverage={WEIGHTS['gap_coverage']}, novelty={WEIGHTS['novelty']}")
    md.append(f"\n## Ranking\n")
    for i, r in enumerate(results, 1):
        md.append(f"{i}. **{r['topic']}** — composite `{r['composite']:.3f}`")
        md.append(f"   - Fleet state relevance: {r['fleet_state_relevance']:.3f}")
        md.append(f"   - Gap coverage: {r['gap_coverage']:.3f}")
        md.append(f"   - Novelty: {r['novelty']:.3f}")
    md.append(f"\n## Baseline (past topics for novelty)\n")
    for t in PAST_TOPICS:
        md.append(f"- {t}")
    md.append(f"\n## Interpretation\n")
    md.append(f"Top pick: **{results[0]['topic']}** — highest alignment with current fleet state and unmet criteria while maintaining novelty vs prior cycles.")
    
    Path('memory/researcher/topic-scores.md').write_text('\n'.join(md), encoding='utf-8')
    print(f"  Summary: memory/researcher/topic-scores.md")

if __name__ == '__main__':
    main()
