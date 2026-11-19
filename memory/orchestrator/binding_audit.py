"""
binding_audit.py - Orchestrator cycle-7 goal 5 (Model Binding Governance)
Checks agents.json model_id aliases against actual LM Studio loaded models.

Modes:
  --dry-run   Validate structure only (no network): all aliases non-empty,
              no duplicate model bindings, all agent IDs unique.
  --live      Probe LM Studio :8888 on each configured host; report mismatches,
              stale bindings (alias in agents.json but model not loaded), and
              orphaned models (loaded but no agent bound).

Output: memory/llm/binding-audit.md (markdown report)
Exit codes: 0 = clean, 1 = issues found, 2 = error
"""
import json, os, sys, urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
AGENTS_JSON = os.path.join(ROOT, "agents.json")
HOSTS_JSON = os.path.join(ROOT, "memory", "llm", "hosts.json")
REPORT_PATH = os.path.join(ROOT, "memory", "llm", "binding-audit.md")

STUDIO_PORTS = {
    "white": 8888,
    "black": 8888,
    "red": 8888,
    "pale": 8888,
}


def load_agents():
    with open(AGENTS_JSON, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("agents", [])


def load_hosts():
    if not os.path.exists(HOSTS_JSON):
        return {}
    with open(HOSTS_JSON, encoding="utf-8") as f:
        return json.load(f)


def probe_studio(host_ip, port=8888, timeout=5):
    """Return list of loaded model IDs from LM Studio, or None on failure."""
    url = f"http://{host_ip}:{port}/v1/models"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            return [m.get("id", "") for m in data.get("data", [])]
    except Exception as e:
        return None


def dry_run_check(agents):
    """Structural validation without network. Returns list of issues."""
    issues = []
    seen_ids = set()
    seen_models = {}

    for a in agents:
        aid = a.get("id", "<missing>")
        mid = a.get("model_id", "")

        if not aid:
            issues.append(f"CRITICAL: agent with empty id at index {agents.index(a)}")
        elif aid in seen_ids:
            issues.append(f"DUPLICATE: agent id '{aid}' appears more than once")
        seen_ids.add(aid)

        if not mid or not mid.strip():
            issues.append(f"MISSING: agent '{aid}' has empty model_id")
        else:
            if mid in seen_models:
                issues.append(
                    f"DUPLICATE-BINDING: model '{mid}' bound to both "
                    f"'{seen_models[mid]}' and '{aid}'"
                )
            else:
                seen_models[mid] = aid

    return issues


def live_check(agents, hosts):
    """Probe each host's LM Studio; cross-reference with agents.json bindings."""
    issues = []
    host_loaded = {}  # host -> [model_ids]

    for hname, hcfg in hosts.items():
        ip = hcfg.get("ip", "")
        port = STUDIO_PORTS.get(hname, 8888)
        if not ip:
            issues.append(f"WARN: host '{hname}' has no IP configured")
            continue
        loaded = probe_studio(ip, port)
        if loaded is None:
            issues.append(f"UNREACHABLE: host '{hname}' ({ip}:{port}) did not respond")
            continue
        host_loaded[hname] = set(loaded)

    # Check each agent binding
    all_loaded = set()
    for models in host_loaded.values():
        all_loaded |= models

    for a in agents:
        aid = a.get("id", "?")
        mid = a.get("model_id", "")
        if not mid:
            continue  # already caught in dry-run
        if all_loaded and mid not in all_loaded:
            issues.append(
                f"STALE-BINDING: agent '{aid}' -> model '{mid}' not loaded on any reachable host"
            )

    # Orphaned models (loaded but no agent references them)
    bound_models = {a.get("model_id", "") for a in agents if a.get("model_id")}
    for hname, models in host_loaded.items():
        for m in sorted(models):
            if m not in bound_models:
                issues.append(f"ORPHANED: model '{m}' loaded on {hname} but no agent bound to it")

    return issues, host_loaded


def write_report(issues, mode, host_loaded=None):
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    status = "PASS" if not issues else f"{len(issues)} ISSUE(S)"

    lines = [
        f"# Binding Audit Report",
        f"",
        f"**Run:** {ts}  ",
        f"**Mode:** {mode}  ",
        f"**Status:** {status}",
        f"",
    ]
    if issues:
        lines.append("## Issues")
        lines.append("")
        for i in issues:
            lines.append(f"- {i}")
        lines.append("")
    else:
        lines.append("No issues found. All bindings valid.")
        lines.append("")

    if host_loaded:
        lines.append("## Host Model Inventory")
        lines.append("")
        for hname, models in sorted(host_loaded.items()):
            lines.append(f"### {hname}")
            for m in sorted(models):
                lines.append(f"- `{m}`")
            lines.append("")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return REPORT_PATH


def main():
    mode = "dry-run"
    if "--live" in sys.argv:
        mode = "live"

    agents = load_agents()
    hosts = load_hosts()

    issues = []

    # Always run structural check
    struct_issues = dry_run_check(agents)
    issues.extend(struct_issues)

    host_loaded = None
    if mode == "live":
        live_issues, host_loaded = live_check(agents, hosts)
        issues.extend(live_issues)

    path = write_report(issues, mode, host_loaded)
    print(f"Binding audit ({mode}): {len(issues)} issue(s)")
    for i in issues:
        print(f"  - {i}")
    print(f"Report: {path}")

    # Exit 0 if clean, 1 if issues (but not critical), 2 on error
    critical = any(i.startswith("CRITICAL") for i in issues)
    return 2 if critical else (1 if issues else 0)


if __name__ == "__main__":
    sys.exit(main())
