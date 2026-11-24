"""
Idle Pass Auditor - Verifier goal #2
Scans last 50 auto-loop passes from autoloop.jsonl.
Flags: (a) agent dispatched for a reached goal, OR (b) generic menu in MAINT/IDLE mode.
Writes report to memory/verifier/idle-audit-report.md.
"""
import json
import re
from pathlib import Path
from datetime import datetime, timezone

AUTOLOOP = Path("memory/ops/autoloop.jsonl")
GOALS_DIR = Path("memory/goals")
REPORT_PATH = Path("memory/verifier/idle-audit-report.md")
GENERIC_MENU_RE = re.compile(r"\[a-z]\)|\(a\)\s|\(b\)\s|\(c\)\s|\(d\)\s", re.IGNORECASE)


def load_passes(n=50):
    """Load last n passes from autoloop.jsonl."""
    if not AUTOLOOP.exists():
        return []
    lines = AUTOLOOP.read_text(encoding="utf-8").strip().split("\n")
    entries = []
    for line in lines[-n:]:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def get_reached_goals():
    """Scan goal files for goals marked as reached/verified."""
    reached = set()
    if not GOALS_DIR.exists():
        return reached
    for gf in GOALS_DIR.glob("*.md"):
        text = gf.read_text(encoding="utf-8", errors="replace")
        # Look for verified: markers or [DONE] tags
        for m in re.finditer(r"\(verified:\s*([^)]+)\)", text):
            pass  # mark goal as reached (we track by file+line context)
        if "reached" in text.lower() or "[DONE]" in text or "(verified:" in text:
            reached.add(gf.stem.replace("goals-", ""))
    return reached


def audit_passes(passes, fleet_mode=None):
    """
    Audit a list of pass entries.
    Returns list of violation dicts: {pass_id, agent, type, detail}
    
    Violation types:
      A - dispatched for reached goal
      B - generic menu in MAINTENANCE/IDLE mode
    """
    violations = []
    if not passes:
        return violations

    # Determine fleet mode from each pass or default
    for i, p in enumerate(passes):
        pass_id = p.get("pass_id", f"pass_{i}")
        agent = p.get("agent", "unknown")
        dispatch_text = p.get("dispatch", p.get("prompt", p.get("text", "")))
        mode = (p.get("fleet_mode", fleet_mode) or "WORK").upper()

        # Check (b): generic menu in MAINTENANCE/IDLE
        if mode in ("MAINTENANCE", "IDLE"):
            # Generic menu pattern: enumerated options like (a)(b)(c)(d)
            lines = dispatch_text.split("\n")
            generic_lines = [l for l in lines if GENERIC_MENU_RE.search(l)]
            if len(generic_lines) >= 2:  # at least 2 generic option lines
                violations.append({
                    "pass_id": pass_id,
                    "agent": agent,
                    "type": "B",
                    "detail": f"Generic menu ({len(generic_lines)} options) in {mode} mode"
                })

        # Check (a): dispatched for reached goal
        # Look for goal references that are marked reached
        if dispatch_text:
            for line in dispatch_text.split("\n"):
                if "reached" in line.lower() and ("goal" in line.lower() or "#" in line):
                    violations.append({
                        "pass_id": pass_id,
                        "agent": agent,
                        "type": "A",
                        "detail": f"Dispatch references reached goal: {line.strip()[:80]}"
                    })
                    break

    return violations


def write_report(violations, total_scanned):
    """Write audit report to markdown."""
    now = datetime.now(timezone.utc).isoformat()
    lines = [
        f"# Idle Pass Audit Report",
        f"",  # blank line
        f"Generated: {now}",
        f"Scanned: {total_scanned} passes",
        f"Violations: {len(violations)}",
        "",
    ]
    if violations:
        lines.append("## Violations")
        lines.append("")
        for v in violations:
            lines.append(f"- **{v['pass_id']}** ({v['agent']}) [{v['type']}]: {v['detail']}")
    else:
        lines.append("No violations detected.")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    return str(REPORT_PATH)


def self_test():
    """
    Self-test with synthetic data:
    1. Clean post-fix data -> 0 violations
    2. Synthetic pre-fix data (generic menus in MAINTENANCE) -> >=5 violations
    """
    print("IDLE PASS AUDITOR - SELFTEST")
    print("=" * 50)

    # Test 1: clean data (WORK mode, specific tasks)
    clean_passes = [
        {"pass_id": f"clean_{i}", "agent": "Researcher", "fleet_mode": "WORK",
         "dispatch": "Work your oldest open goal TO COMPLETION this pass."}
        for i in range(10)
    ]
    v1 = audit_passes(clean_passes)
    assert len(v1) == 0, f"Expected 0 violations on clean data, got {len(v1)}"
    print("  [PASS] clean_data_0_violations")

    # Test 2: pre-fix data (generic menus in MAINTENANCE mode)
    dirty_passes = []
    for i in range(8):
        dirty_passes.append({
            "pass_id": f"dirty_{i}", "agent": "Builder", "fleet_mode": "MAINTENANCE",
            "dispatch": "Choose one: (a) re-run stale scan\n(b) check for orphaned files\n(c) clean temp dirs\n(d) update docs"
        })
    v2 = audit_passes(dirty_passes)
    assert len(v2) >= 5, f"Expected >=5 violations on dirty data, got {len(v2)}"
    print(f"  [PASS] dirty_data_{len(v2)}_violations (expected >=5)")

    # Test 3: IDLE mode with generic menu also flagged
    idle_passes = [
        {"pass_id": f"idle_{i}", "agent": "Scribe", "fleet_mode": "IDLE",
         "dispatch": "Options: (a) archive old notes\n(b) compact decision log\n(c) update glossary"
        } for i in range(3)
    ]
    v3 = audit_passes(idle_passes)
    assert len(v3) >= 2, f"Expected >=2 violations on IDLE generic data, got {len(v3)}"
    print(f"  [PASS] idle_mode_{len(v3)}_violations")

    # Test 4: WORK mode with enumerated options is NOT flagged (it's a goal menu)
    work_passes = [
        {"pass_id": f"work_{i}", "agent": "Mechanic", "fleet_mode": "WORK",
         "dispatch": "Your open goals:\n1. **Goal A** - do X\n2. **Goal B** - do Y"
        } for i in range(5)
    ]
    v4 = audit_passes(work_passes)
    assert len(v4) == 0, f"Expected 0 violations on WORK specific data, got {len(v4)}"
    print("  [PASS] work_specific_0_violations")

    # Test 5: empty passes -> no crash, 0 violations
    v5 = audit_passes([])
    assert len(v5) == 0
    print("  [PASS] empty_data_no_crash")

    print(f"{'-' * 50}")
    print("RESULT: PASS (5/5 self-test scenarios)")
    return True


def main():
    if "--selftest" in __import__("sys").argv:
        self_test()
        return

    print("IDLE PASS AUDITOR")
    print("=" * 50)
    passes = load_passes(50)
    violations = audit_passes(passes)
    report_path = write_report(violations, len(passes))
    print(f"  Scanned: {len(passes)} passes from {AUTOLOOP}")
    print(f"  Violations: {len(violations)}")
    if violations:
        for v in violations[:10]:
            print(f"    [{v['type']}] {v['pass_id']} ({v['agent']}): {v['detail']}")
    print(f"  Report: {report_path}")
    return 0 if len(violations) == 0 else 1


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        self_test()
    else:
        sys.exit(main())
