#!/usr/bin/env python3
"""ratification_audit.py - Log every human touch in the cycle lifecycle; compute removal plan.

A "human touch" is any point where a human actively intervened in the cycle lifecycle:
  - goal-set trigger (user directive to open/redirect a round)
  - ratification (user explicitly approves a proposed set)
  - unblock (user removes a blocker that agents couldn't self-resolve)
  - redirect (user changes course mid-cycle)

Output: memory/ops/human-touches.jsonl (append-only) + removal plan.
Target: <1 touch/cycle.

Usage:
    python memory/orchestrator/ratification_audit.py            # scan + write
    python memory/orchestrator/ratification_audit.py --selftest # verify with synthetic data
"""
import pathlib, json, re, sys
from datetime import datetime, timezone

MEM = pathlib.Path("memory")
TODO_FILE = MEM.parent / "TODO.md"  # root TODO.md
GOALS_DIR = MEM / "goals"
OUTPUT_FILE = MEM / "ops" / "human-touches.jsonl"
PLAN_FILE = MEM / "orchestrator" / "ratification-removal-plan.json"

# Patterns that indicate a human touch in TODO.md or goals files
HUMAN_TOUCH_PATTERNS = [
    ("goal_set_trigger", re.compile(r"user\s+directive|User\s+ask|human\s+directive", re.IGNORECASE)),
    ("ratification", re.compile(r"pending\s+(seat\s+)?ratification|awaiting\s+(seat\s+)?ratification", re.IGNORECASE)),
    ("unblock", re.compile(r"NEEDS-HUMAN|needs\s+human|blocked\s+pending\s+human", re.IGNORECASE)),
    ("redirect", re.compile(r"user\s+(changed|redirected|overrode)|human\s+override", re.IGNORECASE)),
]

# Removal plan: which automation eliminates each touch type
REMOVAL_PLAN = {
    "goal_set_trigger": {
        "automation": "auto_chair.py (G5) - autonomous round-chair protocol detects 100%/PLATEAU and opens next cycle without human trigger",
        "status": "BUILT (memory/orchestrator/auto_chair.py)",
    },
    "ratification": {
        "automation": "auto_chair.py emits single ratification request; convergence_asymptote.py provides the PLATEAU signal that makes ratification a formality",
        "status": "BUILT (memory/orchestrator/auto_chair.py + convergence_asymptote.py)",
    },
    "unblock": {
        "automation": "convergence_sentinel.py auto-opens remediation goals; idle_rebalance.py flips stuck seats; mechanic OOM recovery loop handles infra unblocks",
        "status": "BUILT (memory/orchestrator/convergence_sentinel.py + idle_rebalance.py)",
    },
    "redirect": {
        "automation": "convergence_coupling.py identifies highest-leverage lane; dispatch_audit ensures no stale dispatches; topic_scorer proposes alternatives",
        "status": "PARTIAL (memory/orchestrator/convergence_coupling.py + dispatch_audit.py)",
    },
}


def scan_human_touches(todo_file: pathlib.Path, goals_dir: pathlib.Path) -> list[dict]:
    """Scan TODO.md and goals files for human touch markers. Returns list of touch records."""
    touches = []
    now = datetime.now(timezone.utc).isoformat()

    # Scan TODO.md
    if todo_file.exists():
        content = todo_file.read_text(encoding="utf-8")
        # Split into sections by ## headers
        sections = re.split(r"(?m)^## ", content)
        for section in sections[1:]:  # skip preamble before first ##
            header = section.split("\n")[0].strip()
            ts_match = re.search(r"(\d{4}-\d{2}-\d{2})", header)
            section_date = ts_match.group(1) if ts_match else "unknown"

            for touch_type, pattern in HUMAN_TOUCH_PATTERNS:
                matches = pattern.findall(section)
                if matches:
                    touches.append({
                        "ts": now,
                        "cycle": section_date,
                        "type": touch_type,
                        "source": "TODO.md",
                        "section": header[:100],
                        "match": matches[0][:80],
                    })

    # Scan goals files for ratification markers
    if goals_dir.exists():
        for gf in sorted(goals_dir.glob("*.md")):
            lane = gf.stem
            content = gf.read_text(encoding="utf-8")
            for touch_type, pattern in HUMAN_TOUCH_PATTERNS:
                matches = list(pattern.finditer(content))
                for m in matches:
                    touches.append({
                        "ts": now,
                        "cycle": "current",
                        "type": touch_type,
                        "source": f"goals/{lane}.md",
                        "section": lane,
                        "match": m.group(0)[:80],
                    })

    return touches


def compute_trend(touches: list[dict]) -> dict:
    """Group touches by cycle and compute touches/cycle."""
    cycles = {}
    for t in touches:
        cyc = t["cycle"]
        if cyc not in cycles:
            cycles[cyc] = []
        cycles[cyc].append(t)

    trend = []
    for cyc in sorted(cycles.keys()):
        trend.append({"cycle": cyc, "touches": len(cycles[cyc]), "types": [t["type"] for t in cycles[cyc]]})

    total_cycles = len(trend)
    total_touches = len(touches)
    avg = total_touches / total_cycles if total_cycles > 0 else 0

    return {
        "cycles_analyzed": total_cycles,
        "total_touches": total_touches,
        "avg_touches_per_cycle": round(avg, 2),
        "target": 1.0,
        "meets_target": avg < 1.0,
        "trend": trend,
    }


def build_removal_plan(touches: list[dict]) -> dict:
    """Build a per-touch-type removal plan with named automations."""
    types_seen = set(t["type"] for t in touches)
    plan = {}
    for ttype in sorted(types_seen):
        plan[ttype] = {
            "count": sum(1 for t in touches if t["type"] == ttype),
            **REMOVAL_PLAN.get(ttype, {"automation": "UNASSIGNED - needs new automation", "status": "GAP"}),
        }
    return plan


def is_already_logged(output_file: pathlib.Path, touches: list[dict]) -> bool:
    """Check if these exact touches are already in the log (append-only idempotency)."""
    if not output_file.exists():
        return False
    existing = set()
    for line in output_file.read_text(encoding="utf-8").strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            key = f"{rec.get('cycle','')}|{rec.get('type','')}|{rec.get('source','')}"
            existing.add(key)
        except (json.JSONDecodeError, KeyError):
            continue
    new_keys = {f"{t['cycle']}|{t['type']}|{t['source']}" for t in touches}
    return new_keys <= existing  # all already present


def run(todo_file=None, goals_dir=None, output_file=None, plan_file=None) -> dict:
    """Main entry."""
    tf = todo_file or TODO_FILE
    gd = goals_dir or GOALS_DIR
    of = output_file or OUTPUT_FILE
    pf = plan_file or PLAN_FILE

    touches = scan_human_touches(tf, gd)
    trend = compute_trend(touches)
    plan = build_removal_plan(touches)

    # Append-only write: only write new touches
    if not is_already_logged(of, touches):
        of.parent.mkdir(parents=True, exist_ok=True)
        with of.open("a", encoding="utf-8") as f:
            for t in touches:
                f.write(json.dumps(t) + "\n")

    # Write removal plan (overwrite - it's a snapshot)
    pf.parent.mkdir(parents=True, exist_ok=True)
    plan_output = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "trend": trend,
        "removal_plan": plan,
        "target_touches_per_cycle": 1.0,
        "meets_target": trend["meets_target"],
    }
    pf.write_text(json.dumps(plan_output, indent=2), encoding="utf-8")

    return {"status": "ok", **trend, "plan_file": str(pf)}


# ─── SELF-TEST ───────────────────────────────────────────────────────────────────

def selftest():
    import tempfile
    results = []

    # --- Test 1: 2 seeded cycles with known touch counts -> correct trend ---
    with tempfile.TemporaryDirectory() as tmp:
        tf = pathlib.Path(tmp) / "TODO.md"
        gd = pathlib.Path(tmp) / "goals"
        of = pathlib.Path(tmp) / "human-touches.jsonl"
        pf = pathlib.Path(tmp) / "plan.json"
        gd.mkdir()

        # Cycle A: 2 touches (1 user directive + 1 ratification)
        # Cycle B: 1 touch (1 unblock)
        tf.write_text(
            "## CYCLE A WORK - user directive 2026-11-20\n"
            "Some work here.\n\n"
            "## CYCLE B WORK - pending ratification 2026-11-23\n"
            "More work. NEEDS-HUMAN for deploy approval.\n",
            encoding="utf-8"
        )
        (gd / "testlane.md").write_text("# Test Lane Goals\nNo human markers here.\n", encoding="utf-8")

        result = run(tf, gd, of, pf)
        assert result["status"] == "ok", f"T1: expected ok, got {result['status']}"
        # Cycle A has 1 touch (user directive), Cycle B has 2 touches (ratification + NEEDS-HUMAN)
        # Wait - let me recount: CYCLE A section matches "user directive" = 1 touch
        # CYCLE B section matches "pending ratification" AND "NEEDS-HUMAN" = 2 touches
        # Total = 3 touches across 2 cycles
        assert result["total_touches"] == 3, f"T1: expected 3 touches, got {result['total_touches']}"
        assert result["cycles_analyzed"] == 2, f"T1: expected 2 cycles, got {result['cycles_analyzed']}"

        # Verify removal plan has named automations for each type
        plan_data = json.loads(pf.read_text(encoding="utf-8"))
        rp = plan_data["removal_plan"]
        assert "goal_set_trigger" in rp, f"T1: missing goal_set_trigger in plan"
        assert "ratification" in rp, f"T1: missing ratification in plan"
        assert "unblock" in rp, f"T1: missing unblock in plan"
        for ttype, entry in rp.items():
            assert entry["automation"] and entry["automation"] != "UNASSIGNED - needs new automation", \
                f"T1: {ttype} has no named automation"

        results.append(("T1: 2 seeded cycles -> correct touch counts + removal plan with named automations", "PASS"))

    # --- Test 2: Re-run is append-only (no duplicates) ---
    with tempfile.TemporaryDirectory() as tmp:
        tf = pathlib.Path(tmp) / "TODO.md"
        gd = pathlib.Path(tmp) / "goals"
        of = pathlib.Path(tmp) / "human-touches.jsonl"
        pf = pathlib.Path(tmp) / "plan.json"
        gd.mkdir()

        tf.write_text("## CYCLE X - user directive 2026-11-25\nWork.\n", encoding="utf-8")
        (gd / "lane.md").write_text("# Lane\nClean.\n", encoding="utf-8")

        # First run
        run(tf, gd, of, pf)
        count_after_first = len(of.read_text(encoding="utf-8").strip().split("\n"))

        # Second run (same data)
        result2 = run(tf, gd, of, pf)
        count_after_second = len(of.read_text(encoding="utf-8").strip().split("\n"))

        assert count_after_first == count_after_second, \
            f"T2: expected append-only (no dup), first={count_after_first} second={count_after_second}"

        results.append(("T2: re-run is append-only (no duplicates)", "PASS"))

    # --- Test 3: Clean cycle (0 touches) -> trend shows 0, meets target ---
    with tempfile.TemporaryDirectory() as tmp:
        tf = pathlib.Path(tmp) / "TODO.md"
        gd = pathlib.Path(tmp) / "goals"
        of = pathlib.Path(tmp) / "human-touches.jsonl"
        pf = pathlib.Path(tmp) / "plan.json"
        gd.mkdir()

        tf.write_text("## CYCLE CLEAN - auto-loop 2026-11-26\nAll autonomous work. No human markers.\n", encoding="utf-8")
        (gd / "lane.md").write_text("# Lane Goals\nAll automated.\n", encoding="utf-8")

        result = run(tf, gd, of, pf)
        assert result["total_touches"] == 0, f"T3: expected 0 touches, got {result['total_touches']}"
        # With 0 cycles having touches, avg should be 0 (or no cycles analyzed)
        plan_data = json.loads(pf.read_text(encoding="utf-8"))
        assert plan_data["meets_target"] is True, f"T3: expected meets_target=True"

        results.append(("T3: clean cycle -> 0 touches, meets target", "PASS"))

    # --- Test 4: Touch types correctly classified ---
    with tempfile.TemporaryDirectory() as tmp:
        tf = pathlib.Path(tmp) / "TODO.md"
        gd = pathlib.Path(tmp) / "goals"
        of = pathlib.Path(tmp) / "human-touches.jsonl"
        pf = pathlib.Path(tmp) / "plan.json"
        gd.mkdir()

        # One section with all 4 types
        tf.write_text(
            "## CYCLE MIXED - user directive 2026-11-25\n"
            "pending ratification from seat.\n"
            "NEEDS-HUMAN for infra change.\n"
            "user changed the topic mid-cycle.\n",
            encoding="utf-8"
        )
        (gd / "lane.md").write_text("# Lane\nClean.\n", encoding="utf-8")

        result = run(tf, gd, of, pf)
        plan_data = json.loads(pf.read_text(encoding="utf-8"))
        rp = plan_data["removal_plan"]
        # Should have all 4 types (redirect pattern: "user changed")
        expected_types = {"goal_set_trigger", "ratification", "unblock", "redirect"}
        found_types = set(rp.keys())
        assert expected_types <= found_types, f"T4: expected {expected_types}, got {found_types}"

        results.append(("T4: all 4 touch types correctly classified", "PASS"))

    # Print results
    all_pass = True
    for name, status in results:
        print(f"  [{status}] {name}")
        if status != "PASS":
            all_pass = False
    print(f"\n{'ALL PASS' if all_pass else 'FAILURES DETECTED'} ({len(results)} tests)")
    return all_pass


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    result = run()
    print(json.dumps(result, indent=2))
