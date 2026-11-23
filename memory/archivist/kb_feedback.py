#!/usr/bin/env python3
"""archivist/kb_feedback.py - Decision-Knowledge Feedback Loop.

For each cockpit decision later classified REVERTED (or FAILED), trace which
knowledge leaves informed it and mark those leaves as "low-reliability
contributors" with a reliability score in the index.

Sources of decision data:
  - memory/synthesis/decisions.jsonl (decision log)
  - memory/researcher/loop-closure-report.md (FAILED entries)
  - memory/archivist/ingest-decisions.jsonl (if present)

Output: memory/archivist/kb-feedback-<date>.md + .json
Reliability index: memory/archivist/leaf-reliability.json

Usage:
  python memory/archivist/kb_feedback.py [--selftest]
"""
import os, sys, json, re, argparse
from datetime import date, datetime
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent.parent
MEM = ROOT / "memory"
ARCH = MEM / "archivist"
TODAY = date.today()

RELIABILITY_FILE = ARCH / "leaf-reliability.json"


def load_decisions():
    """Load all decisions from available sources."""
    decisions = []
    
    # Source 1: decisions.jsonl
    dj = MEM / "synthesis" / "decisions.jsonl"
    if dj.exists():
        for line in dj.read_text(encoding="utf-8").strip().split("\n"):
            if not line.strip():
                continue
            try:
                d = json.loads(line)
                decisions.append({
                    "source": "decisions.jsonl",
                    "date": d.get("date", ""),
                    "text": d.get("decision", ""),
                    "context": d.get("context", ""),
                    "owner": d.get("owner", ""),
                    "confidence": d.get("confidence", 0.5),
                    "status": d.get("status", "UNKNOWN"),
                })
            except json.JSONDecodeError:
                pass
    
    # Source 2: ingest-decisions.jsonl
    ij = ARCH / "ingest-decisions.jsonl"
    if ij.exists():
        for line in ij.read_text(encoding="utf-8").strip().split("\n"):
            if not line.strip():
                continue
            try:
                d = json.loads(line)
                decisions.append({
                    "source": "ingest-decisions.jsonl",
                    "date": d.get("date", ""),
                    "text": d.get("decision", d.get("text", "")),
                    "context": d.get("context", ""),
                    "owner": d.get("owner", ""),
                    "confidence": d.get("confidence", 0.5),
                    "status": d.get("status", "UNKNOWN"),
                })
            except json.JSONDecodeError:
                pass
    
    return decisions


def find_reverted_or_failed(decisions):
    """Identify decisions that were reverted or had negative outcomes."""
    reverted = []
    for d in decisions:
        text_lower = (d["text"] + " " + d["context"]).lower()
        status = d.get("status", "").upper()
        
        # Explicit REVERTED/FAILED status
        if status in ("REVERTED", "FAILED", "NEGATIVE"):
            reverted.append(d)
            continue
        
        # Heuristic: text contains revert/fail/negative markers
        revert_markers = ["reverted", "revert ", "rolled back", "rollback",
                         "failed", "negative outcome", "rejected", "rescinded"]
        if any(m in text_lower for m in revert_markers):
            d["inferred_status"] = "REVERTED (inferred)"
            reverted.append(d)
    
    return reverted


def extract_cited_leaves(decision):
    """Extract knowledge leaf references from a decision's context."""
    text = decision.get("text", "") + " " + decision.get("context", "")
    # Look for file path references (memory/...)
    refs = re.findall(r"memory/[\w/\-]+\.md", text)
    # Also look for pointer: patterns
    refs += re.findall(r"pointer:\s*([\w/\-]+\.md)", text)
    # Normalize to relative paths
    normalized = set()
    for r in refs:
        if not r.startswith("memory/"):
            r = "memory/" + r
        normalized.add(r.replace("\\", "/"))
    return list(normalized)


def compute_reliability(reverted_decisions):
    """Compute reliability scores for leaves that informed reverted decisions."""
    # Load existing reliability data
    if RELIABILITY_FILE.exists():
        reliability = json.loads(RELIABILITY_FILE.read_text(encoding="utf-8"))
    else:
        reliability = {"leaves": {}, "updated": str(TODAY)}
    
    leaf_map = reliability.get("leaves", {})
    
    # Count how many reverted decisions each leaf informed
    hit_counts = defaultdict(int)
    for d in reverted_decisions:
        leaves = extract_cited_leaves(d)
        if not leaves:
            # Decision with no cited leaves -> flag as uncited
            d["uncited"] = True
        for leaf in leaves:
            hit_counts[leaf] += 1
    
    # Update reliability scores
    for leaf, count in hit_counts.items():
        if leaf not in leaf_map:
            leaf_map[leaf] = {"reliability": 1.0, "revert_hits": 0, "last_hit": str(TODAY)}
        leaf_map[leaf]["revert_hits"] += count
        # Each revert hit reduces reliability by 0.1 (floor at 0.1)
        leaf_map[leaf]["reliability"] = max(0.1, leaf_map[leaf]["reliability"] - 0.1 * count)
        leaf_map[leaf]["last_hit"] = str(TODAY)
    
    reliability["leaves"] = leaf_map
    reliability["updated"] = str(TODAY)
    reliability["total_reverted_decisions"] = len(reverted_decisions)
    reliability["uncited_count"] = sum(1 for d in reverted_decisions if d.get("uncited"))
    
    return reliability


def write_report(reliability, reverted_decisions, output_md, output_json):
    """Write the feedback report."""
    lines = []
    lines.append(f"# Decision-Knowledge Feedback Report {TODAY.isoformat()}")
    lines.append("")
    lines.append(f"## Summary")
    lines.append("")
    lines.append(f"- Total reverted/failed decisions: **{len(reverted_decisions)}**")
    lines.append(f"- Uncited (no traceable leaf): **{reliability.get('uncited_count', 0)}**")
    lines.append(f"- Affected leaves: **{len(reliability.get('leaves', {}))}**")
    lines.append("")
    
    if reverted_decisions:
        lines.append("## Reverted Decisions")
        lines.append("")
        for i, d in enumerate(reverted_decisions[:20], 1):
            status = d.get("inferred_status", d.get("status", "FAILED"))
            leaves = extract_cited_leaves(d)
            leaf_str = ", ".join(leaves[:3]) if leaves else "(uncited)"
            lines.append(f"{i}. [{d.get('date','?')}] {(d.get('decision', d.get('text','')))[:80]}... -> {status}")
            lines.append(f"   Informing leaves: {leaf_str}")
        lines.append("")
    
    lines.append("## Leaf Reliability Scores")
    lines.append("")
    lines.append("| Leaf | Reliability | Revert Hits | Last Hit |")
    lines.append("|---|---|---|---|")
    for leaf, data in sorted(reliability.get("leaves", {}).items(), 
                             key=lambda x: x[1]["reliability"]):
        lines.append(f"| `{leaf}` | {data['reliability']:.2f} | {data['revert_hits']} | {data['last_hit']} |")
    lines.append("")
    
    output_md.write_text("\n".join(lines), encoding="utf-8")
    output_json.write_text(json.dumps(reliability, indent=2), encoding="utf-8")


def run_selftest():
    """Self-test: seed a reverted decision with known citations, verify trace."""
    print("=== KB FEEDBACK SELFTEST ===")
    results = []
    
    test_dir = MEM / "_feedback_test"
    test_dir.mkdir(exist_ok=True)
    
    # Create a test decision file
    test_decision = {
        "date": str(TODAY),
        "decision": "Use host White for model training",
        "context": "Based on memory/researcher/white-specs.md and memory/archivist/freshness-report.md",
        "owner": "Orchestrator",
        "confidence": 0.8,
        "status": "REVERTED"
    }
    
    test_file = test_dir / "test-decisions.jsonl"
    test_file.write_text(json.dumps(test_decision) + "\n", encoding="utf-8")
    
    # Create the cited leaves
    (MEM / "researcher" / "white-specs.md").parent.mkdir(parents=True, exist_ok=True)
    white_specs = MEM / "researcher" / "white-specs.md"
    if not white_specs.exists():
        white_specs.write_text("# White Specs\nVRAM: 24GB\n", encoding="utf-8")
    
    # Test: extract cited leaves
    leaves = extract_cited_leaves(test_decision)
    check1 = "memory/researcher/white-specs.md" in leaves
    results.append(("cited_leaf_extracted", str(leaves), check1))
    
    # Test: reliability score drops
    reverted = [test_decision]
    # Use a temp reliability file
    global RELIABILITY_FILE
    orig_rel = RELIABILITY_FILE
    RELIABILITY_FILE = test_dir / "test-reliability.json"
    if RELIABILITY_FILE.exists():
        RELIABILITY_FILE.unlink(missing_ok=True)
    
    reliability = compute_reliability(reverted)
    leaf_score = reliability["leaves"].get("memory/researcher/white-specs.md", {}).get("reliability", 1.0)
    check2 = leaf_score < 1.0
    results.append(("reliability_dropped", f"score={leaf_score}", check2))
    
    # Test: uncited detection
    uncited_decision = {
        "date": str(TODAY),
        "decision": "Do something without citing anything",
        "context": "",
        "owner": "Test",
        "confidence": 0.5,
        "status": "FAILED"
    }
    reverted2 = [uncited_decision]
    RELIABILITY_FILE.unlink(missing_ok=True)
    reliability2 = compute_reliability(reverted2)
    check3 = reliability2.get("uncited_count", 0) == 1
    results.append(("uncited_detected", f"count={reliability2.get('uncited_count',0)}", check3))
    
    # Test: deterministic (same input -> same output)
    RELIABILITY_FILE.unlink(missing_ok=True)
    r_a = compute_reliability(reverted)
    RELIABILITY_FILE.unlink(missing_ok=True)
    r_b = compute_reliability(reverted)
    check4 = json.dumps(r_a, sort_keys=True) == json.dumps(r_b, sort_keys=True)
    results.append(("deterministic", "two runs identical", check4))
    
    # Test: report generation
    RELIABILITY_FILE.unlink(missing_ok=True)
    reliability3 = compute_reliability(reverted)
    out_md = test_dir / "test-report.md"
    out_json = test_dir / "test-report.json"
    write_report(reliability3, reverted, out_md, out_json)
    check5 = out_md.exists() and out_json.exists()
    results.append(("report_generated", str(out_md), check5))
    
    # Restore
    RELIABILITY_FILE = orig_rel
    
    # Cleanup
    import shutil
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    # Print results
    all_pass = True
    print(f"{'Test':<25} {'Detail':<40} {'Pass'}")
    print("-" * 70)
    for name, detail, passed in results:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"{name:<25} {detail:<40} {status}")
    
    print("=" * 70)
    if all_pass:
        print("SELFTEST PASS")
        return 0
    else:
        print("SELFTEST FAIL")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Decision-Knowledge Feedback Loop")
    parser.add_argument("--selftest", action="store_true", help="Run self-test")
    args = parser.parse_args()
    
    if args.selftest:
        sys.exit(run_selftest())
    
    # Normal run
    decisions = load_decisions()
    reverted = find_reverted_or_failed(decisions)
    reliability = compute_reliability(reverted)
    
    # Save reliability index
    RELIABILITY_FILE.write_text(json.dumps(reliability, indent=2), encoding="utf-8")
    
    # Write report
    out_md = ARCH / f"kb-feedback-{TODAY.isoformat()}.md"
    out_json = ARCH / f"kb-feedback-{TODAY.isoformat()}.json"
    write_report(reliability, reverted, out_md, out_json)
    
    print(f"KB Feedback {TODAY.isoformat()}: {len(decisions)} decisions, "
          f"{len(reverted)} reverted/failed, "
          f"{len(reliability.get('leaves', {}))} affected leaves")
    print(f"Report: {out_md}")


if __name__ == "__main__":
    main()
