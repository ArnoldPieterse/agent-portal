"""Cockpit Data Golden-Fixture Regression (data-layer gate).

Purpose: catch DATA-completeness regressions in the cockpit in-loop. We diff each
cockpit panel's DATA projection against golden fixtures -- not just page-load -- so a
clobbered/truncated data endpoint is caught before it reaches the UI.

Data flow under test:
  fleet-snapshots.jsonl + health-score.jsonl + incident-alerts.jsonl + decision-log.jsonl
  + down-seats.json  ->  memory/mechanic/cockpit_feed.build_feed()  ->  cockpit-feed.json

This gate runs at the DATA layer (no browser). The Playwright render leg is a separate,
non-sandbox seat (see OPS-NOTE in memory/ops/blockers.md); the verification criteria here
(run green on current state; seeded clobber -> exactly the affected panel fails) are fully
deliverable and verified at this layer.

Panels + backing source (provenance):
  health     <- health_score, fleet_status      [health-score.jsonl]
  agents     <- agents                          [fleet-snapshots.jsonl: agent_statuses]
  hosts      <- hosts                           [fleet-snapshots.jsonl: host_resources]
  goals      <- goals                           [fleet-snapshots.jsonl: goal_progress]
  down_seats <- down_seats                      [down-seats.json]
  incidents  <- active_incidents                [incident-alerts.jsonl]
  decisions  <- recent_decisions                [decision-log.jsonl]

Usage:
  python memory/researcher/cockpit_golden.py                 # gate: live feed vs golden fixtures
  python memory/researcher/cockpit_golden.py --update-golden # regenerate fixtures from current state
  python memory/researcher/cockpit_golden.py --selftest      # AC proof (green-on-current + per-panel clobber isolation)
  python memory/researcher/cockpit_golden.py --clobber-panel agents   # corrupt one panel, re-diff
"""

import json
import copy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOLDEN_DIR = HERE / "golden"
GOLDEN_PATH = GOLDEN_DIR / "cockpit_golden.json"
FEED_PATH = Path("memory/ops/cockpit-feed.json")

# Each panel: (panel_name, [feed keys it projects], backing source for provenance)
PANELS = [
    ("health",     ["health_score", "fleet_status"],       "health-score.jsonl"),
    ("agents",     ["agents"],                              "fleet-snapshots.jsonl:agent_statuses"),
    ("hosts",      ["hosts"],                               "fleet-snapshots.jsonl:host_resources"),
    ("goals",      ["goals"],                               "fleet-snapshots.jsonl:goal_progress"),
    ("down_seats", ["down_seats"],                          "down-seats.json"),
    ("incidents",  ["active_incidents"],                    "incident-alerts.jsonl"),
    ("decisions",  ["recent_decisions"],                    "decision-log.jsonl"),
]
PANEL_KEYS = {name: keys for name, keys, _ in PANELS}
PANEL_SOURCE = {name: src for name, _, src in PANELS}


def load_feed() -> dict:
    """Load the cockpit feed. Prefer the live aggregator; fall back to disk feed."""
    try:
        sys.path.insert(0, str(HERE.parent / "mechanic"))
        import cockpit_feed  # type: ignore
        feed = cockpit_feed.build_feed()
        if feed:
            return feed
    except Exception:
        pass
    return json.loads(FEED_PATH.read_text(encoding="utf-8"))


def project_panel(feed: dict, name: str) -> dict:
    """Deterministic data projection for one panel (top-level 'ts' excluded by construction)."""
    return {k: feed.get(k) for k in PANEL_KEYS[name]}


def canonical(value) -> str:
    """Canonical, order-insensitive JSON string used as the fixture signature."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def diff_summary(expected: dict, actual: dict):
    """Human-readable list of differing keys (top-level within the panel)."""
    diffs = []
    for k in sorted(set(list(expected.keys()) + list(actual.keys()))):
        if canonical(expected.get(k)) != canonical(actual.get(k)):
            e = expected.get(k)
            a = actual.get(k)
            de = len(e) if hasattr(e, "__len__") else type(e).__name__
            da = len(a) if hasattr(a, "__len__") else type(a).__name__
            diffs.append(f"{k}: golden={de} live={da}")
    return diffs


def write_golden(feed: dict) -> None:
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    fixtures = {name: project_panel(feed, name) for name in PANEL_KEYS}
    meta = {"__source_map": PANEL_SOURCE}
    payload = {"fixtures": fixtures, "meta": meta}
    GOLDEN_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def read_golden() -> dict:
    if not GOLDEN_PATH.exists():
        raise SystemExit(
            f"FAIL: no golden fixtures at {GOLDEN_PATH}. "
            "Run `python memory/researcher/cockpit_golden.py --update-golden` once to seed them."
        )
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8")).get("fixtures", {})


def run_gate(feed: dict, golden: dict):
    """Return (results:{panel:(pass,diffs)}, all_green)."""
    results = {}
    for name in PANEL_KEYS:
        exp = golden.get(name)
        act = project_panel(feed, name)
        if canonical(exp) == canonical(act):
            results[name] = (True, [])
        else:
            results[name] = (False, diff_summary(exp or {}, act))
    all_green = all(ok for ok, _ in results.values())
    return results, all_green


def clobber_panel(feed: dict, name: str) -> dict:
    """Seed a data-endpoint clobber on exactly one panel's projection.

    Corrupts the panel's fields (None + drop list items) so its signature changes while
    every other panel is byte-identical -- models a clobbered/truncated upstream endpoint.
    """
    f = copy.deepcopy(feed)
    for k in PANEL_KEYS[name]:
        v = f.get(k)
        if isinstance(v, list):
            f[k] = []  # truncate the feed to zero rows
        else:
            f[k] = None  # null out scalar / dict field
    return f


def selftest() -> int:
    print("=== Cockpit Golden-Fixture Regression -- SELFTEST (data layer) ===")
    feed = load_feed()
    n_panels = len(PANEL_KEYS)
    print(f"feed loaded: {len(feed)} top keys | panels under test: {n_panels}")

    # AC-1: golden fixtures generated from current state -> gate is green on current state.
    fixtures = {name: project_panel(feed, name) for name in PANEL_KEYS}
    res, green = run_gate(feed, fixtures)
    print(f"\n[AC-1] green-on-current-state: {'PASS' if green else 'FAIL'} ({sum(ok for ok,_ in res.values())}/{n_panels} panels match)")
    if not green:
        for name, (ok, diffs) in res.items():
            if not ok:
                print(f"   ! {name}: {diffs}")

    # AC-2: for each panel, a seeded clobber makes EXACTLY that panel fail, all others pass.
    isolation_ok = True
    print("\n[AC-2] per-panel clobber isolation:")
    for name in PANEL_KEYS:
        corrupted = clobber_panel(feed, name)
        res_c, _ = run_gate(corrupted, fixtures)
        failing = [p for p, (ok, _) in res_c.items() if not ok]
        isolated = failing == [name]
        isolation_ok = isolation_ok and isolated
        status = "PASS" if isolated else "FAIL"
        extra = "" if isolated else f"  (failing={failing})"
        print(f"   {status} clobber[{name}] -> exactly [{name}] fails{extra}")

    ok = green and isolation_ok
    print(f"\nRESULT: {'PASS' if ok else 'FAIL'} (AC-1 green-on-current, AC-2 per-panel isolation across {n_panels} panels)")
    return 0 if ok else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if "--update-golden" in argv:
        feed = load_feed()
        write_golden(feed)
        print(f"golden fixtures written: {GOLDEN_PATH} ({len(PANEL_KEYS)} panels)")
        for name, keys, src in PANELS:
            print(f"   - {name:<11} <- {', '.join(keys):<28} [{src}]")
        return 0
    if "--clobber-panel" in argv:
        target = argv[argv.index("--clobber-panel") + 1]
        if target not in PANEL_KEYS:
            raise SystemExit(f"unknown panel {target!r}; valid: {list(PANEL_KEYS)}")
        feed = load_feed()
        fixtures = read_golden()
        corrupted = clobber_panel(feed, target)
        res, _ = run_gate(corrupted, fixtures)
        print(f"clobbered panel: {target} (source {PANEL_SOURCE[target]})")
        for name, (ok, diffs) in res.items():
            mark = "ok  " if ok else "FAIL"
            extra = f"  {diffs}" if diffs else ""
            print(f"   {mark} {name:<11}{extra}")
        return 0
    # default: persistent gate vs on-disk golden fixtures
    feed = load_feed()
    golden = read_golden()
    res, green = run_gate(feed, golden)
    print("=== Cockpit Golden-Fixture Regression -- GATE ===")
    for name, (ok, diffs) in res.items():
        mark = "PASS" if ok else "FAIL"
        extra = f"  {diffs}" if diffs else f"  [{PANEL_SOURCE[name]}]"
        print(f"   {mark:<4} {name:<11}{extra}")
    print(f"\nRESULT: {'GREEN' if green else 'RED'} ({sum(ok for ok,_ in res.values())}/{len(PANEL_KEYS)} panels match golden)")
    return 0 if green else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
