"""API Contract Test Suite (cycle-8 Goal #3).

Loads per-endpoint JSON schemas from memory/verifier/api-contracts/*.json and
validates live /api/* responses against them. Live leg degrades gracefully when
the portal is unreachable from this seat (egress wall -> NEEDS-HUMAN in
memory/ops/blockers.md). Static + negative legs always run.

Usage:
  python memory/verifier/api_contracts.py --static     # validate schema files only
  python memory/verifier/api_contracts.py --negative   # validator-correctness tests
  python memory/verifier/api_contracts.py              # live (needs :8099)
Exit: 0=all pass, 1=failures, 2=portal unreachable (live mode only).
"""
import json, sys, os, time, urllib.request, urllib.error
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
CONTRACT_DIR = os.path.join(HERE, "api-contracts")

def load_contracts() -> Dict[str, dict]:
    """Load every <endpoint>.json from the contract dir (skip manifest.json)."""
    out = {}
    for fn in sorted(os.listdir(CONTRACT_DIR)):
        if not fn.endswith(".json") or fn == "manifest.json":
            continue
        ep = fn[:-5]
        with open(os.path.join(CONTRACT_DIR, fn), encoding="utf-8") as f:
            spec = json.load(f)
        out[ep] = spec.get("schema", {})
    return out

VALID_TYPES = ("object", "array", "string", "number", "integer", "boolean", "null")

def validate(instance: Any, schema: dict, path: str = "$") -> List[str]:
    """Minimal JSON-Schema subset validator. Returns error list (empty=pass)."""
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
        if expected and not isinstance(instance, expected):
            if stype == "integer" and isinstance(instance, bool):
                errors.append(f"{path}: expected integer, got bool")
            else:
                errors.append(f"{path}: expected {stype}, got {type(instance).__name__}")
            return errors
    const = schema.get("const")
    if const is not None and instance != const:
        errors.append(f"{path}: expected const {const!r}, got {instance!r}")
    minimum = schema.get("minimum")
    if minimum is not None and isinstance(instance, (int, float)) and instance < minimum:
        errors.append(f"{path}: {instance} < minimum {minimum}")
    if stype == "object":
        for req in schema.get("required", []):
            if req not in instance:
                errors.append(f"{path}: missing required key '{req}'")
        for key, sub in schema.get("properties", {}).items():
            if key in instance:
                errors.extend(validate(instance[key], sub, f"{path}.{key}"))
    if stype == "array":
        items = schema.get("items")
        if items:
            for i, item in enumerate(instance):
                errors.extend(validate(item, items, f"{path}[{i}]"))
    return errors

def negative_tests() -> List[tuple]:
    """Prove the validator catches deliberate violations (schema-change detection)."""
    gs = {"type": "object", "required": ["ok", "fleet_pct", "agents"],
          "properties": {"ok": {"const": True}, "fleet_pct": {"type": "number"},
                          "agents": {"type": "array",
                                     "items": {"type": "object",
                                               "required": ["agent", "done"]}}}}
    good = {"ok": True, "fleet_pct": 46.0, "agents": [{"agent": "x", "done": 3}]}
    out = []
    e = validate(good, gs)
    out.append(("valid response -> 0 errors", not e, str(e)))
    bad1 = {"ok": True, "fleet_pct": 46.0}  # missing 'agents'
    e = validate(bad1, gs)
    out.append(("missing required key caught", bool(e) and any("agents" in x for x in e), str(e)))
    bad2 = {"ok": True, "fleet_pct": "46", "agents": []}  # wrong type
    e = validate(bad2, gs)
    out.append(("wrong type caught", bool(e) and any("fleet_pct" in x for x in e), str(e)))
    bad3 = {"ok": False, "fleet_pct": 1.0, "agents": []}  # const break
    e = validate(bad3, gs)
    out.append(("const violation caught", bool(e) and any("const" in x for x in e), str(e)))
    bad4 = {"ok": True, "fleet_pct": 1.0, "agents": [{"agent": "x"}]}  # nested missing
    e = validate(bad4, gs)
    out.append(("nested item violation caught", bool(e) and any("done" in x for x in e), str(e)))
    return out