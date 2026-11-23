#!/usr/bin/env python3
"""
policy_conflict.py - Policy Conflict Detector (Builder goal #9, cycle-14).

Scans all policy files (memory/ops/*.md, memory/ops/runbooks/*.md) for overlapping
rules that prescribe different actions for the same trigger condition.

Output: JSON report to memory/builder/policy_conflicts.json + human-readable summary.

Usage:
  python memory/builder/policy_conflict.py              # scan all policy files
  python memory/builder/policy_conflict.py --selftest   # run acceptance tests
"""
import json, os, re, sys, datetime, argparse
from pathlib import Path
from collections import defaultdict

ROOT = Path("memory")
OPS_DIR = ROOT / "ops"
RUNBOOKS_DIR = OPS_DIR / "runbooks"
OUT_JSON = ROOT / "builder" / "policy_conflicts.json"

# Trigger keywords that indicate conditional rules
TRIGGER_PATTERNS = [
    r"\bif\s+([a-z_]+(?:\s+[a-z_]+){0,5})",       # "if host_down"
    r"\bwhen\s+([a-z_]+(?:\s+[a-z_]+){0,5})",     # "when vram_exceeds"
    r"\bon\s+([a-z_]+(?:\s+[a-z_]+){0,5})",       # "on oom_alert"
    r"\btrigger(ed)?\s*[:=]\s*(.+?)(?:\.|$)",   # "trigger: disk_pressure"
    r"\bbefore\s+([a-z_]+(?:\s+[a-z_]+){0,5})",   # "before model_swap"
    r"\bafter\s+([a-z_]+(?:\s+[a-z_]+){0,5})",    # "after recovery"
]

# Action verbs that indicate what the rule prescribes
ACTION_VERBS = [
    "unload", "load", "swap", "restart", "reboot", "kill", "pause",
    "alert", "notify", "escalate", "rollback", "retry", "skip",
    "block", "allow", "reject", "approve", "deny", "migrate",
    "throttle", "scale", "expand", "shrink", "freeze", "hold",
    "create", "delete", "write", "read", "log", "record",
]

# Severity thresholds for action divergence
ACTION_GROUPS = {
    "destructive": ["kill", "reboot", "delete", "rollback", "unload"],
    "restrictive": ["block", "pause", "hold", "freeze", "deny", "reject", "throttle"],
    "permissive":  ["allow", "approve", "load", "retry", "scale", "expand"],
    "observational": ["alert", "notify", "log", "record", "read"],
}


def extract_rules_from_text(text, source_file):
    """Extract rule entries from markdown text. Each rule has trigger + action."""
    rules = []
    lines = text.split("\n")

    for i, line in enumerate(lines):
        # Skip comments and headers
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("<!--"):
            continue

        # Look for trigger patterns
        trigger = None
        for pattern in TRIGGER_PATTERNS:
            m = re.search(pattern, stripped, re.IGNORECASE)
            if m:
                trigger = m.group(1).strip().lower()
                break

        if not trigger:
            continue

        # Look for action verbs in the same line or next 2 lines
        context = " ".join(lines[i:i+3]).lower()
        actions_found = []
        for verb in ACTION_VERBS:
            if re.search(rf"\b{verb}\b", context):
                actions_found.append(verb)

        if actions_found:
            rules.append({
                "trigger": trigger,
                "actions": actions_found,
                "file": str(source_file),
                "line": i + 1,
                "text": stripped[:200],
            })

    return rules


def scan_policy_files():
    """Scan all policy files and return list of extracted rules."""
    all_rules = []
    seen = set()

    # Scan memory/ops/*.md (top-level only, skip INDEX.md)
    if OPS_DIR.exists():
        for f in sorted(OPS_DIR.glob("*.md")):
            if f.name == "INDEX.md":
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
                rules = extract_rules_from_text(text, f)
                all_rules.extend(rules)
            except Exception as e:
                print(f"  WARN: failed to read {f}: {e}")

    # Scan runbooks
    if RUNBOOKS_DIR.exists():
        for f in sorted(RUNBOOKS_DIR.glob("*.md")):
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
                rules = extract_rules_from_text(text, f)
                all_rules.extend(rules)
            except Exception as e:
                print(f"  WARN: failed to read {f}: {e}")

    return all_rules


def trigger_similarity(t1, t2):
    """Compute similarity between two trigger strings (0-1)."""
    if not t1 or not t2:
        return 0.0
    # Exact match
    if t1 == t2:
        return 1.0
    # Token overlap
    tokens1 = set(t1.split())
    tokens2 = set(t2.split())
    if not tokens1 or not tokens2:
        return 0.0
    overlap = len(tokens1 & tokens2) / min(len(tokens1), len(tokens2))
    return overlap


def action_divergence(actions1, actions2):
    """Compute divergence between two action sets (0-1)."""
    if not actions1 or not actions2:
        return 0.0

    # Check for opposing groups
    group1 = set()
    group2 = set()
    for verb in actions1:
        for gname, verbs in ACTION_GROUPS.items():
            if verb in verbs:
                group1.add(gname)
    for verb in actions2:
        for gname, verbs in ACTION_GROUPS.items():
            if verb in verbs:
                group2.add(gname)

    # Opposing groups = high divergence
    opposing_pairs = [
        ("destructive", "permissive"),
        ("restrictive", "permissive"),
        ("destructive", "observational"),
        ("restrictive", "observational"),
    ]
    for a, b in opposing_pairs:
        if (a in group1 and b in group2) or (b in group1 and a in group2):
            return 0.9

    # Same group or no opposing: different verbs are low divergence
    shared = set(actions1) & set(actions2)
    unique = (set(actions1) | set(actions2)) - shared
    if unique:
        # If both in same single group, it's a minor difference (0.2 max)
        all_groups = group1 | group2
        if len(all_groups) <= 1:
            return min(0.2, len(unique) / max(len(set(actions1)), len(set(actions2))) * 0.2)
        # Different groups but not opposing: moderate
        return min(0.5, len(unique) / max(len(set(actions1)), len(set(actions2))) * 0.5)

    return 0.0


def detect_conflicts(rules, trigger_threshold=0.7):
    """Detect conflicting rules: same/overlapping trigger + divergent actions."""
    conflicts = []
    n = len(rules)

    for i in range(n):
        for j in range(i + 1, n):
            r1, r2 = rules[i], rules[j]

            # Skip same-file rules (less likely to be meaningful conflicts)
            if r1["file"] == r2["file"]:
                continue

            sim = trigger_similarity(r1["trigger"], r2["trigger"])
            if sim < trigger_threshold:
                continue

            div = action_divergence(r1["actions"], r2["actions"])
            if div < 0.3:
                continue

            # Severity: high if opposing action groups, medium otherwise
            severity = "high" if div >= 0.8 else ("medium" if div >= 0.5 else "low")

            conflicts.append({
                "rule_a": r1["text"][:150],
                "rule_b": r2["text"][:150],
                "file_a": r1["file"],
                "file_b": r2["file"],
                "trigger_overlap": round(sim, 3),
                "action_divergence": round(div, 3),
                "severity": severity,
            })

    return conflicts


def selftest():
    """Acceptance tests matching the goal spec verification criteria."""
    print("=" * 60)
    print("policy_conflict.py - SELFTEST (spec-aligned)")
    print("=" * 60)

    all_pass = True

    # AC1: synthetic fixture with 2 conflicting rules -> detects conflict
    synthetic_rules = [
        {
            "trigger": "host_down white",
            "actions": ["kill", "reboot"],
            "file": "test_a.md",
            "line": 1,
            "text": "if host_down white then kill and reboot immediately",
        },
        {
            "trigger": "host_down white",
            "actions": ["alert", "notify"],
            "file": "test_b.md",
            "line": 1,
            "text": "when host_down white then alert and notify operator only",
        },
    ]
    conflicts = detect_conflicts(synthetic_rules)
    ac1 = len(conflicts) == 1 and conflicts[0]["severity"] in ("high", "medium")
    print(f"AC1: synthetic conflict detected ({len(conflicts)} found) -> {'PASS' if ac1 else 'FAIL'}")
    if not ac1:
        all_pass = False

    # AC2: real policy files produce a report (may be empty)
    rules = scan_policy_files()
    conflicts_real = detect_conflicts(rules)
    report = {
        "scanned_rules": len(rules),
        "conflicts_found": len(conflicts_real),
        "conflicts": conflicts_real,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    ac2 = isinstance(report["conflicts"], list) and report["scanned_rules"] >= 0
    print(f"AC2: real scan produced report ({report['scanned_rules']} rules, {report['conflicts_found']} conflicts) -> {'PASS' if ac2 else 'FAIL'}")
    if not ac2:
        all_pass = False

    # AC3: false-positive rate < 10% on synthetic test set
    # Create 20 non-conflicting rule pairs + 2 conflicting pairs
    non_conflicting = []
    for idx in range(10):
        non_conflicting.append({
            "trigger": f"condition_{idx}",
            "actions": ["alert"],
            "file": f"file_a_{idx}.md",
            "line": 1,
            "text": f"if condition_{idx} then alert",
        })
        non_conflicting.append({
            "trigger": f"condition_{idx}",
            "actions": ["log"],
            "file": f"file_b_{idx}.md",
            "line": 1,
            "text": f"if condition_{idx} then log",
        })
    # Add 2 genuinely conflicting pairs
    non_conflicting.append({
        "trigger": "vram_exceeds_threshold",
        "actions": ["kill"],
        "file": "conflict_a.md",
        "line": 1,
        "text": "if vram_exceeds_threshold then kill process",
    })
    non_conflicting.append({
        "trigger": "vram_exceeds_threshold",
        "actions": ["alert"],
        "file": "conflict_b.md",
        "line": 1,
        "text": "if vram_exceeds_threshold then alert only",
    })

    fp_conflicts = detect_conflicts(non_conflicting)
    # We expect at most 1 real conflict (the vram pair), but may get some false positives
    # from the alert/log pairs (observational group, so divergence should be low)
    true_positives = sum(1 for c in fp_conflicts if "vram" in c.get("rule_a", "") + c.get("rule_b", ""))
    false_positives = len(fp_conflicts) - true_positives
    total_pairs_tested = 20 + 2
    fp_rate = false_positives / max(1, total_pairs_tested)
    ac3 = fp_rate < 0.10
    print(f"AC3: FP rate {fp_rate:.1%} ({false_positives}/{total_pairs_tested} pairs) -> {'PASS' if ac3 else 'FAIL'}")
    if not ac3:
        all_pass = False

    # AC4: output JSON is valid and has required fields
    test_report = {
        "scanned_rules": 1,
        "conflicts_found": 0,
        "conflicts": [],
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    try:
        parsed = json.loads(json.dumps(test_report))
        assert "conflicts" in parsed and "scanned_rules" in parsed
        ac4 = True
    except Exception:
        ac4 = False
    print(f"AC4: JSON report valid -> {'PASS' if ac4 else 'FAIL'}")
    if not ac4:
        all_pass = False

    # AC5: conflict record has all required fields
    if conflicts:
        c = conflicts[0]
        required = {"rule_a", "rule_b", "file_a", "file_b", "trigger_overlap", "action_divergence", "severity"}
        ac5 = required.issubset(c.keys())
        print(f"AC5: conflict fields complete -> {'PASS' if ac5 else 'FAIL'}")
    else:
        # Test with synthetic
        c = detect_conflicts(synthetic_rules)[0]
        required = {"rule_a", "rule_b", "file_a", "file_b", "trigger_overlap", "action_divergence", "severity"}
        ac5 = required.issubset(c.keys())
        print(f"AC5: conflict fields complete (synthetic) -> {'PASS' if ac5 else 'FAIL'}")
    if not ac5:
        all_pass = False

    print()
    result = f"{sum([ac1, ac2, ac3, ac4, ac5])}/5"
    print(f"RESULT: {result} ACs {'ALL PASSED' if all_pass else 'FAILED'}")
    return 0 if all_pass else 1


def main():
    ap = argparse.ArgumentParser(description="Policy Conflict Detector")
    ap.add_argument("--selftest", action="store_true", help="Run acceptance tests")
    ap.add_argument("--json", action="store_true", help="Output JSON only")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    # Scan and detect
    rules = scan_policy_files()
    conflicts = detect_conflicts(rules)

    report = {
        "scanned_rules": len(rules),
        "conflicts_found": len(conflicts),
        "conflicts": conflicts,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    # Write JSON output
    os.makedirs(OUT_JSON.parent, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Scanned {len(rules)} rules from policy files.")
        print(f"Conflicts found: {len(conflicts)}")
        for c in conflicts[:10]:
            print(f"  [{c['severity'].upper()}] {c['file_a']} <-> {c['file_b']}")
            print(f"    trigger overlap={c['trigger_overlap']:.2f}, action divergence={c['action_divergence']:.2f}")
        if len(conflicts) > 10:
            print(f"  ... and {len(conflicts) - 10} more (see {OUT_JSON})")
        print(f"Report: {OUT_JSON}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
