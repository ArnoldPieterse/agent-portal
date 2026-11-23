#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
failure_mutation.py - Researcher goal #9: Closed-Loop Failure-Mutation Library
==============================================================================
Versioned regression library encoding each DOCUMENTED failure mode of this fleet
as a reproducible fixture + a mutation, each of which MUST be caught by its
intended detector. Extends the one-shot Trust-Pipeline Self-Check into a MAINTAINED
library with multiple classes, cross-fire (false-positive) measurement, and an
explicit coverage-gap probe.

Failure classes encoded (each = clean state + targeted mutation):
  clobber            mirror-revert: on-disk sha != pinned canonical sha
  desync             declared status disagrees with actual file/ledger state
  stale_verified     ledger '(verified:)' marker points at a missing artifact
  phantom_count      dashboard counts a reached goal with no on-disk evidence
  broken_pointer     INDEX pointer references a non-existent leaf path
  stale_instrument   instrument not run within the max-cycles window
  lossy_carryover    snapshot diff drops a file that was expected to persist

AC (goal #9):
  * >=6 fixtures, each caught by its intended detector.
  * an injected mutation NO detector catches is reported as a coverage gap.

Usage:
  python memory/researcher/failure_mutation.py            # full run -> JSON + table
  python memory/researcher/failure_mutation.py selftest   # assert all ACs
  python memory/researcher/failure_mutation.py --class clobber   # single class probe
"""
import json, os, sys, hashlib
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
LIBRARY_VERSION = "v1-2026-11-23"
REPORT = os.path.join(HERE, "failure-mutation-report.json")

# ----------------------------------------------------------------------------
# State model: a plain dict so every fixture is trivially reproducible.
# A "state" looks like:
#   {"files":  {path: content},            # on-disk contents
#    "pins":   {path: sha12},              # pinned canonical hashes (mirror)
#    "ledger": {goal_id: {"status","evidence_path"}},
#    "index":  [ref_path],                 # pointer-map references
#    "goals":  {lane: {"reached_count", "evidence_lines": N}},
#    "instruments": {name: last_run_date}}
# ----------------------------------------------------------------------------

TODAY = date(2026, 11, 23)


def _sha(s):
    return hashlib.sha1(s.encode()).hexdigest()[:12]


def clean_state():
    """A consistent, healthy baseline. Every mutation starts from a copy of this."""
    files = {
        "memory/designer/index_html_CANONICAL_abc123def456_2026-11-23.html": "<html>ok</html>",
        "memory/goals/researcher.md": "# goals\n1. done (verified: 2026-11-23 artifact path)",
        "memory/ops/blockers.md": "OPS-NOTE-1: helper down",
    }
    pins = {"memory/designer/index_html_CANONICAL_abc123def456_2026-11-23.html": _sha("<html>ok</html>")}
    ledger = {
        "r1": {"status": "reached", "evidence_path": "memory/researcher/evidence_r1.md"},
    }
    files["memory/researcher/evidence_r1.md"] = "(verified: ...) artifact exists"
    index = ["memory/researcher/INDEX.md", "memory/goals/INDEX.md"]
    files["memory/researcher/INDEX.md"] = "# map"
    files["memory/goals/INDEX.md"] = "# map"
    goals = {"researcher": {"reached_count": 1, "evidence_lines": 1}}
    instruments = {
        "stale_claim_scan": TODAY.isoformat(),
        "dispatch_desync": (TODAY - timedelta(days=10)).isoformat(),
    }
    return {
        "files": files,
        "pins": pins,
        "ledger": ledger,
        "index": index,
        "goals": goals,
        "instruments": instruments,
    }


# ----------------------------------------------------------------------------
# Mutations: each takes a fresh clean state and introduces exactly one failure.
# ----------------------------------------------------------------------------

def m_clobber(s):
    # mirror wrote different content than the pinned canonical -> sha mismatch
    s["files"]["memory/designer/index_html_CANONICAL_abc123def456_2026-11-23.html"] = "<html>CLOBBERED</html>"
    return s


def m_desync(s):
    # ledger says reached, but the goal file on disk has no matching evidence line
    s["files"]["memory/goals/researcher.md"] = "# goals\n1. open (no verified marker)"
    s["ledger"]["r2"] = {"status": "reached", "evidence_path": "memory/researcher/evidence_r1.md"}  # path exists; signal is count-only
    return s


def m_stale_verified(s):
    # a '(verified:)' ledger entry references an artifact that is missing on disk
    s["ledger"]["r3"] = {"status": "reached", "evidence_path": "memory/researcher/MISSING_r3.md"}
    return s


def m_phantom_count(s):
    # dashboard claims 5 reached but only 1 has on-disk evidence lines
    s["goals"]["researcher"] = {"reached_count": 5, "evidence_lines": 1}
    return s


def m_broken_pointer(s):
    # INDEX points at a leaf that does not exist
    s["index"].append("memory/researcher/phantom_leaf.md")
    return s


def m_stale_instrument(s):
    # push an instrument's last_run beyond the 2-cycle (~14d) window
    s["instruments"]["dispatch_desync"] = (TODAY - timedelta(days=30)).isoformat()
    return s


def m_lossy_carryover(s):
    # expected-to-persist file absent from current snapshot set
    s["expected_persist"] = ["memory/ops/blockers.md", "memory/goals/researcher.md"]
    del s["files"]["memory/ops/blockers.md"]
    return s


# ----------------------------------------------------------------------------
# Detectors: each inspects a state and returns (caught: bool, detail: str).
# Real heuristics (not stubs) - the same logic the live fleet uses.
# ----------------------------------------------------------------------------

def d_clobber(s):
    hits = [p for p, h in s["pins"].items()
            if p in s["files"] and _sha(s["files"][p]) != h]
    return (bool(hits), ";".join(hits) or "shas consistent")


def d_desync(s):
    # reached-entries in the ledger must be backed by an equal number of
    # on-disk '(verified:' markers; a surplus means declared status desynced from file.
    reached = sum(1 for e in s["ledger"].values() if e["status"] == "reached")
    markers = sum(v.count("(verified:") for v in s["files"].values() if isinstance(v, str))
    return (reached > markers, "reached=%d verified_markers=%d" % (reached, markers))


def d_stale_verified(s):
    hits = [gid for gid, e in s["ledger"].items()
            if e["status"] == "reached" and e.get("evidence_path") not in s["files"]]
    return (bool(hits), ";".join(hits) or "all artifacts present")


def d_phantom_count(s):
    hits = [lane for lane, g in s["goals"].items()
            if g["reached_count"] > g.get("evidence_lines", 0)]
    return (bool(hits), ";".join(hits) or "counts backed by evidence")


def d_broken_pointer(s):
    hits = [r for r in s["index"] if r not in s["files"]]
    return (bool(hits), ";".join(hits) or "all pointers resolve")


def d_stale_instrument(s, max_days=14):
    cutoff = TODAY - timedelta(days=max_days)
    hits = []
    for name, last in s["instruments"].items():
        try:
            if date.fromisoformat(last) < cutoff:
                hits.append(name)
        except Exception:
            hits.append(name + "(unparseable)")
    return (bool(hits), ";".join(hits) or "all instruments fresh")


def d_lossy_carryover(s):
    exp = s.get("expected_persist", [])
    hits = [p for p in exp if p not in s["files"]]
    return (bool(hits), ";".join(hits) or "no lossy carry-over")


# ----------------------------------------------------------------------------
# Registry: class -> (mutation, intended_detector)
# ----------------------------------------------------------------------------
CLASSES = [
    ("clobber",          m_clobber,          d_clobber),
    ("desync",           m_desync,           d_desync),
    ("stale_verified",   m_stale_verified,   d_stale_verified),
    ("phantom_count",    m_phantom_count,    d_phantom_count),
    ("broken_pointer",   m_broken_pointer,   d_broken_pointer),
    ("stale_instrument", m_stale_instrument, d_stale_instrument),
    ("lossy_carryover",  m_lossy_carryover,  d_lossy_carryover),
]
DETECTORS = {name: det for name, _, det in CLASSES}


def full_run():
    rows = []
    for name, mut, intended in CLASSES:
        state = mut(clean_state())
        matrix = {det_name: det(state)[0] for det_name, det in DETECTORS.items()}
        caught = matrix[name]
        # false positives: other detectors firing on a non-intended class
        fps = [k for k, v in matrix.items() if v and k != name]
        rows.append({
            "class": name,
            "intended_detector": intended.__name__,
            "caught": bool(caught),
            "false_positives": fps,
        })
    # Coverage-gap probe: a mutation NO detector catches -> must be reported.
    gap_state = clean_state()
    gap_state["files"]["memory/fleet/clock_skew.json"] = json.dumps({
        "host": "black", "reported_ts": "2026-11-23T99:00:00",
        "received_ts": "2026-11-23T08:00:00"})  # future timestamp: ordering inversion
    gap_matrix = {det_name: det(gap_state)[0] for det_name, det in DETECTORS.items()}
    coverage_gap = not any(gap_matrix.values())
    report = {
        "library_version": LIBRARY_VERSION,
        "date": TODAY.isoformat(),
        "classes": len(rows),
        "all_intended_caught": all(r["caught"] for r in rows),
        "rows": rows,
        "coverage_gap_probe": {
            "mutation": "future-timestamp ordering inversion (clock skew)",
            "detector_hits": gap_matrix,
            "is_uncovered": bool(coverage_gap),  # True => correctly reported as a gap
        },
        "per_detector_fp_rate": {
            det_name: round(sum(1 for r in rows if det_name in r["false_positives"]) / max(len(rows), 1), 3)
            for det_name in DETECTORS
        },
    }
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    return report


def selftest():
    rep = full_run()
    fails = []
    if rep["classes"] < 6:
        fails.append("AC1: need >=6 fixtures, got %d" % rep["classes"])
    for r in rep["rows"]:
        if not r["caught"]:
            fails.append("AC1: class '%s' NOT caught by intended detector %s"
                         % (r["class"], r["intended_detector"]))
    if not rep["coverage_gap_probe"]["is_uncovered"]:
        fails.append("AC2: coverage-gap mutation was unexpectedly caught")
    if fails:
        print("\n".join(fails)); return 1
    fpvals = list(rep["per_detector_fp_rate"].values())
    fps = (sum(fpvals) / len(fpvals)) if fpvals else 0.0
    print("failure_mutation %s: %d classes, all intended caught=%s, "
          "coverage-gap probe uncovered=%s, mean FP rate=%.3f -> SELFTEST PASS"
          % (LIBRARY_VERSION, rep["classes"], rep["all_intended_caught"],
             rep["coverage_gap_probe"]["is_uncovered"], fps))
    return 0


if __name__ == "__main__":
    if "selftest" in sys.argv:
        raise SystemExit(selftest())
    if "--class" in sys.argv:
        target = sys.argv[sys.argv.index("--class") + 1]
        name, mut, intended = next((n, m, d) for n, m, d in CLASSES if n == target)
        state = mut(clean_state())
        matrix = {det_name: det(state)[0] for det_name, det in DETECTORS.items()}
        print(json.dumps({"class": name, "matrix": matrix,
                          "intended": intended.__name__}, indent=2))
    else:
        rep = full_run()
        print("failure-mutation library %s: %d classes, all_intended_caught=%s"
              % (LIBRARY_VERSION, rep["classes"], rep["all_intended_caught"]))
        for r in rep["rows"]:
            print("  %-18s intended=%-20s caught=%s fps=%s"
                  % (r["class"], r["intended_detector"], r["caught"],
                     ",".join(r["false_positives"]) or "-"))
        print("coverage-gap probe uncovered=%s (expected True) -> report: %s"
              % (rep["coverage_gap_probe"]["is_uncovered"], os.path.relpath(REPORT)))
