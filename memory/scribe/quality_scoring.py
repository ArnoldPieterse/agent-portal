#!/usr/bin/env python3
"""Synthesis Quality Scoring - Goal 6
Scores every file in memory/synthesis/ on clarity, completeness, actionability, recency.
Usage: python memory/scribe/quality_scoring.py [--json] [--min-score N]
"""
import os, re, json, sys, argparse
from datetime import datetime, date
from pathlib import Path

SYNTHESIS_DIR = Path("memory/synthesis")
TODAY = date(2026, 11, 20)  # will be overridden at runtime

# --- Scoring heuristics ---

def score_clarity(text: str, filename: str) -> float:
    """Can a new agent understand this? Heuristics:
    - Has a clear title/heading (first line is # or ##)
    - Has structured sections (>=2 headings)
    - Average sentence length < 30 words
    - No wall-of-text paragraphs > 400 chars without breaks
    """
    score = 50.0  # baseline
    lines = text.strip().split("\n")
    
    # Title present
    if lines and lines[0].startswith("#"):
        score += 10
    else:
        score -= 10
    
    # Structured sections (>=2 headings)
    headings = [l for l in lines if l.startswith("#")]
    if len(headings) >= 3:
        score += 15
    elif len(headings) == 2:
        score += 8
    else:
        score -= 5
    
    # Sentence length (approximate)
    sentences = re.split(r'[.!?]\s+', text)
    if sentences:
        avg_len = sum(len(s.split()) for s in sentences) / len(sentences)
        if avg_len < 20:
            score += 15
        elif avg_len < 30:
            score += 8
        elif avg_len > 50:
            score -= 15
    
    # Wall of text check
    long_paragraphs = sum(1 for p in text.split("\n\n") if len(p) > 400 and "\n" not in p)
    score -= min(long_paragraphs * 5, 20)
    
    return max(0, min(100, score))


def score_completeness(text: str, filename: str) -> float:
    """Does it cover the full decision? Heuristics:
    - Has context/background section or mentions 'context'
    - Has a clear decision statement
    - Mentions owner/agent names
    - Has next steps or follow-up
    """
    score = 30.0  # baseline (most files won't have all)
    lower = text.lower()
    
    # Context indicators
    context_markers = ["context", "background", "situation", "state before", "prior state"]
    if any(m in lower for m in context_markers):
        score += 15
    
    # Decision statement
    decision_markers = ["decision:", "decided", "agreed:", "ratified", "ruling:", "verdict:", "conclusion:"]
    if any(m in lower for m in decision_markers):
        score += 20
    
    # Agent/owner mentions
    agent_names = ["scribe", "researcher", "builder", "verifier", "designer", "archivist", "mechanic", "orchestrator"]
    agents_found = sum(1 for a in agent_names if a in lower)
    score += min(agents_found * 3, 15)
    
    # Next steps / follow-up
    next_markers = ["next step", "follow-up", "action item", "todo:", "open question", "remaining"]
    if any(m in lower for m in next_markers):
        score += 10
    
    # File length (too short = incomplete)
    if len(text) < 200:
            score -= 15
    elif len(text) > 3000:
        score += 5  # thorough
    
    return max(0, min(100, score))


def score_actionability(text: str, filename: str) -> float:
    """Is there a concrete next step? Heuristics:
    - Contains file paths (memory/...)
    - Contains commands (python ..., git ...)
    - Has explicit action verbs with targets
    - References specific agents to act
    """
    score = 20.0  # baseline
    
    # File paths
    paths = re.findall(r'memory/[\w/._-]+', text)
    score += min(len(paths) * 3, 15)
    
    # Commands
    commands = re.findall(r'(?:python|git|curl|powershell)\s+\S+', text)
    score += min(len(commands) * 4, 20)
    
    # Action items (numbered or bulleted with verbs, or checkbox items)
    action_lines = re.findall(r'^[\s]*[-*\d]+\.?\s+(?:run|create|add|fix|update|build|write|test|verify|deploy)', text, re.MULTILINE | re.IGNORECASE)
    checkboxes = re.findall(r'^[\s]*[-*]\s*\[[ xX]\]', text, re.MULTILINE)
    score += min(len(action_lines) * 5 + len(checkboxes) * 4, 20)
    
    # Agent assignment
    agent_assign = re.findall(r'(?:@\w+|owner:|assigned to|\(Mechanic|\(Scribe|\(Builder|\(Researcher)', text, re.IGNORECASE)
    score += min(len(agent_assign) * 5, 10)
    
    # Explicit next-step section
    if re.search(r'(?:next steps?|action items?|follow-?ups?)\s*[:#]', text, re.IGNORECASE):
        score += 15
    
    return max(0, min(100, score))


def score_recency(filename: str) -> float:
    """Recency based on date in filename.
    <7 days = 90-100, <30 days = 50-89, 30-60 days = 20-49, >60 days = 0-19
    """
    # Extract date from filename (YYYY-MM-DD pattern)
    m = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if not m:
        return 30.0  # unknown date, neutral-low
    
    try:
        file_date = datetime.strptime(m.group(1), "%Y-%m-%d").date()
    except ValueError:
        return 30.0
    
    age_days = (TODAY - file_date).days
    if age_days < 0:
        return 50.0  # future-dated, suspicious
    elif age_days <= 7:
        return 100.0 - (age_days / 7) * 10  # 90-100
    elif age_days <= 30:
        return 80.0 - ((age_days - 7) / 23) * 30  # 50-80
    elif age_days <= 60:
        return 40.0 - ((age_days - 30) / 30) * 20  # 20-40
    else:
        return max(0, 20.0 - (age_days - 60) * 0.5)


def score_file(filepath: Path) -> dict:
    """Score a single synthesis file."""
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"file": str(filepath), "error": str(e)}
    
    clarity = score_clarity(text, filepath.name)
    completeness = score_completeness(text, filepath.name)
    actionability = score_actionability(text, filepath.name)
    recency = score_recency(filepath.name)
    
    overall = round(clarity * 0.3 + completeness * 0.3 + actionability * 0.2 + recency * 0.2, 1)
    
    return {
        "file": str(filepath).replace("\\", "/"),
        "clarity": round(clarity, 1),
        "completeness": round(completeness, 1),
        "actionability": round(actionability, 1),
        "recency": round(recency, 1),
        "overall": overall,
    }


def main():
    global TODAY
    TODAY = date.today()
    
    parser = argparse.ArgumentParser(description="Score synthesis files")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--min-score", type=float, default=0, help="Filter by min overall score")
    args = parser.parse_args()
    
    if not SYNTHESIS_DIR.exists():
        print(f"ERROR: {SYNTHESIS_DIR} not found", file=sys.stderr)
        sys.exit(1)
    
    files = sorted(SYNTHESIS_DIR.glob("*.md"))
    results = [score_file(f) for f in files]
    results = [r for r in results if "error" not in r]
    
    # Filter
    filtered = [r for r in results if r["overall"] >= args.min_score]
    
    # Fleet averages
    if results:
        avg = {
            "clarity": round(sum(r["clarity"] for r in results) / len(results), 1),
            "completeness": round(sum(r["completeness"] for r in results) / len(results), 1),
            "actionability": round(sum(r["actionability"] for r in results) / len(results), 1),
            "recency": round(sum(r["recency"] for r in results) / len(results), 1),
            "overall": round(sum(r["overall"] for r in results) / len(results), 1),
        }
    else:
        avg = {"clarity": 0, "completeness": 0, "actionability": 0, "recency": 0, "overall": 0}
    
    output = {
        "scored_at": TODAY.isoformat(),
        "total_files": len(results),
        "fleet_avg": avg,
        "files": filtered if args.min_score > 0 else results,
    }
    
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print(f"Synthesis Quality Report - {TODAY.isoformat()}")
        print(f"Files scored: {len(results)}")
        print(f"Fleet avg: clarity={avg['clarity']} completeness={avg['completeness']} actionability={avg['actionability']} recency={avg['recency']} overall={avg['overall']}")
        print("\nPer-file scores (sorted by overall desc):")
        for r in sorted(results, key=lambda x: -x["overall"]):
            print(f"  {r['overall']:5.1f}  C={r['clarity']:3.0f} Co={r['completeness']:3.0f} A={r['actionability']:3.0f} R={r['recency']:3.0f}  {os.path.basename(r['file'])}")


if __name__ == "__main__":
    main()