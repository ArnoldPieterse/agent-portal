#!/usr/bin/env python3
"""Cross-lane DATA-contract tests (ASSIST Verifier goal #4, owner: Verifier).

Verifier's existing api_contracts.py / contract_test.py cover HTTP /api/*
ENDPOINT responses. This suite adds the FILE-BASED inter-agent data contracts
the goal names explicitly (goal_ledger schema, convergence_api response shape,
+ roster / forecast-queue / fleet-mode) that lanes exchange on disk. These are
the "cross-lane" surface: one lane writes, another reads.

Contract AC (Verifier goal #4):
  - 5 contracts defined with golden fixtures          -> CONTRACTS below + api-contracts/golden/*.json
  - all pass on current state                         -> run_current()
  - injected schema drift fails correctly             -> run_drift() proves each contract has teeth

Usage:
  python memory/verifier/cross_lane_contract_tests.py
Exit: 0 = all 5 pass current-state AND all 5 drift injections correctly fail.
       1 = any current-state FAIL, or any drift injection did NOT fail (no teeth).

Self-contained: no network, no dependency on unreachable seats. Resolves repo
root from __file__ so it runs from any CWD.
"""
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # .../AgentPortal
GOLDEN_DIR = ROOT / "memory" / "verifier" / "api-contracts" / "golden"
RESULTS_PATH = ROOT / "memory" / "verifier" / "cross_lane_contract_results.json"

# ---------------------------------------------------------------------------
# Minimal JSON-Schema-subset validator (consistent with api_contracts.py).
# Supports: type, required, properties, items, minItems, minProperties,
#           minimum, maximum, const, enum, additionalProperties(schema), oneOf.
# Returns a list of error strings; empty list == valid.
# ---------------------------------------------------------------------------
def validate(instance, schema, path="$"):
    errors = []
    if "oneOf" in schema:
        for sub in schema["oneOf"]:
            if not validate(instance, sub, path):
                return []
        errors.append(f"{path}: does not match any oneOf variant")
        return errors

    stype = schema.get("type")
    if stype:
        tmap = {"object": dict, "array": list, "string": str,
                "integer": int, "number": (int, float), "boolean": bool}
        expected = tmap.get(stype)
        if expected is not None and not isinstance(instance, expected):
            if stype == "integer" and isinstance(instance, bool):
                errors.append(f"{path}: expected integer, got bool")
            elif stype == "number" and isinstance(instance, bool):
                errors.append(f"{path}: expected number, got bool")
            else:
                errors.append(f"{path}: expected {stype}, got {type(instance).__name__}")
            return errors

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}, got {instance!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} not in enum {schema['enum']}")
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: {instance} < minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}: {instance} > maximum {schema['maximum']}")

    if isinstance(instance, dict):
        for req in schema.get("required", []):
            if req not in instance:
                errors.append(f"{path}: missing required key '{req}'")
        props = schema.get("properties", {})
        for k, sub in props.items():
            if k in instance:
                errors.extend(validate(instance[k], sub, f"{path}.{k}"))
        addl = schema.get("additionalProperties")
        if isinstance(addl, dict):
            for k, v in instance.items():
                if k not in props:
                    errors.extend(validate(v, addl, f"{path}.{k}"))
        if "minProperties" in schema and len(instance) < schema["minProperties"]:
            errors.append(f"{path}: {len(instance)} properties < minProperties {schema['minProperties']}")

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: {len(instance)} items < minItems {schema['minItems']}")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for i, v in enumerate(instance):
                errors.extend(validate(v, item_schema, f"{path}[{i}]"))

    return errors


# ---------------------------------------------------------------------------
# Source loaders (one per contract). Each returns the CURRENT real payload.
# ---------------------------------------------------------------------------
def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def src_agents():
    return load_json(ROOT / "agents.json")


def src_ledger():
    return load_json(ROOT / "goal_ledger.json")


def src_next10():
    return load_json(ROOT / "memory" / "goals" / "next10.json")


def src_convergence():
    # Live-computed from this lane's convergence_api (no network).
    sys.path.insert(0, str(ROOT / "memory" / "builder"))
    import convergence_api as ca
    return ca.handle_convergence()


def src_fleet_mode():
    return load_json(ROOT / "memory" / "fleet-mode.json")


# ---------------------------------------------------------------------------
# The 5 cross-lane contracts.
# drift = fn(payload) -> mutated deep-copy that MUST violate the schema.
# ---------------------------------------------------------------------------
def _drop_key(p, key):
    m = copy.deepcopy(p)
    m.pop(key, None)
    return m


CONTRACTS = [
    {
        "id": "C1_agents_roster",
        "name": "agents.json roster (every lane reads the seat registry)",
        "source": src_agents,
        "schema": {
            "type": "object",
            "required": ["agents"],
            "properties": {
                "agents": {
                    "type": "array", "minItems": 1,
                    "items": {
                        "type": "object",
                        "required": ["id", "name", "model_id"],
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "model_id": {"type": "string"},
                        },
                    },
                }
            },
        },
        "drift_desc": "drop required top-level key 'agents'",
        "drift": lambda p: _drop_key(p, "agents"),
    },
    {
        "id": "C2_goal_ledger_ssot",
        "name": "goal_ledger.json SSOT ledger (all lanes write/read)",
        "source": src_ledger,
        "schema": {
            "type": "object",
            "required": ["generated", "source", "evidence_gated",
                          "fleet_total_goals", "fleet_reached", "fleet_pct_reached", "agents"],
            "properties": {
                "generated": {"type": "string"},
                "source": {"type": "string"},
                "evidence_gated": {"type": "boolean"},
                "fleet_total_goals": {"type": "integer", "minimum": 1},
                "fleet_reached": {"type": "integer", "minimum": 0},
                "fleet_pct_reached": {"type": "integer", "minimum": 0, "maximum": 100},
                "agents": {
                    "type": "object", "minProperties": 1,
                    "additionalProperties": {
                        "type": "object",
                        "required": ["total", "reached", "pct_reached", "goals"],
                        "properties": {
                            "total": {"type": "integer", "minimum": 0},
                            "reached": {"type": "integer", "minimum": 0},
                            "pct_reached": {"type": "integer", "minimum": 0, "maximum": 100},
                            "goals": {"type": "array"},
                        },
                    },
                },
            },
        },
        "drift_desc": "fleet_pct_reached -> 150 (violates maximum 100)",
        "drift": lambda p: (lambda m: (m.update({"fleet_pct_reached": 150}), m)[1])(copy.deepcopy(p)),
    },
    {
        "id": "C3_next10_forecast_queue",
        "name": "next10.json forecast queue (forecast engine -> all lanes)",
        "source": src_next10,
        "schema": {
            "type": "object",
            "required": ["ok", "generated", "fleet", "next10", "horizons"],
            "properties": {
                "ok": {"type": "boolean"},
                "generated": {"type": "string"},
                "fleet": {"type": "object"},
                "throughput_goals_per_hour": {"type": "number"},
                "next10": {"type": "array", "minItems": 1},
                "horizons": {"type": "array"},
            },
        },
        "drift_desc": "next10 -> string (violates array type)",
        "drift": lambda p: (lambda m: (m.update({"next10": "not-a-list"}), m)[1])(copy.deepcopy(p)),
    },
    {
        "id": "C4_convergence_api_response",
        "name": "convergence_api.handle_convergence() response shape (Designer/Verifier/Mechanic consume)",
        "source": src_convergence,
        "schema": {
            "type": "object",
            "required": ["ok", "timestamp", "autonomy", "efficiency",
                          "interventions", "steady_state", "cycle_history"],
            "properties": {
                "ok": {"const": True},
                "timestamp": {"type": "string"},
                "autonomy": {
                    "type": "object", "required": ["score", "components", "trend"],
                    "properties": {
                        "score": {"type": "number"},
                        "components": {"type": "object"},
                        "trend": {"type": "string", "enum": ["improving", "stable", "declining"]},
                    },
                },
                "efficiency": {
                    "type": "object", "required": ["current", "delta_vs_last", "trend"],
                },
                "interventions": {
                    "type": "object", "required": ["total", "by_type", "per_cycle_avg"],
                    "properties": {"total": {"type": "integer"}},
                },
                "steady_state": {
                    "type": "object", "required": ["mode", "progress_pct", "criteria_met", "criteria_total"],
                    "properties": {"criteria_total": {"const": 3}},
                },
                "cycle_history": {"type": "array"},
            },
        },
        "drift_desc": "autonomy.trend -> 'exploding' (not in enum)",
        "drift": lambda p: (lambda m: (m["autonomy"].update({"trend": "exploding"}), m)[1])(copy.deepcopy(p)),
    },
    {
        "id": "C5_fleet_mode_state",
        "name": "fleet-mode.json mode/state (convergence_api writes, cockpit reads)",
        "source": src_fleet_mode,
        "schema": {
            "type": "object",
            "required": ["mode", "timestamp", "goal_pct"],
            "properties": {
                "mode": {"type": "string", "enum": ["WORK", "REVIEW", "IDLE", "MAINTENANCE", "STEADY_STATE"]},
                "timestamp": {"type": "string"},
                "goal_pct": {"type": "number", "minimum": 0, "maximum": 100},
            },
        },
        "drift_desc": "goal_pct -> -5 (violates minimum 0)",
        "drift": lambda p: (lambda m: (m.update({"goal_pct": -5}), m)[1])(copy.deepcopy(p)),
    },
]


def main():
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    all_current_pass = True
    all_drift_caught = True

    for c in CONTRACTS:
        # --- current state ---
        try:
            payload = c["source"]()
        except Exception as e:  # source itself broken => contract FAIL
            rows.append({"id": c["id"], "name": c["name"],
                         "current": "ERROR", "current_errors": [f"source raised: {e}"],
                         "drift_caught": False, "drift_desc": c["drift_desc"]})
            all_current_pass = False
            all_drift_caught = False
            continue

        cur_errors = validate(payload, c["schema"])
        cur_ok = not cur_errors
        all_current_pass = all_current_pass and cur_ok

        # --- golden fixture (snapshot of current real payload) ---
        try:
            (GOLDEN_DIR / f"{c['id']}.json").write_text(
                json.dumps(payload, indent=2), encoding="utf-8")
            golden_written = True
        except Exception as e:
            golden_written = False

        # --- injected drift must be caught ---
        mutated = c["drift"](payload)
        drift_errors = validate(mutated, c["schema"])
        drift_caught = bool(drift_errors)
        all_drift_caught = all_drift_caught and drift_caught

        rows.append({
            "id": c["id"],
            "name": c["name"],
            "current": "PASS" if cur_ok else "FAIL",
            "current_errors": cur_errors,
            "golden_written": golden_written,
            "drift_caught": drift_caught,
            "drift_desc": c["drift_desc"],
            "drift_errors_sample": drift_errors[:3],
        })

    passed = all_current_pass and all_drift_caught
    report = {
        "ok": passed,
        "generated": datetime.now(timezone.utc).isoformat(),
        "owner": "verifier",
        "assist_by": "builder",
        "goal": "Verifier goal #4 - cross-lane contract tests (file-based data contracts)",
        "contracts_total": len(CONTRACTS),
        "current_pass": sum(1 for r in rows if r["current"] == "PASS"),
        "drift_caught": sum(1 for r in rows if r.get("drift_caught")),
        "all_current_pass": all_current_pass,
        "all_drift_caught": all_drift_caught,
        "rows": rows,
    }
    RESULTS_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # --- human/console report ---
    print("CROSS-LANE CONTRACT TESTS  (owner: Verifier / assist: Builder)")
    print(f"generated: {report['generated']}")
    print("-" * 72)
    for r in rows:
        cur = r["current"]
        dc = "CAUGHT" if r.get("drift_caught") else "MISSED"
        print(f"[{cur:4}] {r['id']:<32} drift({dc}): {r['drift_desc']}")
        for e in r["current_errors"][:5]:
            print(f"         current ERR: {e}")
        if not r.get("drift_caught"):
            print("         !! drift NOT caught - contract has no teeth here")
    print("-" * 72)
    print(f"current-state pass : {report['current_pass']}/{len(CONTRACTS)}")
    print(f"drift correctly fail: {report['drift_caught']}/{len(CONTRACTS)}")
    print(f"RESULTS -> {RESULTS_PATH.relative_to(ROOT)}")
    print(f"GOLDEN  -> {GOLDEN_DIR.relative_to(ROOT)}/<id>.json")
    print(f"\nOVERALL: {'PASS' if passed else 'FAIL'}")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
