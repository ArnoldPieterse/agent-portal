"""Cross-Lane Contract Tests - Verifier Goal #4 (Cycle 20)
Defines 5 inter-agent API contracts with golden fixtures.
Validates current state; negative tests prove drift detection works.

Usage: python memory/verifier/cross_lane_contracts.py [--self-test | --live]
"""
import pathlib, json, sys, copy
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent  # project root
CONTRACTS_DIR = pathlib.Path(__file__).resolve().parent / 'contracts'

# --- Contract definitions: name -> (source_file, required_fields) ---
# Each contract specifies: file path, required top-level keys with expected types,
# and a golden fixture for reference.

CONTRACTS = {
    'goal_ledger': {
        'file': 'goal_ledger.json',
        'description': 'SSOT goal tracking ledger',
        'required': {
            'generated': str,
            'source': str,
            'evidence_gated': bool,
            'fleet_total_goals': int,
            'fleet_reached': int,
            'fleet_pct_reached': int,
            'agents': dict,
        },
        'nested_rules': {
            'agents.*.total': int,
            'agents.*.reached': int,
            'agents.*.open': int,
            'agents.*.pct_reached': int,
            'agents.*.goals': list,
        },
    },
    'fleet_mode': {
        'file': 'memory/ops/fleet-mode.json',
        'description': 'Fleet state machine SSOT',
        'required': {
            'mode': str,
            'timestamp': str,
            'goal_pct': (int, float),
            'goals_total': int,
            'goals_reached': int,
            'goals_open': int,
            'fsm_state': str,
            'fsm_validated': bool,
        },
        'enum_rules': {
            'mode': ['WORK', 'REST', 'MAINTENANCE'],
            'fsm_state': ['CONVERGING', 'STABLE', 'DEGRADED', 'RECOVERING'],
        },
    },
    'autonomy_score': {
        'file': 'memory/ops/autonomy-score.json',
        'description': 'Convergence autonomy metric',
        'required': {
            'score': (int, float),
            'fleet_readiness': (int, float),
            'components': dict,
            'weights': dict,
            'computed_at': str,
        },
        'invariants': [
            ('weights_sum', lambda d: abs(sum(d['weights'].values()) - 1.0) < 0.01),
            ('score_range', lambda d: 0 <= d['score'] <= 100),
            ('components_nonneg', lambda d: all(v >= 0 for v in d['components'].values())),
        ],
    },
    'cockpit_feed': {
        'file': 'memory/ops/cockpit-feed.json',
        'description': 'Cockpit UI feed data',
        'required': {
            'ts': str,
            'agents': list,
        },
        'nested_rules': {
            'agents.*.name': str,
            'agents.*.state': str,
        },
    },
    'convergence_velocity': {
        'file': 'memory/ops/convergence-velocity.json',
        'description': 'Convergence velocity trend',
        'required': {
            'cycles': (dict, list),
            'trend': str,
            'velocities': list,
        },
        'enum_rules': {
            'trend': ['accelerating', 'stable', 'decelerating', 'declining'],
        },
    },
}


def load_contract_data(name):
    """Load the actual JSON file for a contract."""
    c = CONTRACTS[name]
    path = ROOT / c['file']
    if not path.exists():
        return None, f"FILE NOT FOUND: {c['file']}"
    try:
        return json.loads(path.read_text(encoding='utf-8')), None
    except Exception as e:
        return None, f"PARSE ERROR: {e}"


def validate_contract(name, data=None):
    """Validate a contract. Returns (passed: bool, errors: list)."""
    c = CONTRACTS[name]
    if data is None:
        data, err = load_contract_data(name)
        if err:
            return False, [err]

    errors = []

    # Check required fields
    for field, ftype in c['required'].items():
        if field not in data:
            errors.append(f"MISSING: {field}")
        elif not isinstance(data[field], ftype):
            errors.append(f"TYPE MISMATCH: {field} expected {ftype.__name__ if isinstance(ftype, type) else ftype}, got {type(data[field]).__name__}")

    # Check enum rules
    for field, allowed in c.get('enum_rules', {}).items():
        if field in data and data[field] not in allowed:
            errors.append(f"ENUM VIOLATION: {field}={data[field]!r} not in {allowed}")

    # Check nested rules (simple pattern: 'agents.*.total')
    for rule_path, expected_type in c.get('nested_rules', {}).items():
        parts = rule_path.split('.')
        if len(parts) >= 2 and '*' in parts:
            parent_key = parts[0]
            child_key = parts[-1]
            parent = data.get(parent_key, {})
            if isinstance(parent, dict):
                for k, v in parent.items():
                    if isinstance(v, dict) and child_key in v:
                        val = v[child_key]
                        if not isinstance(val, expected_type):
                            errors.append(f"NESTED TYPE: {parent_key}[{k!r}].{child_key} expected {expected_type.__name__}, got {type(val).__name__}")
                    elif isinstance(parent, list) and len(v) == 1:
                        pass  # handled below for lists
            elif isinstance(parent, list):
                for i, item in enumerate(parent):
                    if isinstance(item, dict) and child_key in item:
                        val = item[child_key]
                        if not isinstance(val, expected_type):
                            errors.append(f"NESTED TYPE: {parent_key}[{i}].{child_key} expected {expected_type.__name__}, got {type(val).__name__}")

    # Check invariants
    for inv_name, inv_fn in c.get('invariants', []):
        try:
            if not inv_fn(data):
                errors.append(f"INVARIANT FAILED: {inv_name}")
        except Exception as e:
            errors.append(f"INVARIANT ERROR: {inv_name}: {e}")

    return len(errors) == 0, errors


def run_negative_test(name, mutation):
    """Inject a mutation and confirm validation catches it."""
    data, err = load_contract_data(name)
    if err:
        # Can't test negative on missing file - use golden fixture instead
        data = _golden_fixture(name)

    mutated = copy.deepcopy(data)
    apply_mutation(mutated, mutation)
    passed, errors = validate_contract(name, data=mutated)
    return not passed, errors  # (drift_detected, errors)


def _golden_fixture(name):
    """Return a minimal valid fixture for each contract."""
    fixtures = {
        'goal_ledger': {
            'generated': '2026-11-27', 'source': 'memory/goals', 'evidence_gated': True,
            'fleet_total_goals': 10, 'fleet_reached': 5, 'fleet_pct_reached': 50,
            'agents': {'test': {'total': 5, 'reached': 3, 'open': 2, 'pct_reached': 60, 'goals': []}}
        },
        'fleet_mode': {
            'mode': 'WORK', 'timestamp': '2026-11-27T00:00:00+00:00',
            'goal_pct': 50.0, 'goals_total': 10, 'goals_reached': 5, 'goals_open': 5,
            'fsm_state': 'CONVERGING', 'fsm_validated': True
        },
        'autonomy_score': {
            'score': 50.0, 'fleet_readiness': 40.0,
            'components': {'pass_autonomy': 50, 'duration_score': 60, 'rework_score': 70, 'trend_score': 40},
            'weights': {'a': 0.35, 'b': 0.25, 'c': 0.2, 'd': 0.2},
            'computed_at': '2026-11-27T00:00:00'
        },
        'cockpit_feed': {
            'ts': '2026-11-27T00:00:00',
            'agents': [{'name': 'test', 'state': 'active'}]
        },
        'convergence_velocity': {
            'cycles': {'1': {'velocity': 1.0}}, 'trend': 'stable', 'velocities': [1.0]
        },
    }
    return fixtures[name]


def apply_mutation(data, mutation):
    """Apply a named mutation to test data."""
    if mutation == 'remove_field':
        # Remove first required field
        c = CONTRACTS[mutation_target_for(mutation)]
        first_key = list(c['required'])[0]
        if first_key in data:
            del data[first_key]
    elif mutation == 'wrong_type':
        for key, val in data.items():
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                data[key] = "WRONG_TYPE_STRING"
                break
            elif isinstance(val, str):
                data[key] = 12345
                break
    elif mutation == 'enum_violation':
        for field, allowed in CONTRACTS[mutation_target_for(mutation)].get('enum_rules', {}).items():
            if field in data:
                data[field] = "INVALID_ENUM_VALUE"
                break
    elif mutation == 'weights_sum':
        if 'weights' in data:
            data['weights'] = {'a': 0.9, 'b': 0.9, 'c': 0.9, 'd': 0.9}  # sums to 3.6
    elif mutation == 'score_range':
        if 'score' in data:
            data['score'] = 150.0  # out of range


def mutation_target_for(mutation):
    """Map a generic mutation name to the contract it targets."""
    mapping = {
        'remove_field': 'goal_ledger',
        'wrong_type': 'fleet_mode',
        'enum_violation': 'fleet_mode',
        'weights_sum': 'autonomy_score',
        'score_range': 'autonomy_score',
    }
    return mapping.get(mutation, 'goal_ledger')


def self_test():
    """Run all positive + negative tests. Returns (pass_count, fail_count)."""
    results = []

    # Positive: golden fixtures should pass
    for name in CONTRACTS:
        fixture = _golden_fixture(name)
        passed, errors = validate_contract(name, data=fixture)
        results.append(('POS', name, passed, errors))

    # Negative: mutations should be caught
    negative_cases = [
        ('remove_field', 'goal_ledger'),
        ('wrong_type', 'fleet_mode'),
        ('enum_violation', 'fleet_mode'),
        ('weights_sum', 'autonomy_score'),
        ('score_range', 'autonomy_score'),
    ]
    for mutation, target in negative_cases:
        data = _golden_fixture(target)
        mutated = copy.deepcopy(data)
        apply_mutation(mutated, mutation)
        passed, errors = validate_contract(target, data=mutated)
        drift_detected = not passed
        results.append(('NEG', f"{target}/{mutation}", drift_detected, errors))

    # Live: validate actual files (informational - may fail if files absent/stale)
    for name in CONTRACTS:
        data, err = load_contract_data(name)
        if err:
            results.append(('LIVE', name, None, [err]))  # None = skip
        else:
            passed, errors = validate_contract(name, data=data)
            results.append(('LIVE', name, passed, errors))

    # Report
    pos_pass = sum(1 for k, n, p, _ in results if k == 'POS' and p)
    pos_total = sum(1 for k, _, _, _ in results if k == 'POS')
    neg_pass = sum(1 for k, n, p, _ in results if k == 'NEG' and p)
    neg_total = sum(1 for k, _, _, _ in results if k == 'NEG')

    print(f"Cross-Lane Contract Tests - {datetime.now().isoformat()}")
    print(f"  Contracts defined: {len(CONTRACTS)}")
    print(f"  Positive (golden fixtures): {pos_pass}/{pos_total} PASS")
    for k, n, p, errs in results:
        if k == 'POS' and not p:
            print(f"    FAIL {n}: {errs[:3]}")
    print(f"  Negative (drift detection): {neg_pass}/{neg_total} DETECTED")
    for k, n, p, errs in results:
        if k == 'NEG' and not p:
            print(f"    MISS {n}: mutation not caught!")
    live_results = [(n, p, e) for k, n, p, e in results if k == 'LIVE']
    live_pass = sum(1 for _, p, _ in live_results if p)
    live_total = sum(1 for _, p, _ in live_results if p is not None)
    print(f"  Live (actual files): {live_pass}/{live_total} PASS")
    for n, p, errs in live_results:
        status = 'PASS' if p else ('SKIP' if p is None else 'FAIL')
        detail = f" ({errs[:2]})" if errs and not p else ''
        print(f"    {status} {n}{detail}")

    all_pass = (pos_pass == pos_total) and (neg_pass == neg_total)
    print(f"\n  RESULT: {'PASS' if all_pass else 'FAIL'}")
    return pos_pass + neg_pass, (pos_total - pos_pass) + (neg_total - neg_pass)


def main():
    if '--self-test' in sys.argv:
        p, f = self_test()
        sys.exit(0 if f == 0 else 1)
    elif '--live' in sys.argv:
        for name in CONTRACTS:
            passed, errors = validate_contract(name)
            status = 'PASS' if passed else 'FAIL'
            print(f"{status} {name}: {'; '.join(errors[:3]) if errors else 'ok'}")
    else:
        self_test()


if __name__ == '__main__':
    main()