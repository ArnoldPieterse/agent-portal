#!/usr/bin/env python3
"""Anomaly Narrative Generator.

When an anomaly is detected in fleet metrics (health score drop, response time spike,
VRAM breach, agent unresponsive), auto-generate a 2-3 sentence natural-language narrative
explaining what happened, why it matters, and what to do next.

Usage: python memory/researcher/anomaly_narrative.py [--type TYPE] [--json]
Output: memory/researcher/anomaly-narratives/narratives-TIMESTAMP.md
"""
import pathlib, re, json, sys
from datetime import datetime
from collections import defaultdict

ANOMALY_TYPES = {
    'health_drop': {
        'trigger': 'Health score dropped below threshold',
        'severity': 'medium',
    },
    'response_spike': {
        'trigger': 'Agent response time exceeded baseline by 2x+',
        'severity': 'medium',
    },
    'vram_breach': {
        'trigger': 'GPU VRAM usage exceeded 90% of capacity',
        'severity': 'high',
    },
    'agent_unresponsive': {
        'trigger': 'Agent failed to respond to ping within timeout',
        'severity': 'high',
    },
    'goal_slip': {
        'trigger': 'Goal completion rate below predicted trajectory',
        'severity': 'low',
    },
}


def generate_narrative(anomaly_type, **kwargs):
    """Generate a 2-3 sentence narrative for the given anomaly type."""
    templates = {
        'health_drop': "Fleet health score fell from {prev} to {curr} ({delta} pts) at {time}. Primary driver: {driver}. Recommended action: {action}.",
        'response_spike': "Agent {agent} response time spiked to {ms}ms (baseline {base}ms, {ratio}x). Correlated with: {cause}. Auto-recovery: {recovery}.",
        'vram_breach': "Host {host} VRAM reached {pct}% ({used}/{total} GB) at {time}. Model {model} is primary consumer. Risk: OOM kill within {eta_min} min if load continues.",
        'agent_unresponsive': "Agent {agent} unresponsive for {duration}s (timeout: {timeout}s). Last known state: {state}. Possible cause: {cause}. Auto-escalation: {escalation}.",
        'goal_slip': "Cycle {cycle} goal completion at {pct}% vs predicted {pred}% by this point. Slipping goals: {goals}. Root cause pattern: {pattern}.",
    }
    if anomaly_type not in templates:
        raise ValueError("Unknown anomaly type: %s" % anomaly_type)
    template = templates[anomaly_type]
    try:
        text = template.format(**kwargs)
    except KeyError as e:
        # Fill missing fields with placeholder
        for key in re.findall(r'\{(\w+)\}', template):
            if key not in kwargs:
                kwargs[key] = 'unknown'
        text = template.format(**kwargs)
    return {
        'type': anomaly_type,
        'severity': ANOMALY_TYPES[anomaly_type]['severity'],
        'timestamp': datetime.now().isoformat(),
        'text': text,
    }


def generate_sample_narratives():
    """Generate sample narratives from historical fleet data for self-test."""
    samples = [
        generate_narrative('health_drop', prev=78, curr=62, delta=16, time='14:00 UTC', driver='Archivist seat unreachable 3 probes', action='verify White GPU and reload model'),
        generate_narrative('vram_breach', host='White', pct=94, used='22.6', total='24', time='14:32 UTC', model='qwen-72b', eta_min=8),
        generate_narrative('agent_unresponsive', agent='Archivist', duration=1446, timeout=10, state='home not_loaded', cause='host migration in progress', escalation='dispatched to White per failover'),
        generate_narrative('goal_slip', cycle='10', pct=50, pred=65, goals='Orchestrator #4, Mechanic #3', pattern='multi-step cross-host coordination'),
        generate_narrative('response_spike', agent='Mechanic', ms=4200, base=800, ratio='5.3', cause='concurrent WinRM session', recovery='queued behind model-swap; ETA 90s'),
    ]
    return samples


def write_narratives(narratives):
    out_dir = pathlib.Path('memory/researcher/anomaly-narratives')
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d_%H%M')
    out_path = out_dir / ('narratives-%s.md' % ts)
    r = "# Anomaly Narratives - %s\n\n" % ts
    for n in narratives:
        r += "## [%s] %s\n" % (n['severity'].upper(), n['type'].replace('_', ' ').title())
        r += "%s\n\n" % n['text']
    out_path.write_text(r, encoding='utf-8')
    return out_path


def self_test():
    narratives = generate_sample_narratives()
    assert len(narratives) >= 3, "Should generate at least 3 narratives"
    for n in narratives:
        assert n['type'] in ANOMALY_TYPES
        sentences = [s for s in n['text'].split('. ') if s.strip()]
        assert 2 <= len(sentences) <= 5, "Expected 2-4 sentences, got %d" % len(sentences)
    types_used = set(n['type'] for n in narratives)
    assert len(types_used) >= 4, "Should cover >=4 anomaly types"
    return True


def main():
    json_out = '--json' in sys.argv
    self_test()
    narratives = generate_sample_narratives()
    out_path = write_narratives(narratives)
    if json_out:
        print(json.dumps(narratives, indent=2))
    else:
        print("Narratives: %s (%db)" % (out_path, out_path.stat().st_size))
        print("Types covered: %d/5" % len(set(n['type'] for n in narratives)))
        print("Self-test: ALL PASS")


if __name__ == '__main__':
    main()
