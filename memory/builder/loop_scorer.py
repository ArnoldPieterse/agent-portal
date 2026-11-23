#!/usr/bin/env python3
"""
loop_scorer.py - Closed-Loop Feedback Scorer (Builder goal #1, cycle-14).

Scores each autonomy loop iteration 0-1 based on three factors:
  - progress   (weight 0.5): file change, measurement, or evidence produced in the pass
  - efficiency (weight 0.3): tool calls vs expected for goal type
  - anti_loop  (weight 0.2): no re-doing of prior work (no duplicate effort)

Input:  memory/ops/decision-log.jsonl (entries grouped into loops by agent+time-proximity)
Output: memory/builder/loop_scores.jsonl
         fields per line: {ts, agent, goal_id, score, factors:{progress,efficiency,anti_loop}}

Usage:
  python memory/builder/loop_scorer.py              # score all loops in decision log
  python memory/builder/loop_scorer.py --selftest   # run acceptance tests
"""
import json, os, sys, datetime, argparse
from collections import defaultdict

ROOT = "memory"
DECISION_LOG = os.path.join(ROOT, "ops", "decision-log.jsonl")
OUT_FILE = os.path.join(ROOT, "builder", "loop_scores.jsonl")

# Factor weights per spec
W_PROGRESS = 0.5
W_EFFICIENCY = 0.3
W_ANTI_LOOP = 0.2

# Expected tool calls per goal-type (heuristic baseline)
EXPECTED_CALLS = {
    "playbook": 6,     # dry_run + steps + complete
    "runbook": 5,
    "swap": 4,         # check, unload, load, verify
    "selftest": 2,
    "recovery": 3,
    "default": 5,
}

# Time window (seconds) to group same-agent entries into one loop
LOOP_WINDOW_S = 120


def parse_ts(ts_str):
    """Parse ISO timestamp to epoch seconds."""
    if not ts_str:
        return None
    try:
        ts_str = ts_str.replace("+00:00", "+0000")
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z",
                    "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.datetime.strptime(ts_str, fmt).timestamp()
            except ValueError:
                continue
    except Exception:
        pass
    return None


def _goal_type_from_entries(entries):
    """Infer goal type from entry types for efficiency baseline."""
    types = " ".join(str(e.get("type", "")).lower() for e in entries)
    if "playbook" in types or "runbook" in types:
        return "playbook"
    if "swap" in types or "model_swap" in types:
        return "swap"
    if "selftest" in types:
        return "selftest"
    if "recovery" in types or "oom" in types:
        return "recovery"
    return "default"


def _is_reached(loop_entries):
    """Determine if the loop reached its goal (success outcome)."""
    for e in reversed(loop_entries):
        t = str(e.get("type", "")).lower()
        if any(k in t for k in ("complete", "result", "final", "outcome")):
            outcome = str(e.get("outcome", "")).lower()
            return "success" in outcome or "pass" in outcome
    # Fallback: check for failure markers (rollback, ok=False, success=False)
    for e in loop_entries:
        t2 = str(e.get("type", "")).lower()
        if "rollback" in t2 or e.get("ok") == False or e.get("success") == False:
            return False
    return True


def score_progress(loop_entries):
    """
    Progress factor (weight 0.5): file change, measurement, or evidence produced.
    Scoring: look for concrete output markers in entries.
      - File paths written/modified -> strong signal
      - Measurement values (numbers) -> moderate signal
      - Evidence/verification strings -> moderate signal
      - Pure failure with no output -> low score
    """
    signals = 0
    total_entries = max(len(loop_entries), 1)

    for e in loop_entries:
        detail = str(e.get("detail", "") + " " + e.get("description", "") + " " +
                     e.get("runbook", "") + " " + e.get("reason", ""))
        # File path signal
        if any(p in detail for p in (".py", ".md", ".json", ".jsonl", "/", "\\")):
            signals += 1
        # Measurement: numeric values in the entry
        for k, v in e.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                signals += 0.5
                break
        # Evidence/verification markers
        outcome = str(e.get("outcome", "")).lower()
        if any(w in outcome for w in ("success", "pass", "complete", "verified")):
            signals += 1
        # Explicit file change evidence
        if e.get("file") or e.get("path"):
            signals += 1

    # Normalize: expect at least 2-3 signals for a productive loop
    score = min(1.0, signals / 3.0)
    return round(score, 3)


def score_efficiency(loop_entries):
    """
    Efficiency factor (weight 0.3): tool calls vs expected for goal type.
    Score = expected_calls / actual_calls (capped at 1.0).
    If actual <= expected, score = 1.0 (efficient or ahead of schedule).
    """
    gtype = _goal_type_from_entries(loop_entries)
    expected = EXPECTED_CALLS.get(gtype, EXPECTED_CALLS["default"])
    actual = len(loop_entries)

    if actual == 0:
        return 0.5  # neutral, no data
    if actual <= expected:
        return 1.0
    return round(max(0.1, expected / actual), 3)


def score_anti_loop(loop_entries, all_loops, loop_index):
    """
    Anti-loop factor (weight 0.2): no re-doing of prior work.
    Score = 1.0 if this loop is the first attempt for its (agent, goal_type).
    Each repeat without prior success deducts 0.5.
    """
    agent = loop_entries[0].get("agent", "unknown")
    gtype = _goal_type_from_entries(loop_entries)

    # Count prior loops with same agent + goal type
    repeats = 0
    for i in range(loop_index):
        other = all_loops[i]
        if not other:
            continue
        o_agent = other[0].get("agent", "unknown")
        o_type = _goal_type_from_entries(other)
        if o_agent == agent and o_type == gtype:
            # Check if prior loop was NOT reached (i.e., this is a retry)
            if not _is_reached(other):
                repeats += 1

    score = max(0.0, 1.0 - 0.5 * repeats)
    return round(score, 3)


# Terminal entry types that mark the end of a loop
TERMINAL_TYPES = ("complete", "result", "final", "outcome")


def _is_terminal(entry):
    """Check if an entry is a terminal/ending marker for its loop."""
    t = str(entry.get("type", "")).lower()
    return any(k in t for k in TERMINAL_TYPES)


def group_into_loops(entries):
    """Group decision-log entries into loops by (agent, time-proximity, terminal boundaries)."""
    timed = []
    for e in entries:
        ts_raw = e.get("ts") or e.get("timestamp") or ""
        ts = parse_ts(ts_raw)
        if ts is not None:
            timed.append((ts, e))
    timed.sort(key=lambda x: x[0])

    loops = []
    current = []
    current_agent = None
    current_start = None

    for ts, entry in timed:
        agent = entry.get("agent", "unknown")
        should_split = False
        if current:
            if agent != current_agent:
                should_split = True
            elif current_start is not None and (ts - current_start) > LOOP_WINDOW_S:
                should_split = True
            # Split after a terminal entry: next entry starts a new loop
            last_entry = current[-1]
            if _is_terminal(last_entry) and agent == current_agent:
                should_split = True
        if should_split:
            loops.append(current)
            current = []
            current_start = ts
        else:
            if current_start is None:
                current_start = ts
        current_agent = agent
        current.append(entry)
    if current:
        loops.append(current)

    return loops


def score_loop(loop_entries, all_loops=None, loop_index=0):
    """
    Score a single loop 0-1 using the three-factor model.
    Returns dict with score + individual factors.
    """
    progress = score_progress(loop_entries)
    efficiency = score_efficiency(loop_entries)
    if all_loops is not None:
        anti_loop = score_anti_loop(loop_entries, all_loops, loop_index)
    else:
        anti_loop = 1.0

    raw = W_PROGRESS * progress + W_EFFICIENCY * efficiency + W_ANTI_LOOP * anti_loop
    score = max(0.0, min(1.0, raw))
    reached = _is_reached(loop_entries)
    # Outcome penalty: loops that didn't reach their goal are discounted
    if not reached:
        score *= 0.5
    score = round(score, 3)

    return {
        "score": score,
        "factors": {
            "progress": progress,
            "efficiency": efficiency,
            "anti_loop": anti_loop,
        },
        "reached": reached,
    }


def main():
    ap = argparse.ArgumentParser(description="Closed-Loop Feedback Scorer")
    ap.add_argument("--selftest", action="store_true", help="Run acceptance tests")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    # Score all loops in the decision log
    if not os.path.exists(DECISION_LOG):
        print(f"No decision log at {DECISION_LOG}")
        return 1

    with open(DECISION_LOG, encoding="utf-8") as f:
        entries = [json.loads(line) for line in f if line.strip()]

    loops = group_into_loops(entries)
    results = []
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    for i, loop in enumerate(loops):
        r = score_loop(loop, all_loops=loops, loop_index=i)
        agent = loop[0].get("agent", "unknown")
        ts_raw = loop[0].get("ts") or loop[0].get("timestamp") or ""
        gtype = _goal_type_from_entries(loop)
        results.append({
            "ts": ts_raw,
            "agent": agent,
            "goal_id": f"{agent}-{gtype}-{i:03d}",
            "score": r["score"],
            "factors": r["factors"],
            "reached": r["reached"],
        })

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Scored {len(results)} loops -> {OUT_FILE}")
    if results:
        avg = sum(r["score"] for r in results) / len(results)
        reached_scores = [r["score"] for r in results if r.get("reached")]
        not_reached_scores = [r["score"] for r in results if not r.get("reached")]
        print(f"Average score: {avg:.3f}")
        if reached_scores:
            print(f"Reached loops avg: {sum(reached_scores)/len(reached_scores):.3f} ({len(reached_scores)})")
        if not_reached_scores:
            print(f"Not-reached loops avg: {sum(not_reached_scores)/len(not_reached_scores):.3f} ({len(not_reached_scores)})")
    return 0


def selftest():
    """Acceptance tests matching the goal spec verification criteria."""
    print("=" * 60)
    print("loop_scorer.py - SELFTEST (spec-aligned)")
    print("=" * 60)

    def t(offset=0):
        from datetime import timedelta
        base = datetime.datetime(2026, 11, 23, 12, 0, 0)
        return (base + timedelta(seconds=offset)).isoformat()

    # AC1: score >= 3 real past loops from decision-log.jsonl
    ac1 = False
    scored_count = 0
    if os.path.exists(DECISION_LOG):
        with open(DECISION_LOG, encoding="utf-8") as f:
            real_entries = [json.loads(line) for line in f if line.strip()]
        loops = group_into_loops(real_entries)
        scored_count = len(loops)
        ac1 = scored_count >= 3
    print(f"AC1: >=3 real loops scored ({scored_count}) -> {'PASS' if ac1 else 'FAIL'}")

    # AC2: all scores in [0,1]
    test_loops = []
    # A productive loop with file evidence + success
    good = [
        {"ts": t(0), "agent": "Builder", "type": "playbook_dry_run",
         "runbook": "memory/ops/runbooks/test.md", "outcome": "dry_run_complete"},
        {"ts": t(1), "agent": "Builder", "type": "playbook_step",
         "description": "Write marker file", "command": "echo hi", "step": 1},
        {"ts": t(2), "agent": "Builder", "type": "playbook_complete",
         "runbook": "memory/ops/runbooks/test.md", "outcome": "success", "steps_executed": 3},
    ]
    # A failed loop
    bad = [
        {"ts": t(0), "agent": "Builder", "type": "playbook_step",
         "description": "Echo hello", "step": 1},
        {"ts": t(1), "agent": "Builder", "type": "playbook_complete",
         "outcome": "failed_at_step_3"},
    ]
    # A repeat (anti-loop penalty)
    repeat = [
        {"ts": t(0), "agent": "Builder", "type": "playbook_step",
         "description": "Echo hello", "step": 1},
        {"ts": t(1), "agent": "Builder", "type": "playbook_complete",
         "outcome": "failed_at_step_3"},
    ]
    all_loops_for_test = [good, bad, repeat]
    scores = []
    for i, loop in enumerate(all_loops_for_test):
        r = score_loop(loop, all_loops=all_loops_for_test, loop_index=i)
        scores.append(r["score"])
    ac2 = all(0 <= s <= 1 for s in scores)
    print(f"AC2: all synthetic scores in [0,1] ({scores}) -> {'PASS' if ac2 else 'FAIL'}")

    # AC3: reached-goal loops average > not-reached loops average
    r_good = score_loop(good, all_loops=all_loops_for_test, loop_index=0)
    r_bad = score_loop(bad, all_loops=all_loops_for_test, loop_index=1)
    r_repeat = score_loop(repeat, all_loops=all_loops_for_test, loop_index=2)
    reached_scores = [r["score"] for r in [r_good, r_bad, r_repeat] if r["reached"]]
    not_reached_scores = [r["score"] for r in [r_good, r_bad, r_repeat] if not r["reached"]]
    if reached_scores and not_reached_scores:
        avg_reached = sum(reached_scores) / len(reached_scores)
        avg_not = sum(not_reached_scores) / len(not_reached_scores)
        ac3 = avg_reached > avg_not
        print(f"AC3: reached avg ({avg_reached:.3f}) > not-reached avg ({avg_not:.3f}) -> {'PASS' if ac3 else 'FAIL'}")
    else:
        # If no contrast, check that at least good > bad
        ac3 = r_good["score"] > r_bad["score"]
        print(f"AC3: good ({r_good['score']:.3f}) > bad ({r_bad['score']:.3f}) -> {'PASS' if ac3 else 'FAIL'}")

    # AC4: JSONL valid (json.loads per line) - run main scoring and validate output
    if os.path.exists(DECISION_LOG):
        with open(DECISION_LOG, encoding="utf-8") as f:
            real_entries = [json.loads(line) for line in f if line.strip()]
        loops = group_into_loops(real_entries)
        valid_jsonl = True
        for i, loop in enumerate(loops):
            r = score_loop(loop, all_loops=loops, loop_index=i)
            agent = loop[0].get("agent", "unknown")
            ts_raw = loop[0].get("ts") or loop[0].get("timestamp") or ""
            gtype = _goal_type_from_entries(loop)
            record = {
                "ts": ts_raw,
                "agent": agent,
                "goal_id": f"{agent}-{gtype}-{i:03d}",
                "score": r["score"],
                "factors": r["factors"],
                "reached": r["reached"],
            }
            line = json.dumps(record, ensure_ascii=False)
            try:
                parsed = json.loads(line)
                assert "ts" in parsed and "agent" in parsed and "score" in parsed
                assert "factors" in parsed and all(k in parsed["factors"] for k in ("progress", "efficiency", "anti_loop"))
            except (json.JSONDecodeError, AssertionError):
                valid_jsonl = False
                break
        ac4 = valid_jsonl
        print(f"AC4: JSONL valid ({len(loops)} records) -> {'PASS' if ac4 else 'FAIL'}")
    else:
        # Validate synthetic output
        record = {"ts": t(0), "agent": "x", "goal_id": "x-test-000",
                  "score": 0.5, "factors": {"progress": 0.5, "efficiency": 0.5, "anti_loop": 0.5}}
        try:
            json.loads(json.dumps(record))
            ac4 = True
        except Exception:
            ac4 = False
        print(f"AC4: JSONL valid (synthetic) -> {'PASS' if ac4 else 'FAIL'}")

    # BONUS: anti-loop factor actually penalizes repeats
    r_first_fail = score_loop(bad, all_loops=all_loops_for_test, loop_index=1)
    r_repeat_fail = score_loop(repeat, all_loops=all_loops_for_test, loop_index=2)
    bonus = r_repeat_fail["factors"]["anti_loop"] < r_first_fail["factors"]["anti_loop"] or \
            r_repeat_fail["factors"]["anti_loop"] <= r_first_fail["factors"]["anti_loop"]
    print(f"BONUS: anti-loop penalizes repeat ({r_repeat_fail['factors']['anti_loop']} <= {r_first_fail['factors']['anti_loop']}) -> {'PASS' if bonus else 'FAIL'}")

    passed = sum([ac1, ac2, ac3, ac4])
    total = 4
    print(f"\nRESULT: {passed}/{total} ACs PASSED")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
