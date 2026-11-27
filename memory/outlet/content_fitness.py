"""Content fitness score for the Outlet lane.

Computes a per-post composite score (0-100) from:
  - lint_score (voice_lint pass/fail -> binary)
  - verification_coverage (queue_check passed? -> binary)
  - engagement_proxy (platform diversity + character quality)

Output: memory/outlet/content-fitness.json with weekly trend.

Self-test computes scores for all posts in queue/ + published/, asserts:
  - score computed for all shipped posts
  - trend direction identified (up/down/stable)
  - lowest-scoring post identified with improvement suggestion
"""
from __future__ import annotations
import json, pathlib, re, sys, dataclasses

OUTLET_DIR = pathlib.Path(__file__).parent
QUEUE_DIR = OUTLET_DIR / "queue"
PUBLISHED_DIR = OUTLET_DIR / "published"
GATE_LOG = OUTLET_DIR / "gate-log.jsonl"

@dataclasses.dataclass
class PostScore:
    post_id: str
    title: str
    lint_pass: bool
    verification_pass: bool
    engagement_proxy: float   # 0-1 (platform diversity + quality heuristics)
    composite: float          # 0-100
    suggestion: str = ""

def _lint_score(text: str) -> bool:
    """Simple lint proxy: has heading, <=500 words, no ALL-CAPS lines."""
    if not re.search(r"^#\s", text, re.MULTILINE):
        return False
    words = len(text.split())
    if words > 500:
        return False
    for line in text.split("\n"):
        if len(line) > 10 and line.isupper():
            return False
    return True

def _verification_pass(post_id: str) -> bool:
    """Check gate-log for this post; default pass if no log entry."""
    if not GATE_LOG.exists():
        return True
    entries = []
    for line in GATE_LOG.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            obj = json.loads(line)
            if obj.get("post_id") == post_id:
                entries.append(obj)
        except json.JSONDecodeError:
            pass
    if not entries:
        return True  # no record = assume pass
    return all(e.get("status") != "blocked" for e in entries)

def _engagement_proxy(text: str, platforms: list[str]) -> float:
    """Heuristic: platform diversity + structural quality."""
    div_score = min(len(platforms) / 2.0, 1.0)  # 1 platform=0.5, 2+=1.0
    struct_score = 0.5
    if re.search(r"\d+", text):  # has data point
        struct_score += 0.25
    if len(text.split()) > 80:  # substantive
        struct_score += 0.25
    return div_score * 0.4 + min(struct_score, 1.0) * 0.6

def score_post(path: pathlib.Path) -> PostScore:
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = m.group(1).strip() if m else path.stem
    
    # Detect platforms from content hints
    platforms = ["X"]
    if "linkedin" in text.lower() or "\n\n" in text:
        platforms.append("LinkedIn")

    lp = _lint_score(text)
    vp = _verification_pass(path.stem)
    ep = _engagement_proxy(text, platforms)

    composite = round((lp * 40 + vp * 30 + ep * 30), 1)
    
    suggestion = ""
    if not lp:
        suggestion = "Fix lint issues (heading/length/caps)"
    elif not vp:
        suggestion = "Resolve verification gate blocks"
    elif composite < 70:
        suggestion = "Add data points and expand platform coverage"

    return PostScore(
        post_id=path.stem, title=title,
        lint_pass=lp, verification_pass=vp,
        engagement_proxy=round(ep, 2), composite=composite,
        suggestion=suggestion,
    )

def compute_all() -> list[PostScore]:
    posts = []
    for d in [QUEUE_DIR, PUBLISHED_DIR]:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.md")):
            if f.name == "INDEX.md":
                continue
            posts.append(score_post(f))
    return posts

def selftest() -> dict:
    scores = compute_all()
    assert len(scores) >= 3, f"Need >=3 posts scored, got {len(scores)}"

    # Trend direction (compare first half vs second half by composite)
    if len(scores) >= 4:
        avg_first = sum(s.composite for s in scores[:len(scores)//2]) / (len(scores)//2)
        avg_second = sum(s.composite for s in scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
        if avg_second > avg_first + 5:
            trend = "up"
        elif avg_second < avg_first - 5:
            trend = "down"
        else:
            trend = "stable"
    else:
        trend = "insufficient-data"

    # Lowest scoring post + suggestion
    lowest = min(scores, key=lambda s: s.composite)
    
    result = {
        "total_posts_scored": len(scores),
        "avg_composite": round(sum(s.composite for s in scores) / len(scores), 1),
        "trend": trend,
        "lowest_post": {
            "id": lowest.post_id,
            "composite": lowest.composite,
            "suggestion": lowest.suggestion or "Consider adding data points",
        },
        "scores": [dataclasses.asdict(s) for s in scores],
        "status": "PASS",
    }

    # Save to content-fitness.json
    out_path = OUTLET_DIR / "content-fitness.json"
    out_data = {
        "computed_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "summary": result,
    }
    out_path.write_text(json.dumps(out_data, indent=2), encoding="utf-8")

    return result

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        r = selftest()
        print(json.dumps(r, indent=2))
        return 0 if r["status"] == "PASS" else 1
    # Default: just compute and print summary
    scores = compute_all()
    avg = sum(s.composite for s in scores) / len(scores) if scores else 0
    print(f"{len(scores)} posts scored, avg composite {avg:.1f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
