#!/usr/bin/env python3
"""cockpit-load-audit.py — Cognitive Load Audit Script
   Cycle-12 Goal 10 | Designer | 2026-11-24
   Counts visible text nodes, distinct colors, and interactive elements above the fold.
   Violation (> threshold) fails the QA gate.
"""
import sys, re, json
from pathlib import Path

# Thresholds from cognitive-budget.md
MAX_PRIMARY_CHANNELS = 3
MAX_TEXT_NODES_ABOVE_FOLD = 12
MAX_DISTINCT_COLORS = 8
MAX_INTERACTIVE_ELEMENTS = 6

def audit(html_path: str) -> dict:
    content = Path(html_path).read_text(encoding='utf-8', errors='replace')
    results = {'file': html_path, 'pass': True, 'violations': []}

    # Count text nodes (approximate: strip tags, count non-empty text segments)
    text_content = re.sub(r'<[^>]+>', ' ', content)
    text_segments = [s.strip() for s in text_content.split() if len(s.strip()) > 2]
    results['text_nodes'] = len(text_segments)
    if len(text_segments) > MAX_TEXT_NODES_ABOVE_FOLD:
        results['violations'].append(f"text nodes ({len(text_segments)}) > {MAX_TEXT_NODES_ABOVE_FOLD}")

    # Count distinct colors (hex + named in CSS)
    hex_colors = set(re.findall(r'#[0-9a-fA-F]{3,8}\b', content))
    named_colors = set(re.findall(r'\b(?:red|blue|green|orange|amber|gray|grey|white|black)\b', content.lower()))
    results['distinct_colors'] = len(hex_colors) + len(named_colors)
    if len(hex_colors) + len(named_colors) > MAX_DISTINCT_COLORS:
        results['violations'].append(f"distinct colors ({len(hex_colors)+len(named_colors)}) > {MAX_DISTINCT_COLORS}")

    # Count interactive elements (buttons, links, inputs, [role=button], [tabindex])
    interactive = re.findall(r'<(?:button|a\s|input|select)[^>]*>', content)
    role_button = re.findall(r'role="button"', content)
    tabindex = re.findall(r'tabindex="[^"]*"', content)
    results['interactive_elements'] = len(interactive) + len(role_button) + len(tabindex)
    if len(interactive) + len(role_button) + len(tabindex) > MAX_INTERACTIVE_ELEMENTS:
        results['violations'].append(f"interactive elements ({len(interactive)+len(role_button)+len(tabindex)}) > {MAX_INTERACTIVE_ELEMENTS}")

    # Primary visual channels (distinct color families used for state coding)
    state_colors = set(re.findall(r'--(?:color|status)-(?:success|warn|critical|muted|text)', content))
    results['primary_channels'] = len(state_colors)
    if len(state_colors) > MAX_PRIMARY_CHANNELS:
        results['violations'].append(f"primary channels ({len(state_colors)}) > {MAX_PRIMARY_CHANNELS}")

    results['pass'] = len(results['violations']) == 0
    return results

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
    result = audit(target)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result['pass'] else 1)
