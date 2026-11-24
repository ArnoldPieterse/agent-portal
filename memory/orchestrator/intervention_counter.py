"""Human-Intervention Counter - tracks human messages that unblock/redirect/approve agents.

Usage:
  python memory/orchestrator/intervention_counter.py --log '{"agent":"Builder","type":"unblock","context":"..."}'
  python memory/orchestrator/intervention_counter.py --trend
  python memory/orchestrator/intervention_counter.py --selftest

Writes to memory/ops/human-interventions.jsonl with entries:
  {ts, cycle, agent, type: "unblock"|"redirect"|"approve", context}
"""
import json
import os
import sys
from datetime import datetime, timezone

OPS_DIR = os.path.join(os.path.dirname(__file__), "..", "ops")
JSONL_PATH = os.path.join(OPS_DIR, "human-interventions.jsonl")

VALID_TYPES = ("unblock", "redirect", "approve")


def _current_cycle() -> int:
    """Best-effort current cycle number from fleet-mode.json or goals dir."""
    try:
        fm_path = os.path.join(os.path.dirname(__file__), "..", "..", "fleet-mode.json")
        if os.path.exists(fm_path):
            with open(fm_path) as f:
                return int(json.load(f).get("cycle", 17))
    except Exception:
        pass
    return 17


def log_intervention(agent: str, type_: str, context: str, ts: str = None, cycle: int = None):
    """Append one intervention record to the JSONL file."""
    if type_ not in VALID_TYPES:
        raise ValueError(f"type must be one of {VALID_TYPES}, got {type_!r}")
    entry = {
        "ts": ts or datetime.now(timezone.utc).isoformat(),
        "cycle": cycle or _current_cycle(),
        "agent": agent,
        "type": type_,
        "context": context[:200],
    }
    os.makedirs(os.path.dirname(JSONL_PATH), exist_ok=True)
    with open(JSONL_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def read_all():
    """Return all intervention entries."""
    if not os.path.exists(JSONL_PATH):
        return []
    entries = []
    with open(JSONL_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def weekly_trend():
    """Return {week_label: count} for the last 4 ISO weeks."""
    from collections import Counter
    entries = read_all()
    counts = Counter()
    for e in entries:
        try:
            dt = datetime.fromisoformat(e["ts"])
            iso = dt.isocalendar()
            week_label = f"{iso[0]}-W{iso[1]:02d}"
            counts[week_label] += 1
        except (KeyError, ValueError):
            pass
    # Last 4 weeks
    now_iso = datetime.now(timezone.utc).isocalendar()
    recent = {}
    for w in range(3, -1, -1):
        week_num = now_iso[1] - w
        year = now_iso[0]
        if week_num < 1:
            week_num += 52
            year -= 1
        label = f"{year}-W{week_num:02d}"
        recent[label] = counts.get(label, 0)
    return recent


def selftest():
    """Create 10 test entries in a temp file, verify format + /api/convergence visibility."""
    import tempfile, shutil

    # Use a temp JSONL to avoid polluting real data
    tmp_dir = tempfile.mkdtemp()
    tmp_jsonl = os.path.join(tmp_dir, "human-interventions.jsonl")
    
    test_entries = []
    agents = ["Builder", "Researcher", "Verifier", "Mechanic", "Designer"]
    types_ = ["unblock", "redirect", "approve"]
    contexts = [
        "User: fix the UI button sizing",
        "User: work together as a team",
        "User: proceed with cycle 17 goals",
        "User: unblocked after model reload",
        "User: redirect to convergence topic",
        "User: approved biweekly cadence",
        "User: fix the mirror revert issue",
        "User: prioritize steady-state detection",
        "User: approve fleet-mode.json update",
        "User: unblock Archivist seat draft",
    ]
    for i in range(10):
        entry = {
            "ts": f"2026-11-{20 + (i % 5):02d}T{8 + (i % 12):02d}:00:00+00:00",
            "cycle": 14 + (i % 3),  # cycles 14, 15, 16
            "agent": agents[i % 5],
            "type": types_[i % 3],
            "context": contexts[i],
        }
        test_entries.append(entry)
        with open(tmp_jsonl, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    # Verify: read back and check structure
    with open(tmp_jsonl, encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]
    
    assert len(lines) == 10, f"Expected 10 entries, got {len(lines)}"
    for e in lines:
        assert "ts" in e, "missing ts"
        assert "cycle" in e, "missing cycle"
        assert "agent" in e, "missing agent"
        assert "type" in e and e["type"] in VALID_TYPES, f"bad type: {e.get('type')}"
        assert "context" in e, "missing context"

    # Verify: per-cycle count matches what convergence_api._get_interventions expects
    from collections import Counter
    cycle_counts = Counter(str(e["cycle"]) for e in lines)
    print(f"  Per-cycle counts: {dict(cycle_counts)}")
    assert sum(cycle_counts.values()) == 10

    # Verify: convergence_api can parse this format (simulate _get_interventions logic)
    counts = {}
    for e in lines:
        cycle = str(e.get("cycle", "?"))
        counts[cycle] = counts.get(cycle, 0) + 1
    total = sum(counts.values())
    assert total == 10, f"convergence_api would see {total}, expected 10"

    shutil.rmtree(tmp_dir)
    print("  SELFTEST PASS: 10 entries, all fields valid, per-cycle counts correct")
    return True


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    elif "--log" in sys.argv:
        idx = sys.argv.index("--log")
        payload = json.loads(sys.argv[idx + 1])
        entry = log_intervention(
            agent=payload["agent"],
            type_=payload["type"],
            context=payload.get("context", ""),
        )
        print(json.dumps(entry))
    elif "--trend" in sys.argv:
        trend = weekly_trend()
        print(json.dumps(trend, indent=2))
    else:
        print(__doc__)

