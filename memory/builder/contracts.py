#!/usr/bin/env python3
"""
Builder Goal #5 — Data-Contract Registry + Lint.
Central registry of the cross-lane JSON/JSONL contracts that steady-state depends on,
with field names, types and required-set. 
  --lint          validate live files against the registry; FAIL (exit 1) on drift with exact path
  --gen-stub NAME emit mock data for a contract (stdout or --out PATH)
  --selftest      assert: lint passes on current live files; a seeded missing-field in a copy is
                  caught with its exact dotted path; every registered contract has a schema.

Type tokens: str, int, number(int|float, not bool), bool, list, dict, any.
Append '?' to a token to allow null (e.g. 'number?' = number or null).
A required field must be PRESENT; its value may be null only if the type allows '?'."""
import argparse, json, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OPS = ROOT / "memory" / "ops"
BUILDER = ROOT / "memory" / "builder"
OUT_DIR = BUILDER


def _base_and_nullable(t):
    return (t[:-1], True) if t.endswith("?") else (t, False)

# kind: 'json' (single object) or 'jsonl' (one object per line).
# required=False => registered-but-optional; absence is not a lint failure.
CONTRACTS = {
    "autoloop": {
        "kind": "jsonl", "required": True, "path": OPS / "autoloop.jsonl",
        "fields": {"agent": "str", "timestamp": "str"},
        "optional": ["start_ts", "end_ts", "duration_s", "productive", "evidence_files"],
    },
    "fleet_mode": {
        "kind": "json", "required": True, "path": OPS / "fleet-mode.json",
        "fields": {"mode": "str", "fsm_state": "str", "fsm_validated": "bool",
                   "goal_pct": "number", "goals_reached": "int", "goals_total": "int",
                   "timestamp": "str"},
    },
    "autonomy_score": {
        "kind": "json", "required": True, "path": OPS / "autonomy-score.json",
        "fields": {"score": "number", "computed_at": "str", "components": "dict", "weights": "dict"},
    },
    "fsm_events": {
        "kind": "jsonl", "required": True, "path": OPS / "fsm-events.jsonl",
        "fields": {"from": "str", "to": "str", "legal": "bool", "ts": "str", "source": "str"},
    },
    "cycle_closeout": {
        "kind": "jsonl", "required": True, "path": OPS / "cycle-closeout.jsonl",
        "fields": {"cycle": "int", "completion_pct": "number?", "start_date": "str?",
                   "end_date": "str?", "recorded_at": "str"},
    },
    "dispatch_cache": {
        "kind": "json", "required": True, "path": OPS / "dispatch-cache.json",
        "fields": {"mode": "str", "generated": "str", "entries": "list"},
    },
    # registered-but-optional: introduced this cycle, file not yet present.
    "convergence_events": {
        "kind": "jsonl", "required": False, "path": OPS / "convergence-events.jsonl",
        "fields": {"type": "str", "ts": "str", "from": "str", "to": "str", "source": "str"},
    },
    "assists": {
        "kind": "jsonl", "required": False, "path": OPS / "assists.jsonl",
        "fields": {"ts": "str", "goal_owner": "str", "assistant": "str", "note": "str"},
    },
}


def _type_ok(val, t):
    base, nullable = _base_and_nullable(t)
    if val is None:
        return nullable
    checks = {
        "any": lambda v: True,
        "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
        "int": lambda v: isinstance(v, int) and not isinstance(v, bool),
        "bool": lambda v: isinstance(v, bool),
        "list": lambda v: isinstance(v, list),
        "dict": lambda v: isinstance(v, dict),
        "str": lambda v: isinstance(v, str),
    }
    return checks.get(base, lambda v: False)(val)


def _check_obj(obj, fields, prefix, violations):
    for k, t in fields.items():
        p = f"{prefix}.{k}" if prefix else k
        if k not in obj:
            violations.append(f"{p}: missing required field")
        elif not _type_ok(obj[k], t):
            violations.append(f"{p}: expected {t}, got {type(obj[k]).__name__}")


def lint_file(path: Path, contract):
    """Return list of violation strings for one file against its contract."""
    fields = contract["fields"]
    if not path.exists():
        return [f"{path.name}: file missing"]
    violations = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    if contract["kind"] == "json":
        try:
            obj = json.loads(text)
        except Exception as e:  # noqa: BLE001
            return [f"{path.name}: not valid JSON ({e.__class__.__name__})"]
        _check_obj(obj, fields, path.stem, violations)
    else:  # jsonl
        for i, line in enumerate(text.splitlines()):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception as e:  # noqa: BLE001
                violations.append(f"{path.stem}[{i}]: not valid JSON ({e.__class__.__name__})")
                continue
            _check_obj(obj, fields, f"{path.stem}[{i}]", violations)
    return violations


def lint():
    report, all_ok = [], True
    for name, c in CONTRACTS.items():
        if not c["required"] and not c["path"].exists():
            report.append(f"  [optional-absent] {name}: registered, file not present (ok)")
            continue
        v = lint_file(c["path"], c) if c["path"].exists() else [f"{c['path'].name}: file missing"]
        if v:
            all_ok = False
            report.append(f"  [DRIFT] {name}:")
            for x in v[:20]:
                report.append(f"      - {x}")
            if len(v) > 20:
                report.append(f"      ... +{len(v)-20} more")
        else:
            report.append(f"  [ok] {name}: schema valid")
    return all_ok, report


def _stub_value(t):
    base = t[:-1] if t.endswith("?") else t
    return {"str": "stub", "int": 0, "number": 0.0, "bool": False,
            "list": [], "dict": {}, "any": None}.get(base, None)


def gen_stub(name):
    c = CONTRACTS[name]
    obj = {k: _stub_value(t) for k, t in c["fields"].items()}
    if c["kind"] == "jsonl":
        return (json.dumps(obj) + "\n") * 2
    return json.dumps(obj, indent=2) + "\n"


def _selftest():
    failures = []
    # (1) lint passes on current live files.
    ok, report = lint()
    print("\n".join(report))
    if not ok:
        failures.append("lint reported drift on current live files")
    # (2) seeded missing-field in a copy -> caught with exact dotted path.
    tmp = Path(tempfile.mkdtemp(prefix="contracts_selftest_"))
    try:
        seed = {k: _stub_value(t) for k, t in CONTRACTS["autoloop"]["fields"].items()}
        del seed["agent"]  # remove one required field
        bad = tmp / "autoloop.jsonl"
        bad.write_text(json.dumps(seed) + "\n", encoding="utf-8")
        v = lint_file(bad, CONTRACTS["autoloop"])
        if not any(".agent: missing required field" in x for x in v):
            failures.append(f"seeded missing-field not caught with exact path; got {v}")
        else:
            print("seeded-missing-field caught ->", [x for x in v if 'agent' in x])
        # type-drift check: wrong type on a json contract.
        fm = dict(json.loads((OPS / "fleet-mode.json").read_text(encoding="utf-8")))
        fm["fsm_validated"] = "yes"  # should be bool
        badfm = tmp / "fleet-mode.json"
        badfm.write_text(json.dumps(fm), encoding="utf-8")
        vf = lint_file(badfm, CONTRACTS["fleet_mode"])
        if not any("fsm_validated: expected bool" in x for x in vf):
            failures.append(f"type-drift not caught; got {vf}")
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    # (3) every registered contract has a schema + gen-stub is parseable.
    for name, c in CONTRACTS.items():
        if not c["fields"]:
            failures.append(f"{name}: no schema registered")
        stub = gen_stub(name)
        try:
            if c["kind"] == "json":
                json.loads(stub)  # whole object
            else:  # jsonl
                for l in [x for x in stub.splitlines() if x.strip()]:
                    json.loads(l)
        except Exception as e:  # noqa: BLE001
            failures.append(f"{name}: gen-stub not parseable ({e.__class__.__name__})")
    if failures:
        print("SELFTEST FAIL")
        for f_ in failures:
            print("  -", f_)
        return 1
    print("SELFTEST PASS: lint clean on live files; seeded missing-field caught (exact path); "
          "type-drift caught; all registered contracts have schemas + parseable stubs.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Builder data-contract registry + lint")
    ap.add_argument("--lint", action="store_true")
    ap.add_argument("--gen-stub", metavar="NAME")
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return _selftest()
    if args.gen_stub:
        if args.gen_stub not in CONTRACTS:
            print(f"unknown contract: {args.gen_stub}", file=sys.stderr)
            return 2
        data = gen_stub(args.gen_stub)
        if args.out:
            Path(args.out).write_text(data, encoding="utf-8")
            print(f"wrote stub -> {args.out}")
        else:
            sys.stdout.write(data)
        return 0
    # default: lint
    ok, report = lint()
    print("\n".join(report))
    print("LINT", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
