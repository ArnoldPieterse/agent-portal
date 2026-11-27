#!/usr/bin/env python3
"""
Designer goal-evidence integrity checker.
Parses memory/goals/designer.md, extracts every referenced ui/* artifact from the
'('verified: ...)' evidence spans, and asserts each file exists on disk (non-empty).
Emits JSON so the fleet convergence metric's underlying evidence is checkable.

Why: /api/goals counts a goal as 'reached' on its '(verified: ...)' marker. If the
referenced artifact was later deleted or never landed, the fleet % is inflated.
This sweep catches that class of false/stale claim (see memory/ops/blockers.md,
OPS-NOTE 2026-11-25 'false evidence claim').

Usage: python memory/designer/verify_goal_evidence.py [--json out.json]
Exit code: 0 = all referenced artifacts present; 1 = one or more missing.
"""
import re, sys, json, pathlib, datetime

ROOT = pathlib.Path(__file__).resolve().parents[2]  # repo root (memory/designer/x.py -> root)
GOALS = ROOT / "memory" / "goals" / "designer.md"
OUT_DEFAULT = ROOT / "memory" / "designer" / "goal-evidence-integrity.json"

# match artifact refs like ui/cockpit-convergence.js, ui/app.css, ui/core.js (also index.html)
REF_RE = re.compile(r"(?:ui/[A-Za-z0-9_.\-]+\.(?:js|css))|(?:index\.html)")
# each goal line: starts with a number + '.', contains 'verified:' marker
GOAL_RE = re.compile(r"^\s*(\d+)\.\s+\*\*(?P<title>[^*]+)\*\*", re.M)

def parse_goals(text):
    """Split goal file into per-goal lines, capturing title + any artifact refs."""
    goals = []
    # find all goal start positions
    starts = [(m.start(), int(m.group(1)), m.group("title").strip()) for m in GOAL_RE.finditer(text)]
    for i, (pos, num, title) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        body = text[pos:end]
        verified = "(verified:" in body
        refs = sorted(set(REF_RE.findall(body)))
        goals.append({"num": num, "title": title, "verified_marker": verified, "refs": refs})
    return goals

def main():
    text = GOALS.read_text(encoding="utf-8")
    goals = parse_goals(text)
    now = datetime.datetime.now().isoformat(timespec="seconds")
    missing, checked = [], 0
    for g in goals:
        for ref in g["refs"]:
            p = ROOT / ref
            exists = p.exists() and p.stat().st_size > 0
            checked += 1
            if not exists:
                missing.append({"goal": g["num"], "title": g["title"], "ref": ref})
    ok = not missing
    report = {
        "generated": now,
        "goals_file": str(GOALS.relative_to(ROOT)),
        "goal_count": len(goals),
        "verified_marker_count": sum(1 for g in goals if g["verified_marker"]),
        "artifact_refs_checked": checked,
        "missing_artifacts": missing,
        "all_present": ok,
        "goals": [{"num": g["num"], "title": g["title"], "verified": g["verified_marker"], "refs": g["refs"]} for g in goals],
    }
    out = pathlib.Path(sys.argv[sys.argv.index("--json") + 1]) if "--json" in sys.argv else OUT_DEFAULT
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"checked={checked} missing={len(missing)} all_present={ok}")
    for m in missing:
        print(f"  MISSING goal {m['goal']} ({m['title'][:40]}): {m['ref']}")
    print(f"report -> {out.relative_to(ROOT)}")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())