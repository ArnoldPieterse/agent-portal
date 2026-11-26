#!/usr/bin/env python3
"""intervention_logger.py - Detect and log human interventions from chat messages.

Goal #4 (Cycle 17): Hook module for agent_portal.py message handler.
When a human message matches unblock/redirect/approve patterns,
logs to memory/ops/human-interventions.jsonl with structured fields.

Usage:
  python memory/builder/intervention_logger.py --selftest   # verify detection + logging
  python memory/builder/intervention_logger.py --check "message text"  # classify one message

Integration (when portal is edited):
  from intervention_logger import check_message, log_intervention
  result = check_message(human_text)
  if result: log_intervention(agent=result['agent'], type=result['type'], context=human_text[:200])
"""
import json, os, re, sys
from datetime import datetime, timezone

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_FILE = os.path.join(WS, "memory", "ops", "human-interventions.jsonl")

# --- Pattern definitions ---------------------------------------------------
# Each pattern: (type, regex, description)
PATTERNS = [
    # Unblock patterns: user explicitly unblocks or removes a blocker
    ("unblock", re.compile(
        r"(?ix)\b(unblock|unblocked|clear.*block|remove.*blocker"
        r"|go.*ahead|proceed|treat.*as.*normal"
        r"|no.*longer.*block|drop.*the.*block"
        r"|relocated|failover|fallback)\b",
    ), "User unblocks a lane or removes a blocker"),

    # Redirect patterns: user changes direction, priority, or scope
    ("redirect", re.compile(
        r"(?ix)\b(redirect|reprioriti[sz]e|change.*priority|switch"
        r"|stop.*doing|instead.*do|focus.*on"
        r"|prioritize|drop.*goal|skip.*this"
        r"|change.*course|new.*direction|pivot)\b",
    ), "User redirects work or changes priority/scope"),

    # Approve patterns: user explicitly approves something
    ("approve", re.compile(
        r"(?ix)\b(approved?|lgtm|looks.*good|ship.*it"
        r"|go.*for.*it|green.*light|sign.*off"
        r"|accepted?|fine.*with.*that|agreed)\b",
    ), "User approves a proposal or approach"),
]

# Agent detection: which agent is the message targeting?
AGENT_RE = re.compile(r"@?(Builder|Mechanic|Archivist|Researcher|Orchestrator|Verifier|Scribe|Designer)", re.IGNORECASE)


def check_message(text):
    """Classify a human message. Returns {type, agent, patterns_matched} or None."""
    if not text or not text.strip():
        return None

    matched = []
    for mtype, pattern, desc in PATTERNS:
        m = pattern.search(text)
        if m:
            matched.append((mtype, m.group(0)))

    if not matched:
        return None

    # Primary type = first match (priority: unblock > redirect > approve by order)
    primary_type = matched[0][0]

    # Detect target agent
    agent_match = AGENT_RE.search(text)
    agent = agent_match.group(1) if agent_match else "Group"

    return {
        "type": primary_type,
        "agent": agent,
        "patterns_matched": [pm[0] for pm in matched],
        "matched_text": [pm[1] for pm in matched],
    }


def log_intervention(agent, type_, context, cycle=None):
    """Append a structured intervention record. Returns the entry dict."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": agent,
        "type": type_,
        "context": context[:300],  # cap length
    }
    if cycle is not None:
        entry["cycle"] = cycle

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def selftest():
    """Verify: 5 matching messages logged correctly; non-matching not logged."""
    import tempfile, shutil

    print("=== intervention_logger.py --selftest ===")
    passed = 0
    failed = 0

    # Use a temp log file
    global LOG_FILE
    orig_log = LOG_FILE
    tmpdir = tempfile.mkdtemp(prefix="intlog_test_")
    LOG_FILE = os.path.join(tmpdir, "human-interventions.jsonl")

    try:
        # --- 5 matching messages (should be detected) ---
        test_msgs = [
            ("Please unblock the Builder lane, it's been stuck for hours", "unblock", "Builder"),
            ("@Mechanic redirect priority: do the VRAM forecast before probes", "redirect", "Mechanic"),
            ("Approved, ship it to production", "approve", "Group"),
            ("The model was relocated to another host, treat as normal seat", "unblock", "Group"),
            ("@Archivist change course - focus on the convergence KB instead", "redirect", "Archivist"),
        ]

        for text, expected_type, expected_agent in test_msgs:
            result = check_message(text)
            if result is None:
                print(f"  FAIL: not detected: '{text[:50]}...'")
                failed += 1
                continue
            if result["type"] != expected_type:
                print(f"  FAIL: wrong type '{result['type']}' (expected '{expected_type}'): '{text[:50]}'")
                failed += 1
                continue
            if result["agent"] != expected_agent:
                print(f"  FAIL: wrong agent '{result['agent']}' (expected '{expected_agent}'): '{text[:50]}'")
                failed += 1
                continue

            # Log it
            entry = log_intervention(result["agent"], result["type"], text)
            passed += 1
            print(f"  PASS: [{result['type']}] @ {result['agent']}: '{text[:50]}'")

        # --- 3 non-matching messages (should NOT be detected) ---
        non_matching = [
            "What's the current status of cycle 17?",
            "The weather is nice today, let's take a break",
            "Can you explain how the mirror sync works?",
        ]

        for text in non_matching:
            result = check_message(text)
            if result is not None:
                print(f"  FAIL: false positive on '{text[:50]}': {result}")
                failed += 1
            else:
                passed += 1
                print(f"  PASS: correctly ignored: '{text[:50]}'")

        # --- Verify log file has exactly 5 entries ---
        with open(LOG_FILE, encoding="utf-8") as f:
            lines = [l for l in f.read().strip().splitlines() if l.strip()]
        assert len(lines) == 5, f"Expected 5 log entries, got {len(lines)}"

        # Verify structure of first entry
        e0 = json.loads(lines[0])
        for field in ["ts", "agent", "type", "context"]:
            assert field in e0, f"Missing field '{field}' in log entry"
        passed += 1
        print(f"  PASS: log file has {len(lines)} entries with correct structure")

    finally:
        LOG_FILE = orig_log
        shutil.rmtree(tmpdir, ignore_errors=True)

    total = passed + failed
    print(f"\nResult: {passed}/{total} tests passed")
    if failed == 0:
        print("SELFTEST PASS")
        return 0
    else:
        print("SELFTEST FAIL")
        return 1


# --- Predictive Intervention Detector (Goal #5, Cycle 18) -------------------
# Analyzes an agent's recent messages for patterns that PRECEDE human intervention.
# Signals: repeated failures, blocker mentions, retry loops, escalation language.

PREDICT_N = 5  # look back N messages

SIGNAL_PATTERNS = [
    ("repeated_failure", re.compile(
        r"(?ix)\b(fail(?:ed|ure)?|error|crash|exception|traceback|exit\s+code\s+[1-9])\b",
    ), 0.25, "Failure/error language detected"),
    ("blocker_mention", re.compile(
        r"(?ix)\b(block(?:ed|er)?|stuck|waiting\s+(?:for|on)|cannot\s+proceed"
        r"|unable\s+to|no\s+way\s+forward|deadlock)\b",
    ), 0.30, "Blocker or stuck language"),
    ("retry_loop", re.compile(
        r"(?ix)\b(trying\s+(?:again|once\s+more)|re-?attempt|second\s+try"
        r"|let\s+me\s+try\s+(?:a\s+)?(?:different|other|alternative))\b",
    ), 0.20, "Retry/re-attempt language"),
    ("escalation", re.compile(
        r"(?ix)\b(need(s|ed)?\s+(?:human|admin|user)\s+help"
        r"|NEEDS-HUMAN|escalat|cannot\s+solve|out\s+of\s+my\s+scope"
        r"|requires\s+manual)\b",
    ), 0.35, "Explicit escalation or out-of-scope"),
]


def predict_intervention(agent_messages, n=None):
    """Analyze last N messages for pre-intervention signals.
    
    Args:
        agent_messages: list of message strings (most recent last)
        n: lookback window (default PREDICT_N=5)
    
    Returns:
        dict with keys:
            risk_score: float 0.0-1.0
            signals: list of {name, count, weight, description}
            verdict: "low" | "medium" | "high"
            detail: human-readable summary
    """
    if n is None:
        n = PREDICT_N
    msgs = agent_messages[-n:] if len(agent_messages) > n else agent_messages
    
    if not msgs:
        return {"risk_score": 0.0, "signals": [], "verdict": "low", "detail": "no messages"}
    
    signals = []
    total_score = 0.0
    
    for name, pattern, weight, desc in SIGNAL_PATTERNS:
        hits = sum(1 for msg in msgs if pattern.search(msg))
        if hits > 0:
            # Diminishing returns: multiple hits in window add less each time
            effective_weight = weight * (1.0 + 0.3 * min(hits - 1, 2))
            total_score += effective_weight
            signals.append({"name": name, "count": hits, "weight": round(effective_weight, 3), "description": desc})
    
    # Cap at 1.0
    risk_score = min(1.0, total_score)
    
    if risk_score >= 0.6:
        verdict = "high"
    elif risk_score >= 0.3:
        verdict = "medium"
    else:
        verdict = "low"
    
    detail_parts = []
    for s in signals:
        detail_parts.append(f"{s['name']} x{s['count']}")
    detail = f"risk={risk_score:.2f} [{verdict}] signals: {', '.join(detail_parts) if detail_parts else 'none'}"
    
    return {
        "risk_score": round(risk_score, 3),
        "signals": signals,
        "verdict": verdict,
        "detail": detail,
    }


def selftest_predict():
    """Verify predict_intervention on known scenarios."""
    print("\n--- Predictive Intervention Detector selftest ---")
    passed = 0
    failed = 0
    
    # Scenario 1: Agent hitting repeated errors -> HIGH risk
    msgs_high = [
        "Running the build... got an error in module X",
        "Trying again with a different flag... still failing",
        "Second attempt failed - exit code 1, traceback attached",
        "Let me try once more with the workaround",
        "Still crashing. I'm blocked and cannot proceed without human help.",
    ]
    r = predict_intervention(msgs_high)
    if r["verdict"] == "high" and r["risk_score"] >= 0.6:
        passed += 1
        print(f"  PASS: high-risk scenario -> {r['detail']}")
    else:
        failed += 1
        print(f"  FAIL: expected high, got {r['verdict']} ({r['risk_score']}): {r['detail']}")
    
    # Scenario 2: Normal productive work -> LOW risk
    msgs_low = [
        "Wrote the new module with 3 functions and unit tests",
        "All 5 selftests pass. Moving to integration.",
        "Updated the INDEX pointer and committed.",
        "Next: extending the dashboard panel per Pixel's spec.",
        "Done for this pass. Evidence logged.",
    ]
    r = predict_intervention(msgs_low)
    if r["verdict"] == "low" and r["risk_score"] < 0.3:
        passed += 1
        print(f"  PASS: low-risk scenario -> {r['detail']}")
    else:
        failed += 1
        print(f"  FAIL: expected low, got {r['verdict']} ({r['risk_score']}): {r['detail']}")
    
    # Scenario 3: Mild concern (one failure mention) -> MEDIUM at most
    msgs_med = [
        "Started the refactor",
        "One test failed on edge case, investigating",
        "Fixed it - all green now",
        "Continuing with the next task",
        "Progress logged",
    ]
    r = predict_intervention(msgs_med)
    if r["verdict"] in ("low", "medium") and r["risk_score"] < 0.6:
        passed += 1
        print(f"  PASS: medium/low scenario -> {r['detail']}")
    else:
        failed += 1
        print(f"  FAIL: expected low/medium, got {r['verdict']} ({r['risk_score']}): {r['detail']}")
    
    # Scenario 4: Empty input -> LOW, no crash
    r = predict_intervention([])
    if r["verdict"] == "low" and r["risk_score"] == 0.0:
        passed += 1
        print(f"  PASS: empty input -> {r['detail']}")
    else:
        failed += 1
        print(f"  FAIL: empty input unexpected: {r}")
    
    # Scenario 5: Exactly N=5 window respected (6th message ignored)
    msgs_window = ["old failure here"] * 3 + ["all good now"] * 4
    r = predict_intervention(msgs_window, n=5)  # only last 5 = all "good"
    if r["risk_score"] < 0.3:
        passed += 1
        print(f"  PASS: window respected (6 msgs, n=5 ignores oldest) -> {r['detail']}")
    else:
        failed += 1
        print(f"  FAIL: window not respected: {r['detail']}")
    
    total = passed + failed
    print(f"  Predict selftest: {passed}/{total} passed")
    return failed == 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok1 = selftest() == 0
        ok2 = selftest_predict()
        sys.exit(0 if (ok1 and ok2) else 1)
    elif "--predict" in sys.argv:
        idx = sys.argv.index("--predict")
        msgs = sys.argv[idx + 1:]
        result = predict_intervention(msgs)
        print(json.dumps(result, indent=2))
    elif "--check" in sys.argv:
        idx = sys.argv.index("--check")
        text = " ".join(sys.argv[idx + 1:])
        result = check_message(text)
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("no intervention detected")
    else:
        print(__doc__)
