#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
blast_radius.py - Researcher goal #10: Autonomy Guardrails & Blast-Radius Registry
===================================================================================
The safety layer that lets the Self-Healing Remediation Bus (goal #1) run unattended:
BEFORE any remediation action executes, compute its BLAST RADIUS (files / hosts /
endpoints affected) and gate it on a risk class {safe | review | halt}.

  safe   -> allowed to auto-apply (local, reversible, single target, not canonical)
  review -> surfaced for operator sign-off; NOT auto-applied
  halt   -> blocked entirely (remote/production, irreversible, or fleet-wide)

AC (goal #10):
  * for each remediation type it returns an explicit blast-radius set + risk class;
  * a seeded high-blast action is gated to review/halt, not auto-applied.

Usage:
  python memory/researcher/blast_radius.py           # full run -> JSON + table
  python memory/researcher/blast_radius.py selftest  # assert all ACs
"""
import json, os, sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
REGISTRY_VERSION = "v1-2026-11-23"
REPORT = os.path.join(HERE, "blast-radius-report.json")
TODAY = date(2026, 11, 23)

# ----------------------------------------------------------------------------
# Action model. Each remediation action declares the properties that determine
# its blast radius; the gate derives the affected set + risk class from them.
#   type            human id (aligned to remediation_bus.py fix actions)
#   targets         concrete objects touched (file paths / hosts / endpoints)
#   scope           local | shared | remote
#   reversible      can the action be undone cleanly?
#   idempotent      re-running is a no-op?
#   touches_canonical  does it write a pinned/canonical or SSOT resource?
# ----------------------------------------------------------------------------
ACTIONS = [
    {"type": "clear_stale_verified_marker", "targets": ["memory/researcher/evidence_x.md"],
     "scope": "local", "reversible": True, "idempotent": True, "touches_canonical": False},
    {"type": "write_correction_note", "targets": ["memory/researcher/stale-claim-corrections.md"],
     "scope": "local", "reversible": True, "idempotent": True, "touches_canonical": False},
    {"type": "rebuild_reach_matrix", "targets": ["memory/researcher/reach-matrix.json"],
     "scope": "local", "reversible": True, "idempotent": True, "touches_canonical": False},
    {"type": "trigger_mtime_reload", "targets": ["portal:mtime-reload"],
     "scope": "local", "reversible": True, "idempotent": True, "touches_canonical": False},
    {"type": "relend_clobbered_endpoint", "targets": ["memory/designer/index_html_CANONICAL_*.html"],
     "scope": "shared", "reversible": True, "idempotent": True, "touches_canonical": True},
    {"type": "repin_index_html", "targets": ["index.html", "memory_mirror.py:PIN_FILES"],
     "scope": "shared", "reversible": True, "idempotent": False, "touches_canonical": True},
    # HIGH-BLAST seeded action: remote, production model lifecycle, irreversible until reload
    {"type": "unload_host_model", "targets": ["host:black:/models/home", "/api/fleet/cockpit"],
     "scope": "remote", "reversible": False, "idempotent": True, "touches_canonical": False},
]


def blast_radius(a):
    """Explicit set of files / hosts / endpoints affected by the action."""
    return {"targets": sorted(set(a["targets"])), "scope": a["scope"],
            "count": len(set(a["targets"]))}


def risk_class(a):
    """Derive safe | review | halt from the action's declared properties."""
    if a["scope"] == "remote" or not a["reversible"]:
        return "halt"                      # production / irreversible -> never auto-apply
    if a["touches_canonical"] or a["scope"] == "shared" or len(set(a["targets"])) > 1:
        return "review"                    # canonical/SSOT/multi-target -> operator sign-off
    return "safe"                          # local, reversible, single target


def gate(a):
    rc = risk_class(a)
    return {
        "type": a["type"],
        "blast_radius": blast_radius(a),
        "risk_class": rc,
        "allowed_unattended": (rc == "safe"),   # only 'safe' may auto-apply
    }


def full_run():
    gates = [gate(a) for a in ACTIONS]
    high_blast = [g for g in gates if g["risk_class"] in ("review", "halt")]
    unattended_blocked = all(not g["allowed_unattended"] for g in high_blast)
    report = {
        "registry_version": REGISTRY_VERSION,
        "date": TODAY.isoformat(),
        "action_count": len(gates),
        "risk_distribution": {rc: sum(1 for g in gates if g["risk_class"] == rc)
                              for rc in ("safe", "review", "halt")},
        "high_blast_gated": unattended_blocked,   # AC2: no high-blast action auto-applies
        "gates": gates,
    }
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    return report


def selftest():
    rep = full_run()
    fails = []
    if rep["action_count"] < 5:
        fails.append("AC1: need >=5 remediation types, got %d" % rep["action_count"])
    for g in rep["gates"]:
        if not g["blast_radius"]["targets"] or g["risk_class"] not in ("safe", "review", "halt"):
            fails.append("AC1: action %s missing blast-radius set / risk class" % g["type"])
    # AC2: the seeded high-blast (remote/irreversible) action must NOT auto-apply
    seed = next((g for g in rep["gates"] if g["type"] == "unload_host_model"), None)
    if seed is None or seed["risk_class"] not in ("review", "halt") or seed["allowed_unattended"]:
        fails.append("AC2: high-blast action 'unload_host_model' was NOT gated to review/halt")
    if not rep["high_blast_gated"]:
        fails.append("AC2: some high-blast action is allowed unattended")
    # sanity: at least one safe + one non-safe for a meaningful spread
    if rep["risk_distribution"]["safe"] < 1 or rep["risk_distribution"]["halt"] < 1:
        fails.append("spread: expected >=1 safe and >=1 halt")
    if fails:
        print("\n".join(fails)); return 1
    print("blast_radius %s: %d actions, dist=%s, high-blast gated (not auto-applied)=%s "
          "-> SELFTEST PASS"
          % (REGISTRY_VERSION, rep["action_count"], rep["risk_distribution"],
             rep["high_blast_gated"]))
    return 0


if __name__ == "__main__":
    if "selftest" in sys.argv:
        raise SystemExit(selftest())
    rep = full_run()
    print("blast-radius registry %s: %d actions, distribution=%s"
          % (REGISTRY_VERSION, rep["action_count"], rep["risk_distribution"]))
    for g in rep["gates"]:
        auto = "AUTO" if g["allowed_unattended"] else "gate"
        print("  %-28s %-7s targets=%-3d [%s] %s"
              % (g["type"], g["risk_class"], g["blast_radius"]["count"], auto,
                 ",".join(g["blast_radius"]["targets"][:2])))
    print("high-blast actions gated (not auto-applied)=%s -> report: %s"
          % (rep["high_blast_gated"], os.path.relpath(REPORT)))
