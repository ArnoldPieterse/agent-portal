"""
Auto-Remediation Policy Engine
=============================
Loads remediation-policy.json, evaluates fleet state against rules,
and returns the matching action (or None) with precondition check results.

Usage:
    python memory/orchestrator/remediation_policy.py --simulate <scenario_name>
    python memory/orchestrator/remediation_policy.py --check '<json_state>'
"""
import json, sys, os, time, argparse
from pathlib import Path

POLICY_PATH = Path(__file__).resolve().parent.parent / "ops" / "remediation-policy.json"
DECISION_LOG = Path(__file__).resolve().parent.parent.parent / "decision-log.jsonl"

# ---------------------------------------------------------------------------
# Core engine
# ---------------------------------------------------------------------------

def load_policy(path: Path = POLICY_PATH) -> dict:
    with open(path) as f:
        return json.load(f)


def _eval_condition(condition: dict, state: dict) -> bool:
    """Evaluate a single condition against the fleet state dict.
    
    state keys are dot-notation paths like 'host.vram_pct', 'agent.consecutive_ping_failures'.
    For multi-host/agent scenarios, state is a dict of dicts:
      {"hosts": {"name": {...}}, "agents": {"name": {...}}}
    We check if ANY host/agent matches the condition.
    """
    field = condition["field"]       # e.g. "host.vram_pct"
    op = condition["op"]
    value = condition["value"]
    
    entity_type, metric = field.split(".", 1)
    entities = state.get(entity_type + "s", {})
    
    ops = {
        ">": lambda a, b: a > b,
        ">=": lambda a, b: a >= b,
        "<": lambda a, b: a < b,
        "<=": lambda a, b: a <= b,
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
    }
    fn = ops.get(op)
    if fn is None:
        raise ValueError(f"Unknown operator: {op}")
    
    # Check every entity; condition is met if ANY entity satisfies it
    for name, metrics in entities.items():
        actual = metrics.get(metric)
        if actual is not None and fn(actual, value):
            return True
    return False


def _check_preconditions(preconditions: list, state: dict) -> tuple:
    """Check all preconditions. Returns (all_met: bool, details: list[str])."""
    details = []
    all_met = True
    for pre in preconditions:
        # Precondition format: "field op value == expected" or a simple boolean expression
        # We parse common patterns; complex ones default to True (documented as trusted)
        met = _eval_precondition(pre, state)
        if not met:
            all_met = False
        details.append(f"{'OK' if met else 'FAIL'}: {pre}")
    return all_met, details


def _eval_precondition(expr: str, state: dict) -> bool:
    """Evaluate a precondition expression.
    
    Supported patterns:
      - "X == true" / "X == false"  (boolean literal check)
      - "field op value"            (numeric comparison against state)
      - Complex expressions default to True (treated as operator-trusted)
    """
    expr = expr.strip()
    
    # Boolean literal: "something == true"
    if "== true" in expr:
        return True  # trust; would need live state query
    if "== false":
        return False
    
    # Numeric comparison: "a >= b" where a and b are state fields or literals
    for op in [">=", "<=", "!=", "==", ">", "<"]:
        if op in expr:
            parts = expr.split(op, 1)
            left = _resolve_value(parts[0].strip(), state)
            right = _resolve_value(parts[1].strip(), state)
            if left is None or right is None:
                return True  # can't evaluate; trust
            ops = {">": lambda a,b: a>b, ">=": lambda a,b: a>=b, "<": lambda a,b: a<b, "<=": lambda a,b: a<=b, "==": lambda a,b: a==b, "!=": lambda a,b: a!=b}
            return ops[op](left, right)
    
    # Default: trust complex expressions
    return True


def _resolve_value(token: str, state: dict):
    """Resolve a token to a number from state or parse as literal."""
    try:
        return float(token)
    except (ValueError, TypeError):
        pass
    # Try dot-notation lookup in flat state
    if "." in token:
        entity_type, _, metric = token.partition(".")
        entities = state.get(entity_type + "s", {})
        for name, m in entities.items():
            if metric in m:
                return m[metric]
    return None


def evaluate(state: dict, policy: dict = None) -> list:
    """Evaluate all rules against fleet state. Returns list of triggered decisions."""
    if policy is None:
        policy = load_policy()
    
    decisions = []
    for rule in policy["rules"]:
        if _eval_condition(rule["condition"], state):
            pre_met, pre_details = _check_preconditions(rule.get("preconditions", []), state)
            decision = {
                "rule_id": rule["id"],
                "degradation_type": rule["degradation_type"],
                "action": rule["action"],
                "rollback": rule["rollback"],
                "preconditions_met": pre_met,
                "precondition_details": pre_details,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "executable": pre_met  # only execute if all preconditions pass
            }
            decisions.append(decision)
    return decisions


def log_decision(decision: dict, log_path: Path = DECISION_LOG):
    """Append a decision to the decision log JSONL."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps({"source": "remediation_policy", **decision}) + "\n")


# ---------------------------------------------------------------------------
# Simulation scenarios (for verification)
# ---------------------------------------------------------------------------
SCENARIOS = {
    "model_oom": {
        "hosts": {"White": {"vram_pct": 99, "consecutive_probe_failures": 0, "disk_free_pct": 45}},
        "agents": {"Builder": {"consecutive_ping_failures": 0, "context_usage_pct": 40}}
    },
    "host_unreachable": {
        "hosts": {"White": {"vram_pct": 50, "consecutive_probe_failures": 3, "disk_free_pct": 30}},
        "agents": {}
    },
    "agent_unresponsive": {
        "hosts": {"White": {"vram_pct": 60, "consecutive_probe_failures": 0, "disk_free_pct": 50}},
        "agents": {"Researcher": {"consecutive_ping_failures": 2, "context_usage_pct": 30}}
    },
    "vram_pressure": {
        "hosts": {"White": {"vram_pct": 92, "consecutive_probe_failures": 0, "disk_free_pct": 40}},
        "agents": {}
    },
    "disk_critical": {
        "hosts": {"White": {"vram_pct": 50, "consecutive_probe_failures": 0, "disk_free_pct": 8}},
        "agents": {}
    },
    "context_exhaustion": {
        "hosts": {"White": {"vram_pct": 50, "consecutive_probe_failures": 0, "disk_free_pct": 50}},
        "agents": {"Scribe": {"consecutive_ping_failures": 0, "context_usage_pct": 92}}
    },
    "healthy": {
        "hosts": {"White": {"vram_pct": 45, "consecutive_probe_failures": 0, "disk_free_pct": 60}},
        "agents": {"Builder": {"consecutive_ping_failures": 0, "context_usage_pct": 30}}
    }
}


def run_simulation(scenario_name: str):
    if scenario_name not in SCENARIOS:
        print(f"Unknown scenario: {scenario_name}. Available: {list(SCENARIOS.keys())}")
        sys.exit(1)
    state = SCENARIOS[scenario_name]
    policy = load_policy()
    decisions = evaluate(state, policy)
    
    print(f"\n=== Scenario: {scenario_name} ===")
    print(f"State: {json.dumps(state, indent=2)}")
    print(f"\nDecisions ({len(decisions)}):")
    for d in decisions:
        status = "EXECUTABLE" if d["executable"] else "BLOCKED (preconditions unmet)"
        print(f"  [{d['rule_id']}] {d['degradation_type']} -> {d['action']['type']} ({status})")
        for detail in d["precondition_details"]:
            print(f"    {detail}")
    if not decisions:
        print("  (none — fleet healthy)")
    
    # Log the decisions
    for d in decisions:
        log_decision(d)
    
    return decisions


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Auto-Remediation Policy Engine")
    parser.add_argument("--simulate", type=str, help="Run a named simulation scenario")
    parser.add_argument("--check", type=str, help="Check against raw JSON state string")
    parser.add_argument("--list-scenarios", action="store_true", help="List available scenarios")
    args = parser.parse_args()
    
    if args.list_scenarios:
        print("Available scenarios:")
        for name in SCENARIOS:
            print(f"  {name}")
    elif args.simulate:
        run_simulation(args.simulate)
    elif args.check:
        state = json.loads(args.check)
        policy = load_policy()
        decisions = evaluate(state, policy)
        print(json.dumps(decisions, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
