"""Service Dependency Graph - maps fleet services to their dependencies.
Usage: python memory/mechanic/service_deps.py [--json | --mermaid | --test-remove <dep_id>]

Produces:
  - service-deps.json: structured dependency graph
  - service-deps.mmd: mermaid diagram (renderable in markdown)
"""
import json, os, sys
from datetime import datetime, timezone

# Known fleet services and their dependencies
SERVICES = {
    "portal": {
        "description": "Fleet portal server (agent_portal.py)",
        "host": "white",
        "port": 8099,
        "depends_on": ["python-runtime", "agents.json", "memory-dir", "ui-modules", "llm-studio-white"],
    },
    "llm-studio-white": {
        "description": "LM Studio instance on White (port 8888)",
        "host": "white",
        "port": 8888,
        "depends_on": ["python-runtime", "gpu-vram-white", "model-files"],
    },
    "llm-studio-black": {
        "description": "LM Studio instance on Black (port 8889)",
        "host": "black",
        "port": 8889,
        "depends_on": ["python-runtime", "gpu-vram-black", "model-files"],
    },
    "llm-studio-red": {
        "description": "LM Studio instance on Red (port 8890)",
        "host": "red",
        "port": 8890,
        "depends_on": ["python-runtime", "gpu-vram-red", "model-files"],
    },
    "file-watcher": {
        "description": "Memory mirror sync (memory_mirror.py)",
        "host": "white",
        "port": None,
        "depends_on": ["python-runtime", "memory-dir", "git-binary"],
    },
    "health-check": {
        "description": "Fleet health probe (health_check.py)",
        "host": "white",
        "port": None,
        "depends_on": ["python-runtime", "portal"],
    },
    "winrm-remote": {
        "description": "WinRM remote management channel",
        "host": "all",
        "port": 5985,
        "depends_on": ["network-lan", "winrm-service", "credentials-store"],
    },
    "net-probe": {
        "description": "Network health probe (net_probe.py)",
        "host": "white",
        "port": None,
        "depends_on": ["python-runtime", "network-lan"],
    },
}

# Infrastructure dependencies (leaf nodes - no further deps)
INFRA = {
    "python-runtime": {"type": "runtime", "description": "Python 3.x interpreter"},
    "agents.json": {"type": "file", "path": "agents.json", "description": "Agent profiles config"},
    "memory-dir": {"type": "directory", "path": "memory/", "description": "Shared project memory"},
    "ui-modules": {"type": "directory", "path": "ui/", "description": "Frontend CSS/JS modules"},
    "gpu-vram-white": {"type": "hardware", "host": "white", "description": "GPU VRAM on White"},
    "gpu-vram-black": {"type": "hardware", "host": "black", "description": "GPU VRAM on Black"},
    "gpu-vram-red": {"type": "hardware", "host": "red", "description": "GPU VRAM on Red"},
    "model-files": {"type": "directory", "path": "/models/", "description": "LLM model weights"},
    "git-binary": {"type": "binary", "description": "Git executable for mirror sync"},
    "network-lan": {"type": "network", "description": "LAN connectivity between hosts"},
    "winrm-service": {"type": "service", "port": 5985, "description": "Windows Remote Management service"},
    "credentials-store": {"type": "file", "path": "memory/ops/winrm_creds.json", "description": "WinRM credentials (encrypted)"},
}

def build_graph():
    """Build the full dependency graph as nested dict."""
    graph = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "services": {},
        "infrastructure": INFRA,
        "edges": [],
    }
    for svc_id, svc in SERVICES.items():
        graph["services"][svc_id] = svc
        for dep in svc["depends_on"]:
            graph["edges"].append({"from": svc_id, "to": dep, "type": "requires"})
    return graph

def compute_impact_set(graph, removed_dep):
    """Given a dependency ID, find all services that would be impacted (transitively)."""
    # Build reverse adjacency: dep -> set of services depending on it
    dependents = {}
    for edge in graph["edges"]:
        dependents.setdefault(edge["to"], set()).add(edge["from"])
    # BFS from removed_dep through service-to-service deps
    impacted = set()
    queue = [removed_dep]
    while queue:
        current = queue.pop(0)
        for svc in dependents.get(current, set()):
            if svc not in impacted:
                impacted.add(svc)
                # If svc is itself a service that others depend on, propagate
                if svc in graph["services"]:
                    queue.append(svc)
    return sorted(impacted)

def to_mermaid(graph):
    """Generate mermaid diagram text."""
    lines = ["graph TD"]
    for svc_id, svc in graph["services"].items():
        label = f"{svc_id}[\"{svc['description'].split('(')[0].strip()}\"]"
        lines.append(f"  {label}")
    for dep_id, dep in graph["infrastructure"].items():
        lines.append(f"  {dep_id}((\"{dep['description'][:30]}\"))")
    for edge in graph["edges"]:
        lines.append(f"  {edge['from']} -->|requires| {edge['to']}")
    return "\n".join(lines)

def main():
    out_dir = os.path.dirname(__file__)
    graph = build_graph()

    if "--test-remove" in sys.argv:
        idx = sys.argv.index("--test-remove")
        dep_id = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
        if not dep_id:
            print("Usage: --test-remove <dep_id>")
            sys.exit(1)
        if dep_id not in graph["infrastructure"] and dep_id not in graph["services"]:
            print(f"Unknown dependency: {dep_id}")
            print(f"Known: {list(graph['infrastructure'].keys()) + list(graph['services'].keys())}")
            sys.exit(1)
        impacted = compute_impact_set(graph, dep_id)
        print(f"\nImpact set if '{dep_id}' is removed:")
        for svc in impacted:
            desc = graph["services"].get(svc, {}).get("description", "?")
            print(f"  - {svc}: {desc}")
        if not impacted:
            print("  (none - no services depend on this)")
        return

    # Default: write JSON + mermaid
    json_path = os.path.join(out_dir, "service-deps.json")
    mmd_path = os.path.join(out_dir, "service-deps.mmd")
    with open(json_path, "w") as f:
        json.dump(graph, f, indent=2)
    with open(mmd_path, "w") as f:
        f.write(to_mermaid(graph))

    print(f"Services: {len(graph['services'])}")
    print(f"Infrastructure deps: {len(graph['infrastructure'])}")
    print(f"Edges: {len(graph['edges'])}")
    print(f"Wrote: {json_path}")
    print(f"Wrote: {mmd_path}")

if __name__ == "__main__":
    main()