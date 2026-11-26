#!/usr/bin/env python3
"""prestage_remediate.py - Generate + execute model pre-staging commands to eliminate SPOF variants.

Usage:
  python memory/ops/prestage_remediate.py --dry-run    # show what would be loaded where
  python memory/ops/prestage_remediate.py --execute    # actually issue load commands via Studio API
  python memory/ops/prestage_remediate.py --report     # print gap report (no action)

Reads: agents.json (model_id per agent)
Writes: memory/mechanic/prestage-remediation-log.jsonl (one line per action taken)

Exit codes: 0=OK, 1=gaps found (dry-run/report), 2=execution error
"""
import json, sys, pathlib, urllib.request, datetime, os

ROOT = pathlib.Path.cwd()  # AgentPortal root
AGENTS_JSON = ROOT / "agents.json"
LOG_FILE = ROOT / "memory" / "mechanic" / "prestage-remediation-log.jsonl"

# Studio base URLs per host (adjust as hosts come online)
HOST_STUDIO_URLS = {
    "white": "http://127.0.0.1:8888",
    "pale": "http://127.0.0.1:8889",
    "black": "http://127.0.0.1:8890",
    "red": "http://127.0.0.1:8891",
}

def load_agents():
    """Return {agent_id: model_id} from agents.json."""
    data = json.loads(AGENTS_JSON.read_text(encoding="utf-8"))
    return {a["id"]: a["model_id"] for a in data.get("agents", [])}

def probe_hosts():
    """Try to reach each host's Studio API. Returns {host: [model_ids] or None}."""
    host_models = {}
    for host, url in HOST_STUDIO_URLS.items():
        try:
            req = urllib.request.Request(f"{url}/api/models")
            with urllib.request.urlopen(req, timeout=5) as resp:
                models = json.loads(resp.read())
                if isinstance(models, list):
                    host_models[host] = [m.get("id", m.get("name", "")) for m in models]
                else:
                    host_models[host] = list(models.keys()) if isinstance(models, dict) else []
        except Exception:
            host_models[host] = None
    return host_models

def find_gaps(agent_models, host_models):
    """Identify model variants with <2 host residency."""
    # Build variant -> hosts map from live probe
    variant_hosts = {}
    any_reachable = False
    for host, models in host_models.items():
        if models is None:
            continue
        any_reachable = True
        for m in models:
            variant_hosts.setdefault(m, set()).add(host)
    
    if not any_reachable:
        # Fallback: assume single-host residency based on agent count
        # Variants used by only 1 agent are highest SPOF risk
        from collections import Counter
        variant_agents = {}
        for aid, mid in agent_models.items():
            variant_agents.setdefault(mid, []).append(aid)
        gaps = []
        for variant, agents in sorted(variant_agents.items()):
            if len(agents) <= 1:
                gaps.append({
                    "variant": variant,
                    "hosts": ["unknown (single-host assumed)"],
                    "agents": agents,
                    "risk": "SPOF (unverified - all hosts unreachable)"
                })
        return gaps
    
    # Normal path: check residency
    gaps = []
    for variant, hosts in sorted(variant_hosts.items()):
        if len(hosts) < 2:
            affected = [aid for aid, mid in agent_models.items() if mid == variant]
            gaps.append({"variant": variant, "hosts": sorted(hosts), "agents": affected, "risk": "SPOF"})
    return gaps

def pick_target_host(variant, current_hosts):
    """Pick the best host to add this variant on."""
    candidates = [h for h in HOST_STUDIO_URLS if h not in current_hosts]
    return candidates[0] if candidates else None

def generate_commands(gaps):
    """Generate exact API calls to load each gap variant on an additional host."""
    cmds = []
    for gap in gaps:
        target = pick_target_host(gap["variant"], gap["hosts"])
        if target is None:
            cmds.append({"action": "SKIP", "reason": f"no candidate host for {gap['variant']}"})
            continue
        url = HOST_STUDIO_URLS[target]
        cmds.append({
            "action": "LOAD",
            "variant": gap["variant"],
            "target_host": target,
            "url": f"{url}/api/models/load",
            "method": "POST",
            "body": {"model_id": gap["variant"]},
            "estimated_time_s": 180,
        })
    return cmds

def execute_commands(cmds):
    """Execute load commands. Returns results."""
    results = []
    for cmd in cmds:
        if cmd["action"] != "LOAD":
            results.append({"cmd": cmd, "status": "skipped", "detail": cmd.get("reason", "")})
            continue
        try:
            req = urllib.request.Request(
                cmd["url"],
                data=json.dumps(cmd["body"]).encode(),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=300) as resp:
                body = json.loads(resp.read())
                results.append({"cmd": cmd, "status": "ok", "response": body})
        except Exception as e:
            results.append({"cmd": cmd, "status": "error", "detail": str(e)})
    return results

def log_action(entries):
    """Append to remediation log."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps({"ts": ts, **e}) + "\n")

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--report"
    
    agent_models = load_agents()
    host_models = probe_hosts()
    gaps = find_gaps(agent_models, host_models)
    
    reachable = [h for h, m in host_models.items() if m is not None]
    print(f"Mode: {mode} | Reachable hosts: {reachable or 'NONE'}")
    print(f"Gaps found: {len(gaps)}")
    for g in gaps:
        agents_str = ", ".join(g["agents"]) if g["agents"] else "(none mapped)"
        print(f"  - {g['variant']}: hosts={g['hosts']} agents=[{agents_str}]")
    
    if not gaps:
        print("VERDICT: OK - all variants have >=2 host residency")
        return 0
    
    if mode == "--report":
        print("VERDICT: GAP - remediation needed (run --dry-run for plan)")
        return 1
    
    cmds = generate_commands(gaps)
    
    if mode == "--dry-run":
        print("\nPlanned actions:")
        for c in cmds:
            if c["action"] == "LOAD":
                print(f"  LOAD {c['variant']} -> {c['target_host']} ({c['url']})")
            else:
                print(f"  SKIP: {c.get('reason')}")
        return 1
    
    if mode == "--execute":
        results = execute_commands(cmds)
        log_action(results)
        ok = sum(1 for r in results if r["status"] == "ok")
        err = sum(1 for r in results if r["status"] == "error")
        print(f"\nExecuted: {ok} ok, {err} errors")
        for r in results:
            if r["status"] == "error":
                print(f"  ERROR: {r['cmd'].get('variant')}: {r['detail']}")
        return 2 if err else 0
    
    print(f"Unknown mode: {mode}")
    return 1

if __name__ == "__main__":
    sys.exit(main())
