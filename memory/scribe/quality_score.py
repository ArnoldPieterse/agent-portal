"""Synthesis Quality Scorer (Scribe goal #6).
Scores synthesis docs on 4 dimensions: completeness, accuracy, conciseness, actionability.
Usage: python memory/scribe/quality_score.py [file ...]
Without args, scores the 5 most recent non-DRAFT .md files in memory/synthesis/.
"""
import os, re, sys, json
from datetime import datetime

SYNTHESIS_DIR = "memory/synthesis"

def find_files(args):
    if args:
        return args
    files = []
    for f in os.listdir(SYNTHESIS_DIR):
        if f.endswith(".md") and "DRAFT" not in f.upper():
            files.append(os.path.join(SYNTHESIS_DIR, f))
    files.sort(key=os.path.getmtime, reverse=True)
    return files[:5]

def score_completeness(text, filename):
    """Check for structural coverage: headers, sections, references to other docs."""
    score = 5  # baseline
    headers = re.findall(r"^#{1,3}\s+.+$", text, re.MULTILINE)
    if len(headers) >= 3:
        score += 1
    if len(headers) >= 6:
        score += 1
    # References to other files/agents
    refs = re.findall(r"(?:memory/|TODO\.md|agents?\.)", text)
    if len(refs) >= 3:
        score += 1
    # Mentions multiple agents
    agents_mentioned = set()
    for agent in ["Orchestrator","Researcher","Builder","Verifier","Designer","Archivist","Scribe","Mechanic"]:
        if agent.lower() in text.lower():
            agents_mentioned.add(agent)
    if len(agents_mentioned) >= 3:
        score += 1
    # Has a date or round identifier
    if re.search(r"\d{4}-\d{2}-\d{2}|round|cycle|R\d+", text, re.I):
        score += 1
    return min(score, 10)

def score_accuracy(text, filename):
    """Check file paths exist, dates are valid, no obvious contradictions."""
    score = 10  # start high, deduct for issues
    # Check referenced file paths
    paths = re.findall(r"\b(?:memory/[\w/._-]+|TODO\.md|agents\.json|index\.html)\b", text)
    missing = []
    for p in set(paths):
        if not os.path.exists(p):
            missing.append(p)
    if missing:
        score -= min(len(missing), 4)  # max -4 for missing paths
    # Check dates are valid format
    dates = re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    invalid_dates = []
    for d in dates:
        try:
            datetime.strptime(d, "%Y-%m-%d")
        except ValueError:
            invalid_dates.append(d)
    if invalid_dates:
        score -= min(len(invalid_dates), 3)
    # Flag self-contradictions (same term with "NOT" / "no longer" patterns)
    contradictions = re.findall(r"(?:is NOT|no longer|reverted|undone|canceled)", text, re.I)
    if len(contradictions) > 3:
        score -= 1  # heavy revision history may indicate instability
    return max(score, 1)

def score_conciseness(text, filename):
    """Measure redundancy and information density."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return 1
    # Check for repeated lines (exact or near-exact)
    seen = set()
    repeats = 0
    for line in lines:
        key = line.lower()[:80]  # first 80 chars as fingerprint
        if key in seen and len(key) > 20:
            repeats += 1
        seen.add(key)
    density = 1 - (repeats / max(len(lines), 1))
    # Word count vs line count ratio (very long lines may be dense or run-on)
    words = len(text.split())
    avg_line_len = words / max(len(lines), 1)
    
    score = int(density * 8) + 2  # base from density
    if avg_line_len > 60:
        score -= 1  # very long lines, harder to scan
    if len(lines) < 5:
        score -= 1  # too short to be a synthesis
    return max(1, min(score, 10))

def score_actionability(text, filename):
    """Check for clear next steps with owners."""
    score = 3  # baseline
    # Look for action items: lines with "TODO", "next", "action", "owner"
    action_lines = re.findall(r"^(?:[-*\d.]+|>?)\s*(?:TODO|NEXT|ACTION|OWNED|ASSIGNED).*:?.*$", text, re.MULTILINE | re.I)
    if len(action_lines) >= 3:
        score += 2
    elif len(action_lines) >= 1:
        score += 1
    # Owner attribution: "Owner: X" or "@AgentName" patterns
    owners = re.findall(r"(?:owner|assigned to|@)(?:\s*:?)?\s*(Orchestrator|Researcher|Builder|Verifier|Designer|Archivist|Scribe|Mechanic)", text, re.I)
    if len(owners) >= 3:
        score += 2
    elif len(owners) >= 1:
        score += 1
    # Deadline or date on actions
    deadlines = re.findall(r"(?:due|by|deadline|target)[:\s]+\d{4}-\d{2}-\d{2}", text, re.I)
    if deadlines:
        score += 1
    # "Next steps" or "Follow-up" section
    if re.search(r"^#{1,3}\s+(?:next steps|follow.?up|action items|open items)", text, re.MULTILINE | re.I):
        score += 1
    return min(score, 10)

def score_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    
    c = score_completeness(text, filepath)
    a = score_accuracy(text, filepath)
    co = score_conciseness(text, filepath)
    ac = score_actionability(text, filepath)
    composite = round((c + a + co + ac) / 4, 1)
    
    return {
        "file": filepath,
        "completeness": c,
        "accuracy": a,
        "conciseness": co,
        "actionability": ac,
        "composite": composite,
        "word_count": len(text.split()),
        "line_count": len([l for l in text.split("\n") if l.strip()])
    }

def main():
    args = sys.argv[1:]
    files = find_files(args)
    results = []
    for f in files:
        if not os.path.exists(f):
            print(f"  SKIP (not found): {f}")
            continue
        r = score_file(f)
        results.append(r)
        status = "PASS" if r["composite"] >= 8.0 else "BELOW TARGET"
        print(f"  {os.path.basename(f):50s} C={r['completeness']} A={r['accuracy']} Co={r['conciseness']} Ac={r['actionability']} | composite={r['composite']} [{status}]")
    
    if results:
        avg = round(sum(r["composite"] for r in results) / len(results), 2)
        print(f"\n  Average composite: {avg}/10 (target >8.0)")
        
        # Write JSON evidence
        out_path = "memory/scribe/quality_score_run.json"
        with open(out_path, "w") as f:
            json.dump({"date": datetime.now().isoformat(), "results": results, "average": avg}, f, indent=2)
        print(f"  Evidence written to {out_path}")

if __name__ == "__main__":
    main()
