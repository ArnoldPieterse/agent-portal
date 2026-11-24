"""goal_inheritance.py - Cross-Cycle Goal Inheritance Engine.

Detects goals from cycle N that were scoped down (v1 done, v2 pending) and
auto-generates the v2 continuation with inherited context + updated verification.

Usage:
    python memory/orchestrator/goal_inheritance.py          # scan + generate
    python memory/orchestrator/goal_inheritance.py --selftest  # run selftest
"""
import pathlib, json, re, hashlib
from datetime import date, datetime

MEM = pathlib.Path("memory")
ARCHIVE = MEM / "goals" / "archive"
CLOSED_TOPICS = MEM / "goals" / "closed_topics.json"
OUTPUT = MEM / "orchestrator" / "inherited-goals.json"

# Patterns that indicate a goal was scoped down (v1 done, v2 pending)
SCOPE_PATTERNS = [
    r"\bv[1-9]\b.*done.*v[2-9]",       # "v1 done, v2 pending"
    r"scoped?\s+down",                   # explicit "scoped down"
    r"phase\s*[1-3].*complete.*phase\s*[2-4]",  # "phase 1 complete"
    r"remaining.*portion",                # "remaining portion"
    r"partial(ly)?\s+complete",          # "partially complete"
    r"(v|phase|stage)\s*\d+\s+(done|complete|reached).*?(v|phase|stage)\s*\d+",
]

def compute_sig(text: str) -> str:
    """Compute signature for closed_topics dedup."""
    # Match the existing sig format (first 16 hex of sha1)
    return hashlib.sha1(text.lower().strip().encode()).hexdigest()[:16]

def load_closed_sigs() -> set:
    if not CLOSED_TOPICS.exists():
        return set()
    data = json.loads(CLOSED_TOPICS.read_text(encoding="utf-8"))
    sigs = set()
    for entry in data:
        if isinstance(entry, dict):
            sigs.add(entry.get("sig", ""))
            sigs.add(compute_sig(entry.get("text", "")))
        else:
            sigs.add(compute_sig(str(entry)))
    return sigs

def scan_archive_for_scoped_goals() -> list:
    """Scan all archive files for goals with scope-down indicators."""
    scoped = []
    if not ARCHIVE.exists():
        return scoped
    
    for f in sorted(ARCHIVE.glob("*.md")):
        content = f.read_text(encoding="utf-8")
        # Parse numbered goals
        goal_pattern = re.compile(r"^(\d+)\.\s+\*\*(.+?)\*\*\s*-\s+(.+?)(?=\n\n|\n\d+\.|$)", re.MULTILINE | re.DOTALL)
        
        for m in goal_pattern.finditer(content):
            num = int(m.group(1))
            title = m.group(2).strip()
            body = m.group(3).strip()
            
            # Check if this goal was reached
            is_reached = "[REACHED" in body or "✅ REACHED" in body or "(verified:" in body
            
            # Check for scope-down indicators in title + body
            full_text = f"{title} {body}"
            matched_pattern = None
            for pat in SCOPE_PATTERNS:
                if re.search(pat, full_text, re.IGNORECASE):
                    matched_pattern = pat
                    break
            
            if is_reached and matched_pattern:
                scoped.append({
                    "source_file": str(f.relative_to(MEM.parent)),
                    "goal_num": num,
                    "title": title,
                    "body": body[:500],
                    "pattern_matched": matched_pattern,
                    "agent": f.name.split("-")[0],
                })
    
    return scoped

def generate_v2_goal(original: dict) -> dict:
    """Generate a v2 continuation goal from a scoped-down v1."""
    title = original["title"]
    body = original["body"]
    agent = original["agent"]
    
    # Extract version reference or create one
    v_match = re.search(r"\bv(\d+)\b", title + " " + body, re.IGNORECASE)
    if v_match:
        next_v = int(v_match.group(1)) + 1
        v_label = f"v{next_v}"
    else:
        v_label = "v2"
    
    # Build inherited context
    inherited_context = (
        f"Inherited from cycle goal {original['goal_num']} ({original['source_file']}): "
        f"{title}. Prior completion established baseline; this continuation extends scope."
    )
    
    # Updated verification: must be more specific than original
    orig_verified = re.search(r"Verified:\s*(.+?)(?:\n|$)", body)
    if orig_verified:
        base_criteria = orig_verified.group(1).strip()
        new_verification = (
            f"Verified: all v1 criteria still pass (regression: {base_criteria[:200]}) "
            f"+ new v{v_label} scope additions pass independently. "
            f"Inherited context validated against current fleet state."
        )
    else:
        new_verification = (
            f"Verified: v{v_label} deliverable exists and passes its own acceptance test; "
            f"inherited v1 baseline still valid (no regression)."
        )
    
    v2_title = f"{title} ({v_label})"
    v2_body = (
        f"Inherit from: {original['source_file']} goal {original['goal_num']}. "
        f"Context: {inherited_context[:300]}\n"
        f"Scope: Complete the remaining portion beyond v1. "
        f"Update verification to cover full scope, not just the scoped-down subset.\n"
        f"{new_verification}"
    )
    
    return {
        "agent": agent,
        "title": v2_title,
        "body": v2_body,
        "source": original["source_file"],
        "inherited_from_goal": original["goal_num"],
        "generated": date.today().isoformat(),
    }

def validate_not_duplicate(goal: dict, closed_sigs: set) -> bool:
    """Check goal is not already in closed_topics."""
    text = f"**{goal['title']}** - {goal['body']}"
    sig = compute_sig(text)
    if sig in closed_sigs:
        return False
    # Also check title-level dedup (looser)
    for entry_sig, entry_text in _closed_texts(closed_sigs):
        if goal["title"].lower()[:40] in entry_text.lower():
            return False
    return True

def _closed_texts(sigs: set):
    """Yield (sig, text) pairs from closed topics."""
    if not CLOSED_TOPICS.exists():
        return
    data = json.loads(CLOSED_TOPICS.read_text(encoding="utf-8"))
    for entry in data:
        if isinstance(entry, dict):
            yield entry.get("sig", ""), entry.get("text", "")

def selftest():
    """Run 3 synthetic inheritance cases and validate."""
    print("=== goal_inheritance.py SELFTEST ===")
    
    # Create 3 synthetic scoped-down goals
    test_cases = [
        {
            "source_file": "goals/archive/test-cycle1.md",
            "goal_num": 1,
            "title": "Knowledge Graph v1 (Core Edges)",
            "body": "Build core edge types. Verified: 3 edge types work. v2 pending: temporal edges + typed relations.",
            "pattern_matched": r"v[1-9].*done.*v[2-9]",
            "agent": "archivist",
        },
        {
            "source_file": "goals/archive/test-cycle2.md",
            "goal_num": 3,
            "title": "Fleet Health Dashboard Phase 1",
            "body": "Phase 1 complete: basic status cards. Remaining portion: trend charts + alerting. Verified: cards render.",
            "pattern_matched": r"phase\s*[1-3].*complete.*phase\s*[2-4]",
            "agent": "designer",
        },
        {
            "source_file": "goals/archive/test-cycle3.md",
            "goal_num": 5,
            "title": "Auto-Priority Engine (scoped down: ranking only)",
            "body": "Partially complete - ranking works but dispatch integration pending. Verified: ranking scores correct.",
            "pattern_matched": r"partial(ly)?\s+complete",
            "agent": "builder",
        },
    ]
    
    closed_sigs = load_closed_sigs()
    print(f"  Loaded {len(closed_sigs)} closed topic signatures")
    
    all_valid = True
    for i, case in enumerate(test_cases, 1):
        v2 = generate_v2_goal(case)
        
        # Validate structure
        has_title = bool(v2["title"])
        has_body = len(v2["body"]) > 50
        has_verification = "Verified:" in v2["body"]
        has_inheritance = "Inherited from" in v2["body"] or "Inherit from" in v2["body"]
        agent_valid = v2["agent"] in ("archivist", "designer", "builder", "orchestrator", 
                                       "researcher", "verifier", "mechanic", "scribe")
        
        # Validate not duplicate
        is_new = validate_not_duplicate(v2, closed_sigs)
        
        checks = {
            "has_title": has_title,
            "has_body": has_body,
            "has_verification": has_verification,
            "has_inheritance_context": has_inheritance,
            "agent_valid": agent_valid,
            "not_duplicate": is_new,
        }
        
        passed = all(checks.values())
        status = "PASS" if passed else "FAIL"
        print(f"  Case {i} [{case['title'][:40]}]: {status}")
        if not passed:
            failed = [k for k, v in checks.items() if not v]
            print(f"    Failed: {failed}")
            all_valid = False
    
    print(f"\n  Result: {'ALL PASS' if all_valid else 'SOME FAILED'} ({sum(1 for _ in test_cases)}/3 cases)")
    
    # Also run live scan
    scoped = scan_archive_for_scoped_goals()
    print(f"  Live scan: {len(scoped)} scoped-down goals found in archive")
    
    if all_valid:
        print("  SELFTEST: PASS")
        return True
    else:
        print("  SELFTEST: FAIL")
        return False

def main():
    import sys
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    
    # Normal mode: scan + generate
    scoped = scan_archive_for_scoped_goals()
    closed_sigs = load_closed_sigs()
    
    inherited = []
    for s in scoped:
        v2 = generate_v2_goal(s)
        if validate_not_duplicate(v2, closed_sigs):
            inherited.append(v2)
    
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(inherited, indent=2), encoding="utf-8")
    print(f"Scanned archive: {len(scoped)} scoped-down goals found")
    print(f"Generated {len(inherited)} valid v2 goals -> {OUTPUT}")

if __name__ == "__main__":
    main()
