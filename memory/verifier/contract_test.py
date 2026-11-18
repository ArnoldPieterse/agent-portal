#!/usr/bin/env python3
"""API Contract Tests - validates live /api/* responses against JSON Schemas.

Usage: python memory/verifier/contract_test.py [--port 8099] [--endpoint /api/goals]

Exit codes:
  0 = all tested endpoints pass contract
  1 = one or more endpoints fail (details printed)
  2 = portal unreachable
"""
import json, sys, time, urllib.request, urllib.error
from typing import Any, Dict, List, Optional

# ─── JSON Schema definitions per endpoint ─────────────────────────────────────
# Each schema describes the MINIMUM required structure. We validate:
#   - top-level type (object/array)
#   - required keys present
#   - key types match
# Schemas are intentionally lenient on nested optional fields; strict on contract keys.

SCHEMAS: Dict[str, dict] = {
    "/api/agents": {
        "type": "object",
        "required": ["agents"],
        "properties": {
            "agents": {"type": "array", "items": {"type": "object", "required": ["name"]}}
        }
    },
    "/api/user-messages": {
        "type": "object",
        "required": ["ok", "messages"],
        "properties": {"ok": {"const": True}, "messages": {"type": "array"}}
    },
    "/api/history": {
        "type": "object",
        "required": ["ok", "history"],
        "properties": {"ok": {"const": True}, "history": {"type": "array"}}
    },
    "/api/autoloop": {
        "type": "object",
        "required": [],  # shape varies; just require valid object
        "properties": {}
    },
    "/api/run-state": {
        "type": "object",
        "required": [],
        "properties": {}
    },
    "/api/models": {
        # proxied from Studio /v1/models - could be list or object
        "oneOf": [{"type": "array"}, {"type": "object"}]
    },
    "/api/status": {
        "oneOf": [{"type": "object"}, {"type": "array"}]
    },
    "/api/fleet": {
        "type": "object",
        "required": ["hosts"],
        "properties": {
            "hosts": {"type": "array", "items": {"type": "object", "required": ["name", "status"]}}
        }
    },
    "/api/perf": {
        "type": "object",
        "required": [],
        "properties": {}
    },
    "/api/health/fleet": {
        "type": "object",
        "required": [],
        "properties": {}
    },
    "/api/fleet/capacity": {
        "type": "object",
        "required": [],
        "properties": {}
    },
    "/api/memory-health": {
        "type": "object",
        "required": ["ok"],
        "properties": {"ok": {"type": "boolean"}}
    },
    "/api/decisions": {
        "oneOf": [{"type": "object"}, {"type": "array"}]
    },
    "/api/git": {
        "type": "object",
        "required": ["ok"],
        "properties": {"ok": {"type": "boolean"}}
    },
    "/api/ops": {
        "type": "object",
        "required": ["hosts"],
        "properties": {
            "hosts": {"type": "array", "items": {"type": "object", "required": ["name"]}}
        }
    },
    "/api/goals": {
        "type": "object",
        "required": ["ok", "fleet_pct", "fleet_done", "fleet_total", "agents"],
        "properties": {
            "ok": {"const": True},
            "generated": {"type": "string"},
            "fleet_pct": {"type": "number"},
            "fleet_done": {"type": "integer", "minimum": 0},
            "fleet_total": {"type": "integer", "minimum": 0},
            "agents": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["agent", "total", "done", "open", "blocked"],
                    "properties": {
                        "agent": {"type": "string"},
                        "total": {"type": "integer", "minimum": 0},
                        "done": {"type": "integer", "minimum": 0},
                        "open": {"type": "integer", "minimum": 0},
                        "blocked": {"type": "integer", "minimum": 0}
                    }
                }
            },
            "goal_reset_pending": {"type": "boolean"}
        }
    },
    "/api/models/status": {
        "type": "object",
        "required": ["ok", "block_mode", "down_seats", "action_required"],
        "properties": {
            "ok": {"const": True},
            "block_mode": {},
            "down_seats": {"type": "array"},
            "action_required": {"type": "boolean"}
        }
    },
    "/api/net/fleet": {
        "oneOf": [{"type": "object"}, {"type": "array"}]
    },
    "/api/provenance": {
        "type": "object",
        "required": ["ok"],
        "properties": {"ok": {"type": "boolean"}}
    },
    "/api/goals/history": {
        "oneOf": [{"type": "object"}, {"type": "array"}]
    },
    "/api/goals/timeline": {
        "type": "object",
        "required": ["ok", "cycles"],
        "properties": {
            "ok": {"const": True},
            "cycles": {"type": "array", "items": {"type": "object", "required": ["date"]}}
        }
    },
    "/api/merge-queue": {
        "oneOf": [{"type": "object"}, {"type": "array"}]
    },
    "/api/evolution/stats": {
        "oneOf": [{"type": "object"}, {"type": "array"}]
    },
    "/api/knowledge-bases": {
        "oneOf": [{"type": "object"}, {"type": "array"}]
    },
    "/api/tools": {
        "type": "object",
        "required": ["local_tools", "reasoning_levels"],
        "properties": {
            "local_tools": {"type": "array"},
            "reasoning_levels": {"type": "array", "items": {"type": "string"}}
        }
    },
    "/api/memory": {
        "type": "object",
        "required": ["text", "infinite_budget", "inter_agent_replies"],
        "properties": {
            "text": {"type": "string"},
            "limit": {},  # null or int
            "infinite_budget": {"type": "boolean"},
            "inter_agent_replies": {"type": "integer"},
            "last_reset_by": {}
        }
    },
    "/api/memory/file": {
        # requires ?path= param; schema for success case
        "oneOf": [
            {"type": "object", "required": ["path", "text"],
             "properties": {"path": {"type": "string"}, "text": {"type": "string"}}},
            {"type": "object", "required": ["error"],
             "properties": {"error": {"type": "string"}}}
        ]
    },
    "/api/activity": {
        "oneOf": [{"type": "array"}, {"type": "object"}]
    },
    "/api/manifest": {
        "type": "object",
        "required": ["count", "files"],
        "properties": {
            "count": {"type": "integer", "minimum": 0},
            "files": {
                "type": "array",
                "items": {"type": "object", "required": ["path", "mtime"],
                          "properties": {"path": {"type": "string"}, "mtime": {"type": "number"}}}
            }
        }
    },
    "/api/uploads": {
        "type": "object",
        "required": ["count", "files"],
        "properties": {
            "count": {"type": "integer", "minimum": 0},
            "files": {
                "type": "array",
                "items": {"type": "object", "required": ["path", "size", "mtime"],
                          "properties": {"path": {"type": "string"},
                                         "size": {"type": "integer"},
                                         "mtime": {"type": "number"}}}
            }
        }
    },
    "/api/file": {
        # requires ?path= param; success or 404
        "oneOf": [
            {"type": "object", "required": ["path", "name", "size"],
             "properties": {"path": {"type": "string"}, "name": {"type": "string"}}},
            {"type": "object", "required": ["error"],
             "properties": {"error": {"type": "string"}}}
        ]
    }
    # /api/file/raw and /api/run-events are non-JSON (raw file / SSE stream) - excluded
}

# Endpoints that need query params to return a valid shape
PARAM_ENDPOINTS = {
    "/api/memory/file": "?path=memory/INDEX.md",
    "/api/file": "?path=agents.json",
    "/api/history": "?mode=group",
}

# ─── Minimal JSON Schema validator (no external deps) ────────────────────────

def validate(instance: Any, schema: dict, path: str = "$") -> List[str]:
    """Validate instance against schema. Returns list of error strings (empty = pass)."""
    errors = []
    if "oneOf" in schema:
        # pass if ANY sub-schema passes
        sub_errors = []
        for i, sub in enumerate(schema["oneOf"]):
            errs = validate(instance, sub, path)
            if not errs:
                return []  # matched one variant
            sub_errors.extend(errs)
        errors.append(f"{path}: does not match any oneOf variant")
        return errors

    stype = schema.get("type")
    if stype:
        type_map = {"object": dict, "array": list, "string": str, "integer": int,
                    "number": (int, float), "boolean": bool}
        expected = type_map.get(stype)
        if expected and not isinstance(instance, expected):
            # special: bool is subclass of int in Python
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
        # validate nested properties (only those present)
        props = schema.get("properties", {})
        for key, sub_schema in props.items():
            if key in instance:
                errors.extend(validate(instance[key], sub_schema, f"{path}.{key}"))

    if stype == "array":
        items_schema = schema.get("items")
        if items_schema:
            for i, item in enumerate(instance):
                errors.extend(validate(item, items_schema, f"{path}[{i}]"))

    return errors

# ─── Main test runner ─────────────────────────────────────────────────────────

def fetch(base: str, endpoint: str, timeout: int = 10) -> tuple:
    """Return (status_code, parsed_json_or_text). Raises on network error."""
    url = base + endpoint
    req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req, timeout=timeout)
    body = resp.read()
    try:
        return resp.status, json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return resp.status, body.decode("utf-8", "replace")

def run_tests(port: int = 8099, only_endpoint: Optional[str] = None) -> int:
    base = f"http://localhost:{port}"
    endpoints = list(SCHEMAS.keys()) if not only_endpoint else [only_endpoint]

    # Check connectivity first
    try:
        status, _ = fetch(base, "/api/goals", timeout=5)
    except Exception as e:
        print(f"FATAL: portal unreachable at {base}: {e}")
        return 2

    passed, failed, skipped = 0, 0, 0
    results = []

    for ep in endpoints:
        full_ep = ep + PARAM_ENDPOINTS.get(ep, "")
        schema = SCHEMAS[ep]
        t0 = time.perf_counter()
        try:
            status, body = fetch(base, full_ep)
        except Exception as e:
            failed += 1
            results.append((ep, "FAIL", f"network error: {e}"))
            continue
        elapsed_ms = (time.perf_counter() - t0) * 1000

        if status != 200:
            failed += 1
            results.append((ep, "FAIL", f"HTTP {status} (expected 200)"))
            continue

        if not isinstance(body, (dict, list)):
            # non-JSON response where we expected JSON
            failed += 1
            results.append((ep, "FAIL", f"response is not JSON: {type(body).__name__}"))
            continue

        errs = validate(body, schema)
        if errs:
            failed += 1
            detail = "; ".join(errs[:5])
            results.append((ep, "FAIL", f"{len(errs)} schema violations: {detail}"))
        else:
            passed += 1
            results.append((ep, "PASS", f"{elapsed_ms:.0f}ms"))

    # Report
    print(f"\n{'='*60}")
    print(f"API CONTRACT TEST - {len(endpoints)} endpoints")
    print(f"{'='*60}")
    for ep, status_str, detail in results:
        icon = "✓" if status_str == "PASS" else "✗"
        print(f"  {icon} {ep:35s} {status_str:4s} {detail}")
    print(f"{'='*60}")
    print(f"  TOTAL: {passed} pass / {failed} fail / {skipped} skip")
    print(f"{'='*60}\n")

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    port = 8099
    only = None
    static = False
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--port" and i+1 < len(args):
            port = int(args[i+1]); i += 2
        elif args[i] == "--endpoint" and i+1 < len(args):
            only = args[i+1]; i += 2
        elif args[i] == "--static":
            static = True; i += 1
        else:
            i += 1
    if static:
        # Static mode: validate schemas are well-formed without hitting the portal.
        print("[STATIC MODE] Validating schema structure (no live requests)\n")
        errors = []
        for path, spec in SCHEMAS.items():
            # Schema is the value itself (or oneOf variants)
            if "oneOf" not in spec and "type" not in spec:
                errors.append(f"{path}: missing 'type' or 'oneOf' in schema")
            else:
                # Check for valid JSON types
                t = spec.get("type")
                if t and t not in ("object","array","string","number","integer","boolean","null"):
                    errors.append(f"{path}: invalid type '{t}'")
                if "oneOf" in spec:
                    for i, sub in enumerate(spec["oneOf"]):
                        st = sub.get("type")
                        if st and st not in ("object","array","string","number","integer","boolean","null"):
                            errors.append(f"{path}: oneOf[{i}] invalid type '{st}'")
        if errors:
            for e in errors:
                print(f"  FAIL: {e}")
            sys.exit(1)
        else:
            print(f"  PASS: all {len(SCHEMAS)} schemas structurally valid")
            print(f"\nSummary: {len(SCHEMAS)} endpoints covered, 0 structural errors")
            sys.exit(0)
    sys.exit(run_tests(port, only))
