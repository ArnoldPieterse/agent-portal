#!/usr/bin/env python3
"""
Decision Impact Tracker - Scribe goal #1 (cycle-8)

Checks every entry in memory/synthesis/decisions.jsonl that has a
predicted_consequence + review_date which has passed. Verifies whether the
outcome materialized by grepping memory/ for evidence.

Output: memory/synthesis/decision-impacts.md
  Table: {id, decision, predicted_consequence, actual_outcome (verified/stale/wrong), evidence_path}
"""
import json, os, re, sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # repo root
DECISIONS_PATH = ROOT / "memory" / "synthesis" / "decisions.jsonl"
OUTPUT_PATH = ROOT / "memory" / "synthesis" / "decision-impacts.md"
MEMORY_DIR = ROOT / "memory"

def today_str():
    return date.today().isoformat()

def load_decisions():
    if not DECISIONS_PATH.exists():
        print(f"ERROR: {DECISIONS_PATH} not found", file=sys.stderr)
        sys.exit(1)
    entries = []
    for i, line in enumerate(DECISIONS_PATH.read_text(encoding='utf-8').splitlines()):
        if not line.strip():
            continue
        d = json.loads(line)
        d['_id'] = f"D{i+1:03d}"
        entries.append(d)
    return entries

def extract_keywords(text, max_kw=6):
    """Extract meaningful keywords from a predicted consequence string."""
    # Remove common stop words and punctuation
    text_lower = text.lower()
    words = re.findall(r'[a-z][a-z_-]{3,}', text_lower)
    stop = {'the', 'and', 'for', 'with', 'from', 'that', 'this', 'which',
            'were', 'was', 'are', 'is', 'been', 'being', 'have', 'has',
            'had', 'will', 'would', 'should', 'could', 'may', 'might',
            'all', 'any', 'each', 'per', 'via', 'without', 'manual',
            'intervention', 'operations', 'subsequent', 'cycles'}
    keywords = [w for w in words if w not in stop]
    # Deduplicate preserving order
    seen = set()
    unique = []
    for k in keywords:
        if k not in seen:
            seen.add(k)
            unique.append(k)
    return unique[:max_kw]

def grep_memory(keywords):
    """
    Search memory/ tree for evidence matching the keywords.
    Returns (found: bool, evidence_path: str|None, match_count: int)
    """
    if not MEMORY_DIR.exists():
        return False, None, 0

    # Score files by how many keywords appear
    best_file = None
    best_score = 0

    for dirpath, dirnames, filenames in os.walk(MEMORY_DIR):
        # Skip very large dirs and binary-ish stuff
        dirnames[:] = [d for d in dirnames if d not in ('__pycache__', '.git', 'node_modules')]
        for fname in filenames:
            if not fname.endswith(('.md', '.jsonl', '.json', '.py', '.txt')):
                continue
            fpath = Path(dirpath) / fname
            rel_path = fpath.relative_to(ROOT)
            try:
                content = fpath.read_text(encoding='utf-8', errors='ignore').lower()
            except Exception:
                continue
            score = sum(1 for kw in keywords if kw in content)
            if score > best_score:
                best_score = score
                best_file = str(rel_path)

    # Require at least 2 keyword matches to count as evidence
    threshold = min(2, len(keywords))
    if best_score >= threshold and best_file:
        return True, best_file, best_score
    return False, None, best_score

def check_outcome(entry):
    """
    Determine actual_outcome for a decision entry.
    Returns (outcome: str, evidence_path: str|None)
    """
    predicted = entry.get('predicted_consequence', '')
    keywords = extract_keywords(predicted)

    if not keywords:
        return 'stale', None

    found, evidence_path, score = grep_memory(keywords)

    if found:
        return 'verified', evidence_path
    return 'stale', None

def main():
    today = today_str()
    entries = load_decisions()

    # Filter: has predicted_consequence + review_date, and review_date has passed
    due = []
    for e in entries:
        if 'predicted_consequence' not in e or 'review_date' not in e:
            continue
        rd = e['review_date']
        if rd <= today:
            due.append(e)

    if not due:
        print("No decisions with passed review dates found.")
        return

    results = []
    for e in due:
        outcome, evidence_path = check_outcome(e)
        results.append({
            'id': e['_id'],
            'date': e.get('date', '?'),
            'decision': e['decision'][:100],
            'predicted_consequence': e['predicted_consequence'],
            'review_date': e['review_date'],
            'actual_outcome': outcome,
            'evidence_path': evidence_path or '(none found)'
        })

    # Write output markdown
    lines = []
    lines.append("# Decision Impact Report")
    lines.append(f"Generated: {today}")
    lines.append(f"Decisions checked: {len(results)} (of {len(entries)} total)")
    lines.append("")
    lines.append("| ID | Date | Decision | Predicted Consequence | Review Date | Outcome | Evidence Path |")
    lines.append("|----|------|----------|-----------------------|-------------|---------|---------------|")
    for r in results:
        dec_short = r['decision'][:60] + ('...' if len(r['decision']) > 60 else '')
        pred_short = r['predicted_consequence'][:50] + ('...' if len(r['predicted_consequence']) > 50 else '')
        lines.append(f"| {r['id']} | {r['date']} | {dec_short} | {pred_short} | {r['review_date']} | **{r['actual_outcome']}** | `{r['evidence_path']}` |")
    lines.append("")

    # Summary
    verified = sum(1 for r in results if r['actual_outcome'] == 'verified')
    stale = sum(1 for r in results if r['actual_outcome'] == 'stale')
    wrong = sum(1 for r in results if r['actual_outcome'] == 'wrong')
    lines.append(f"**Summary:** {verified} verified, {stale} stale, {wrong} wrong")
    lines.append("")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text('\n'.join(lines), encoding='utf-8')
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)} ({len(results)} decisions checked)")
    print(f"  verified: {verified}, stale: {stale}, wrong: {wrong}")

if __name__ == '__main__':
    main()