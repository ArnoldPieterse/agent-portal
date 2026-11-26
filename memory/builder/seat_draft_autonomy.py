#!/usr/bin/env python3
"""
Builder Goal #7 — Seat-Draft Autonomy Validator v2.
Scores each seat-drafted goal for autonomy-readiness: flags goals that implicitly require a
human ("connect account", "approve", "Arnold to ...", "ask the user", ...), estimates the
removable-touch count, and rejects/annotates drafts that would add a new human gate. Pairs with
the zero-touch closeout so next-cycle goals are born autonomy-clean.

Distinct from seat_draft_validate (quality/feasibility): this adds only the human-gate axis.
Same numbered-goal format as seat_draft_validate: `N. **Title** - text` lines in a .md file.

Usage:
  python memory/builder/seat_draft_autonomy.py <goal.md> [--strict] [--out REPORT.json]
  python memory/builder/seat_draft_autonomy.py --selftest

Default is annotate-only (exit 0) so it is safe to run on live drafts; --strict exits 1 if any
goal is flagged, for use as a closeout gate.
"""
import argparse, json, os, re, sys
from datetime import datetime, timezone

# (label, regex) — each match is one implicit human-gate touchpoint.
GATE_PATTERNS = [
    ("connect-account", r"connect\s+(?:the\s+)?account|account\s+credential"),
    ("ratify-approve",  r"\b(approve|approval|ratif(?:y|ication))\b"),
    ("named-human",     r"\barnold\b"),
    ("ask-human",       r"ask\s+(?:the\s+)?(user|human)|human\s+to\s|user\s+to\s+(?:click|approve|confirm)"),
    ("manual-action",   r"\bmanually\b|by\s+hand|click\s+(?:the\s+)?button|press\s+(?:the\s+)?button"),
    ("notify-human",    r"(send|draft)\s+(?:an?\s+)?email\s+(to\s+)?(?:me|the\s+user)|notify\s+(?:the\s+)?user"),
    ("pending-human",   r"pending\s+(?:human|user|approval)|needs?\s+a?\s?(?:human|user)\s+(?:action|input|touch)"),
]
_COMPILED = [(label, re.compile(rx, re.IGNORECASE)) for label, rx in GATE_PATTERNS]

GOAL_RE = re.compile(r'^(\d+)\.\s+\*\*(.+?)\*\*\s*-\s+(.*)', re.MULTILINE)


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def detect_gates(text):
    """Return list of {label, phrase} for each distinct gate pattern matched in text."""
    hits = []
    for label, rx in _COMPILED:
        m = rx.search(text)
        if m:
            hits.append({"label": label, "phrase": m.group(0).strip()})
    return hits


def score_goal(gates):
    """Autonomy-readiness 0..100 and a clean/flagged verdict. Each distinct gate pattern
    costs 30 points (floor 0). clean iff no gates."""
    n = len(gates)
    return max(0, 100 - 30 * n), ("clean" if n == 0 else "flagged")


def parse_goals(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, encoding="utf-8") as f:
        content = f.read()
    goals = []
    for m in GOAL_RE.finditer(content):
        goals.append({"num": int(m.group(1)), "title": m.group(2), "text": m.group(3)})
    return goals


def validate_file(filepath, agent=None):
    agent = agent or (os.path.basename(filepath)[:-3] if filepath.endswith(".md") else os.path.basename(filepath))
    goals = parse_goals(filepath)
    goal_reports = []
    flagged = []
    total_removable = 0
    for g in goals:
        gates = detect_gates(g["title"] + " \n " + g["text"])
        score, verdict = score_goal(gates)
        removable = len(gates)
        total_removable += removable
        if verdict == "flagged":
            flagged.append(g["num"])
        goal_reports.append({"num": g["num"], "title": g["title"], "readiness": verdict,
                             "autonomy_score": score, "gates": gates,
                             "removable_touch_estimate": removable})
    return {"agent": agent, "file": filepath, "total_goals": len(goals),
            "clean_count": len(goals) - len(flagged), "flagged": flagged,
            "all_clean": not flagged, "estimated_removable_touches": total_removable,
            "goals": goal_reports}


def _selftest():
    import tempfile, shutil
    import pathlib as _pl
    tmp = _pl.Path(tempfile.mkdtemp(prefix="seatdraft_selftest_"))
    failures = []
    try:
        # (1) a draft with one human-gate goal is flagged on the offending line.
        dirty = tmp / "dirty.md"
        dirty.write_text(
            "# Draft\n"
            "1. **Clean Autonomy Goal** - emit through the FSM and log to jsonl automatically.\n"
            "2. **Account Wiring** - connect account to the provider and ask the user to approve.\n",
            encoding="utf-8")
        rep = validate_file(str(dirty))
        if rep["all_clean"]:
            failures.append("dirty draft not flagged as not-all-clean")
        if 2 not in rep["flagged"] or 1 in rep["flagged"]:
            failures.append(f"wrong goals flagged: {rep['flagged']} (want [2])")
        g2 = next(x for x in rep["goals"] if x["num"] == 2)
        labels = {g["label"] for g in g2["gates"]}
        if "connect-account" not in labels or "ratify-approve" not in labels:
            failures.append(f"expected connect-account + ratify-approve gates, got {labels}")
        # (2) a clean draft passes.
        clean = tmp / "clean.md"
        clean.write_text(
            "# Draft\n"
            "1. **Self-Heal Probe** - run the liveness probe and append jsonl with no human step.\n"
            "2. **Contract Lint** - validate live files against the registry and fail on drift.\n",
            encoding="utf-8")
        repc = validate_file(str(clean))
        if not repc["all_clean"] or repc["flagged"]:
            failures.append(f"clean draft wrongly flagged: {repc['flagged']}")
        # (3) score reproducible across runs.
        a = validate_file(str(dirty))
        b = validate_file(str(dirty))
        if json.dumps(a["goals"]) != json.dumps(b["goals"]):
            failures.append("goal scores not reproducible across runs")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if failures:
        print("SELFTEST FAIL")
        for f_ in failures:
            print("  -", f_)
        return 1
    print("SELFTEST PASS: human-gate goal flagged on its line (connect-account + ratify-approve); "
          "clean draft passes; scores reproducible across runs.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Builder seat-draft autonomy validator v2")
    ap.add_argument("file", nargs="?")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any goal flagged")
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return _selftest()
    if not args.file:
        ap.error("goal.md required (or --selftest)")
    rep = validate_file(args.file)
    rep["ts"] = _now()
    print(json.dumps(rep, indent=2))
    if args.out:
        Path_out = os.path.abspath(args.out)
        with open(Path_out, "w", encoding="utf-8") as f:
            json.dump(rep, f, indent=2)
        print(f"[seat_draft_autonomy] report -> {Path_out}")
    return 1 if (args.strict and not rep["all_clean"]) else 0


if __name__ == "__main__":
    sys.exit(main())
