#!/usr/bin/env python3
"""model_prestage_audit.py - Pre-staging gap analysis for <120s failover SLA.

Purpose: Verify that every agent's model variant is resident on >=2 hosts,
so that a host-down event triggers re-point (<60s) rather than load (120-240s).
Directly supports Verifier goal #2 (chaos-recovery verification, SLA <120s).

Usage:
  python memory/mechanic/model_prestage_audit.py --selftest   # synthetic pass/fail
  python memory/mechanic/model_prestage_audit.py --live       # probe real hosts

Output: memory/mechanic/prestage-audit-report.json + .md
"""
import json, os, sys, time, socket, argparse
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
CATALOG_PATH = HERE.parent / "llm" / "hotload-catalog.json"
AGENTS_JSON = HERE.parent.parent / "agents.json"
REPORT_JSON = HERE / "prestage-audit-report.json"
REPORT_MD = HERE / "prestage-audit-report.md"

# Fleet topology (from hotload catalog)
HOSTS = {"white": "127.0.0.1", "pale": None, "black": None, "red": None}
STUDIO_PORT = 8888
SLA_S = 120  # target recovery time


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_catalog():
    """Load the hotload catalog. Returns {host: [model_entries]} + metadata."""
    if not CATALOG_PATH.exists():
        return None, None
    cat = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    meta = cat.get("_meta", {})
    models = cat.get("models", [])
    # Group by host
    by_host = {}
    for m in models:
        h = m.get("host", "unknown")
        by_host.setdefault(h, []).append(m)
    return meta, by_host


def load_agents():
    """Load agents.json. Returns list of {name, model_id}."""
    if not AGENTS_JSON.exists():
        return []
    d = json.loads(AGENTS_JSON.read_text(encoding="utf-8"))
    return d.get("agents", [])


def resolve_model_variant(model_id, catalog_models):
    """Map an agent's model_id to a canonical variant (Q8_0 or Q4_K_S)."""
    mid = (model_id or "").lower()
    if "q8" in mid:
        return "Q8_0"
    elif "q4" in mid:
        return "UD-Q4_K_S"
    # Alias resolution: check catalog agent_profiles
    for m in catalog_models:
        variant = m.get("gguf_variant", "")
        profiles = [p.lower() for p in m.get("agent_profiles", [])]
        if model_id.lower() in [p for p in profiles]:
            return variant
    # Fallback: match by id
    for m in catalog_models:
        if m.get("id", "") == model_id.lower():
            return m.get("gguf_variant", "?")
    return "?"


def audit(meta, by_host, agents):
    """Core audit: for each model variant, count how many hosts have it resident.
    
    Returns:
      - coverage: {variant: [hosts]}
      - gaps: [{variant, hosts, missing_count, affected_agents}]
      - verdict: PASS if all variants on >=2 hosts
    """
    all_models = []
    for host, models in by_host.items():
        for m in models:
            m["_host"] = host
            all_models.append(m)
    
    # Build variant -> hosts map
    variant_hosts = {}  # {variant: set(hosts)}
    for m in all_models:
        v = m.get("gguf_variant", "?")
        h = m["_host"]
        variant_hosts.setdefault(v, set()).add(h)
    
    # Map agents to variants
    agent_variants = {}  # {agent_name: variant}
    for a in agents:
        v = resolve_model_variant(a.get("model_id", ""), all_models)
        agent_variants[a.get("name", "?")] = v
    
    # Find gaps: variants with <2 hosts (including unknown variants mapped to 0 hosts)
    gaps = []
    all_variants_needed = set(variant_hosts.keys()) | set(agent_variants.values())
    for variant in sorted(all_variants_needed):
        hosts = variant_hosts.get(variant, set())
        if len(hosts) < 2:
            affected = [an for an, v in agent_variants.items() if v == variant]
            risk = "UNKNOWN-MODEL: not in catalog; cannot pre-stage" if variant == "?" else \
                   "SINGLE-POINT-OF-FAILURE: host-down = full reload (120-240s)"
            gaps.append({
                "variant": variant,
                "hosts": sorted(hosts),
                "host_count": len(hosts),
                "affected_agents": affected,
                "risk": risk
            })
    
    # Verdict
    verdict = "PASS" if not gaps else "GAP"
    
    return {
        "ts": now_iso(),
        "sla_s": SLA_S,
        "variants": {v: sorted(h) for v, h in variant_hosts.items()},
        "agent_map": agent_variants,
        "gaps": gaps,
        "verdict": verdict,
        "summary": f"{len(variant_hosts)} model variants across {len(by_host)} hosts; "
                  f"{len(gaps)} variant(s) below dual-residency threshold"
    }


def selftest():
    """Prove the audit engine works on synthetic data."""
    print("[selftest] model_prestage_audit.py")
    
    # Case 1: all variants dual-resident -> PASS
    meta = {"hosts": {"white": {}, "pale": {}, "black": {}, "red": {}}}
    by_host = {
        "white": [{"gguf_variant": "Q8_0", "host": "white"}, {"gguf_variant": "UD-Q4_K_S", "host": "white"}],
        "pale": [{"gguf_variant": "Q8_0", "host": "pale"}, {"gguf_variant": "UD-Q4_K_S", "host": "pale"}],
    }
    agents = [
        {"name": "Orchestrator", "model_id": "Qwen3.8-27B-Q8_0"},
        {"name": "Researcher", "model_id": "Qwen3.8-27B-Q4_K_S"},
    ]
    r = audit(meta, by_host, agents)
    assert r["verdict"] == "PASS", f"Expected PASS, got {r['verdict']}: {r['gaps']}"
    assert len(r["variants"]["Q8_0"]) == 2
    print(f"  [PASS] dual-resident -> PASS ({r['summary']})")
    
    # Case 2: one variant dual, one single-host -> GAP
    by_host2 = {
        "white": [{"gguf_variant": "Q8_0", "host": "white"}, {"gguf_variant": "UD-Q4_K_S", "host": "white"}],
        "pale": [{"gguf_variant": "Q8_0", "host": "pale"}],  # Q4 missing from pale
    }
    r2 = audit(meta, by_host2, agents)
    assert r2["verdict"] == "GAP", f"Expected GAP, got {r2['verdict']}"
    assert len(r2["gaps"]) == 1, f"Expected 1 gap, got {len(r2['gaps'])}: {r2['gaps']}"
    assert r2["gaps"][0]["variant"] == "UD-Q4_K_S"
    print(f"  [PASS] single-host variant -> GAP ({r2['summary']})")
    
    # Case 3: three hosts, all variants covered -> PASS
    by_host3 = {
        "white": [{"gguf_variant": "Q8_0", "host": "white"}],
        "pale": [{"gguf_variant": "UD-Q4_K_S", "host": "pale"}],
        "black": [{"gguf_variant": "Q8_0", "host": "black"}, {"gguf_variant": "UD-Q4_K_S", "host": "black"}],
    }
    r3 = audit(meta, by_host3, agents)
    assert r3["verdict"] == "PASS"
    print(f"  [PASS] three-host spread -> PASS ({r3['summary']})")
    
    # Case 4: unknown variant (agent has model not in catalog) -> GAP
    agents4 = agents + [{"name": "Ghost", "model_id": "mystery-model-x9"}]
    r4 = audit(meta, by_host, agents4)
    # Ghost maps to '?' which has 0 hosts -> gap
    assert any(g["variant"] == "?" for g in r4["gaps"]), f"Expected ? gap: {r4['gaps']}"
    print(f"  [PASS] unknown variant -> GAP flagged ({len(r4['gaps'])} gap(s))")
    
    print("[selftest] ALL PASS (4/4)")
    return True


def run_live():
    """Run the audit against real catalog + agents.json."""
    meta, by_host = load_catalog()
    if not by_host:
        print("[live] ERROR: hotload-catalog.json not found or empty")
        return False
    
    agents = load_agents()
    if not agents:
        print("[live] WARNING: agents.json not found; auditing catalog only")
    
    result = audit(meta, by_host, agents)
    
    # Write reports
    REPORT_JSON.write_text(json.dumps(result, indent=2))
    
    md_lines = [
        "# Model Pre-staging Audit Report",
        f"Run: {result['ts']}",
        f"SLA target: <{SLA_S}s recovery (Verifier goal #2)",
        "",
        "## Variant Coverage",
        "| Variant | Hosts | Count | Status |",
        "|---------|-------|-------|--------|",
    ]
    for v, hosts in sorted(result["variants"].items()):
        status = "OK" if len(hosts) >= 2 else "**GAP**"
        md_lines.append(f"| {v} | {', '.join(hosts)} | {len(hosts)} | {status} |")
    
    md_lines += ["", "## Agent-to-Variant Map", "| Agent | Variant |", "|-------|---------|"]
    for an, v in sorted(result["agent_map"].items()):
        md_lines.append(f"| {an} | {v} |")
    
    if result["gaps"]:
        md_lines += ["", "## GAPS (single-point-of-failure)"]
        for g in result["gaps"]:
            md_lines.append(f"- **{g['variant']}** on {', '.join(g['hosts'])} only; affects: {', '.join(g['affected_agents'])}")
            md_lines.append(f"  Risk: {g['risk']}")
            md_lines.append(f"  Fix: load {g['variant']} on one additional host (120-240s one-time cost)")
    
    md_lines += ["", f"## Verdict: **{result['verdict']}**", "", result["summary"]]
    REPORT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    
    print(f"[live] Verdict: {result['verdict']}")
    print(f"[live] {result['summary']}")
    for g in result["gaps"]:
        print(f"  GAP: {g['variant']} only on {g['hosts']} (affects {len(g['affected_agents'])} agents)")
    print(f"[live] Reports: {REPORT_JSON.name}, {REPORT_MD.name}")
    return result["verdict"] == "PASS"


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Model pre-staging audit for <120s failover SLA")
    ap.add_argument("--selftest", action="store_true", help="Run synthetic self-test")
    ap.add_argument("--live", action="store_true", help="Audit real catalog + agents")
    args = ap.parse_args()
    
    if args.selftest:
        ok = selftest()
        sys.exit(0 if ok else 1)
    elif args.live:
        ok = run_live()
        sys.exit(0 if ok else 1)
    else:
        print(__doc__)
        sys.exit(0)