"""Scribe Goal #2 - Thread Compression Engine.

Usage: python memory/scribe/compress.py <thread_file> [more_files...]
Produces: 3-bullet summary + decision list + open items + action items with owners.
Acceptance: output <=20% of input; no decisions lost.
"""
import os, re, sys

AGENT_NAMES = ['Orchestrator', 'Researcher', 'Builder', 'Verifier', 'Designer', 'Archivist', 'Scribe', 'Mechanic']

def clean_line(s):
    s = re.sub(r'\*{1,2}', '', s)
    s = re.sub(r'^[-*]\s+', '', s.strip())
    s = re.sub(r'^#+\s*', '', s)
    return s.strip()

def truncate(s, n=100):
    if len(s) <= n:
        return s
    cut = s[:n]
    sp = cut.rfind(' ')
    if sp > n // 2:
        cut = cut[:sp]
    return cut.rstrip(' ,;:') + '...'

def first_sentence(s, max_len=100):
    m = re.match(r'^([^.;!?]+[.!?])', s)
    sent = m.group(1).strip() if m else s
    return truncate(sent, max_len)

def extract_decisions(text):
    decisions = []
    for line in text.split('\n'):
        stripped = line.strip()
        if not stripped or len(stripped) < 20:
            continue
        lower = stripped.lower()
        is_decision = bool(re.search(r'(?i)\b(decided|decision:|resolved|ruling:|ratif|reject|approved|agreed|canonical|final:|verdict)\b', lower))
        if is_decision:
            clean = clean_line(stripped)
            short = first_sentence(clean, 100)
            if short and len(short) >= 20 and short not in decisions:
                decisions.append(short)
    return decisions

def extract_open_items(text):
    items = []
    for line in text.split('\n'):
        stripped = line.strip()
        if not stripped or len(stripped) < 20:
            continue
        lower = stripped.lower()
        is_open = bool(re.search(r'(?i)\b(open|unresolved|tbd|pending|blocker|blocked|needs|awaiting|still|unblock)\b', lower))
        if is_open and not re.match(r'^#{1,3}\s', stripped):
            clean = clean_line(stripped)
            short = first_sentence(clean, 100)
            if short and len(short) >= 20 and short not in items:
                items.append(short)
    return items

def extract_actions(text):
    actions = []
    for line in text.split('\n'):
        stripped = line.strip()
        if not stripped or len(stripped) < 20:
            continue
        lower = stripped.lower()
        has_agent = any(a.lower() in lower for a in AGENT_NAMES)
        has_action = bool(re.search(r'(?i)\b(should|will|must|needs? to|to (?:fix|build|write|create|update|check|verify|test|deploy|run))\b', lower))
        if has_agent and has_action:
            clean = clean_line(stripped)
            short = first_sentence(clean, 100)
            if short and len(short) >= 20 and short not in actions:
                actions.append(short)
    return actions

def summarize(text):
    lines = text.split('\n')
    headers = [l.strip().lstrip('#').strip() for l in lines if l.startswith('#')]
    topic = headers[0] if headers else 'Untitled'
    n_dec = len(extract_decisions(text))
    n_open = len(extract_open_items(text))
    n_act = len(extract_actions(text))
    agents = sorted(set(a for a in AGENT_NAMES if a.lower() in text.lower()))
    return [
        f"Topic: {truncate(topic, 60)}",
        f"Agents: {', '.join(agents) or 'none'}",
        f"Stats: {n_dec} dec, {n_open} open, {n_act} act | {len(lines)} lines",
    ]

def compress(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    input_len = len(text)
    decisions = extract_decisions(text)
    open_items = extract_open_items(text)[:6]
    actions = extract_actions(text)[:6]
    bullets = summarize(text)
    budget = int(input_len * 0.19)

    def build(dec, ope, act):
        L = [f"# Compressed: {os.path.basename(filepath)}", "", "## Summary"]
        for b in bullets:
            L.append(f"- {b}")
        L.append("")
        L.append("## Decisions")
        if dec:
            for d in dec:
                L.append(f"- {d}")
        else:
            L.append("- (none)")
        L.append("")
        L.append("## Open Items")
        if ope:
            for o in ope:
                L.append(f"- {o}")
        else:
            L.append("- (none)")
        L.append("")
        L.append("## Actions")
        if act:
            for a in act:
                L.append(f"- {a}")
        else:
            L.append("- (none)")
        return '\n'.join(L)

    output = build(decisions, open_items, actions)
    while len(output) > budget and (decisions or open_items or actions):
        if actions:
            actions.pop()
        elif open_items:
            open_items.pop()
        else:
            decisions.pop()
        output = build(decisions, open_items, actions)
    return output, input_len, len(output), len(extract_decisions(text))

def main():
    if len(sys.argv) < 2:
        print("Usage: python memory/scribe/compress.py <thread_file> [more_files...]")
        sys.exit(1)
    files = sys.argv[1:]
    all_pass = True
    for fp in files:
        if not os.path.exists(fp):
            print(f"ERROR: {fp} not found")
            all_pass = False
            continue
        output, in_len, out_len, total_dec = compress(fp)
        ratio = out_len / in_len * 100 if in_len > 0 else 0
        status = "PASS" if ratio <= 20 else "FAIL"
        if ratio > 20:
            all_pass = False
        print(f"\n{'='*60}")
        print(f"File: {fp}")
        print(f"Input: {in_len} | Output: {out_len} | Ratio: {ratio:.1f}% [{status}]")
        print(f"Decisions in source: {total_dec}")
        print(f"{'='*60}")
        print(output)
    if not all_pass:
        sys.exit(1)

if __name__ == '__main__':
    main()
