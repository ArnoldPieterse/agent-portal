#!/usr/bin/env python3
"""Fleet Onboarding Wizard v4 (Orchestrator goal #7, cycle-7).

Onboards a new agent end-to-end: interactive CLI prompts for name, role
template, model preference (validated against the hotload catalog + existing
aliases), and tools subset. Generates all four fleet artifacts:
  1. agents.json entry (full field set, matching existing profiles)
  2. memory/<id>/INDEX.md          (agent leaf index)
  3. memory/goals/<id>.md          (goal-file skeleton)
  4. memory/INDEX.md sub-index line

Usage:
  python memory/orchestrator/onboard_agent.py                 # interactive (tty)
  python memory/orchestrator/onboard_agent.py --name Tessa --id tessa \
      --role researcher --model quinn-q4 --tools web_search,python --dry-run
  python memory/orchestrator/onboard_agent.py ...             # execute (+ commit)
       [--blurb TEXT] [--persona TEXT] [--emoji E] [--color HEX]
       [--max-tool-calls N] [--force] [--no-commit]

Pairs with retire_agent.py: onboarding a test agent then retiring it must leave
zero orphaned references (that is the acceptance test).

Exit codes: 0 ok, 2 usage/bad input, 3 file not found.
"""
import argparse
import datetime as _dt
import json
import os
import re
import subprocess
import sys

DEFAULT_CATALOG = "memory/llm/hotload-catalog.json"

# Role templates: template -> (blurb, persona, tools, emoji, color).
# Keep personas short; the full runtime persona can be widened later.
ROLE_TEMPLATES = {
    "researcher": (
        "investigative researcher; finds answers, cross-checks sources, reports with confidence",
        "You are a research specialist. Find answers, cross-check independent sources, and report findings with an explicit confidence level and citations. Lead with the answer, then the evidence.",
        ["web_search", "python", "terminal"], "🔎", "#2fbf71",
    ),
    "builder": (
        "hands-on implementer; builds in small verified increments",
        "You are a hands-on builder. Implement in small, verified increments. Never claim something is built unless a tool call in this reply produced the artifact.",
        ["python", "terminal", "edit_file"], "🔧", "#f5a623",
    ),
    "designer": (
        "graphics/UI/frontend specialist; critiques and builds interfaces",
        "You are a design + frontend specialist. Critique and build interfaces. Prefer the shared token system; keep files small and modular.",
        ["edit_file", "python", "render_html"], "🎨", "#c05be0",
    ),
    "verifier": (
        "evidence-first tester; passes or fails with proof",
        "You are an evidence-first verifier. Pass or fail every claim with reproducible proof (command + output). No proof, no pass.",
        ["python", "terminal"], "✅", "#3aa0ff",
    ),
    "scribe": (
        "synthesizer; compresses threads into decisions + open items",
        "You are a synthesizer. Compress long threads into crisp decisions plus a short list of open items. Preserve the supersession chain.",
        ["python", "terminal", "edit_file"], "📝", "#e05b5b",
    ),
    "archivist": (
        "research and knowledge-base retrieval; cites what it finds",
        "You are an archivist. Retrieve from the knowledge base and cite exactly what you find, with paths. Never invent a source.",
        ["python", "terminal", "web_search"], "📚", "#8a7bff",
    ),
    "mechanic": (
        "ops engineer; keeps the fleet healthy, fixes with evidence",
        "You are an ops engineer. Keep the fleet healthy and fix failures with evidence (probe + log). Do not re-probe a known blocker.",
        ["python", "terminal"], "🛠️", "#5bc0c0",
    ),
    "generic": (
        "general-purpose fleet agent",
        "You are a general-purpose fleet agent. Be concrete and decisive; every change you make must be verifiable.",
        ["python", "terminal"], "🤖", "#888888",
    ),
}

ALL_TOOLS = ["web_search", "python", "terminal", "edit_file", "render_html"]


def _today():
    return _dt.date.today().isoformat()


def _load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _known_models(catalog_path, agents_file):
    """Valid model choices = existing agent aliases + catalog model ids."""
    known = set()
    try:
        ag = _load_json(agents_file)
        for a in ag.get("agents", []):
            if a.get("model_id"):
                known.add(a["model_id"])
    except (OSError, json.JSONDecodeError):
        pass
    try:
        cat = _load_json(catalog_path)
        for m in cat.get("models", []):
            if m.get("id"):
                known.add(m["id"])
    except (OSError, json.JSONDecodeError):
        pass
    return sorted(known)


def _slugify(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "agent"


def _prompt(label, default="", choices=None):
    hint = f" [{default}]" if default else ""
    if choices:
        print(f"{label}{hint} ({', '.join(choices)}): ", end="")
    else:
        print(f"{label}{hint}: ", end="")
    val = input().strip()
    return val or default


def _collect_interactive(args):
    """Prompt for any fields not given via flags (tty only)."""
    name = args.name or _prompt("Agent display name", required=True)
    if not name:
        raise SystemExit(2)
    agent_id = args.id or _slugify(name)
    roles = list(ROLE_TEMPLATES.keys())
    role = (args.role or _prompt("Role template", "generic", roles)).lower()
    if role not in ROLE_TEMPLATES:
        print(f"WARNING: unknown role '{role}', using 'generic'.", file=sys.stderr)
        role = "generic"
    models = _known_models(args.catalog, args.agents_file)
    model = args.model or _prompt("Model id / alias", models[0] if models else "", models)
    tools_csv = args.tools
    if not tools_csv:
        tools_csv = _prompt("Tools (comma-separated)", ",".join(ROLE_TEMPLATES[role][2]))
    return name, agent_id, role, model, tools_csv


def _build_entry(name, agent_id, role, model, tools, blurb, persona,
                 emoji, color, max_tool_calls):
    tpl = ROLE_TEMPLATES.get(role, ROLE_TEMPLATES["generic"])
    return {
        "id": agent_id,
        "name": name,
        "emoji": emoji or tpl[3],
        "color": color or tpl[4],
        "model_id": model,
        "temperature": 0.7,
        "max_tokens": 0,
        "blurb": blurb or tpl[0],
        "persona": persona or tpl[1],
        "reasoning": "default",
        "tools": tools,
        "run_tools_locally": True,
        "max_tool_calls": max_tool_calls,
        "rag": False,
        "rag_kb_id": "",
    }


def _goal_skeleton(name, blurb):
    return (
        f"# {name} - 0 goals (set {_today()}, onboarded)\n\n"
        f"Focus: {blurb}\n\n"
        "_No goals set yet. Orchestrator drafts at next cycle kickoff._\n"
    )


def _leaf_index(name, agent_id):
    return (
        f"# {name} ({agent_id}) - leaf index\n\n"
        f"Onboarded {_today()}. Keep evidence leaves here; each small enough to read whole.\n"
    )


def _insert_index_line(index_path, agent_id, blurb):
    """Insert a sub-index bullet after the last existing one under '## Sub-indexes'.
    Returns (changed: bool, new_line)."""
    line = f"- -> memory/{agent_id}/INDEX.md   {blurb[:60]}"
    if not os.path.exists(index_path):
        with open(index_path, "w", encoding="utf-8") as fh:
            fh.write(f"# MEMORY INDEX\n\n## Sub-indexes\n{line}\n")
        return True, line
    with open(index_path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    # find '## Sub-indexes' then the contiguous '- -> memory/' block after it
    start = None
    for i, ln in enumerate(lines):
        if ln.strip() == "## Sub-indexes":
            start = i + 1
            break
    if start is None:
        lines.append("")
        lines.append("## Sub-indexes")
        lines.append(line)
        return True, line
    last_bullet = None
    for i in range(start, len(lines)):
        if lines[i].startswith("- -> memory/"):
            last_bullet = i
        elif lines[i].strip() != "" and last_bullet is not None:
            break
    if last_bullet is None:
        lines.insert(start, line)
    else:
        lines.insert(last_bullet + 1, line)
    with open(index_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return True, line


def _plan(args, name, agent_id, role, model, tools, entry):
    memory_dir = args.memory_dir
    goals_file = os.path.join(memory_dir, "goals", f"{agent_id}.md")
    leaf_dir = os.path.join(memory_dir, agent_id)
    leaf_index = os.path.join(leaf_dir, "INDEX.md")
    return {
        "name": name, "id": agent_id, "role": role, "model": model, "tools": tools,
        "agents_file": args.agents_file, "entry": entry,
        "goals_file": goals_file, "leaf_dir": leaf_dir, "leaf_index": leaf_index,
        "index_md": os.path.join(memory_dir, "INDEX.md"),
    }


def _print_plan(p, known_models):
    print(f"\n=== ONBOARD PLAN: {p['name']} ({p['id']}) ===")
    print(f"role={p['role']}  model={p['model']}  tools={p['tools']}")
    if p["model"] not in known_models:
        print(f"  [warn] model '{p['model']}' not in catalog/aliases (proceed only with --force)")
    print(f"1. agents.json : add entry id='{p['id']}' -> {p['agents_file']}")
    print(f"2. leaf index  : {p['leaf_index']}")
    print(f"3. goal file   : {p['goals_file']}")
    print(f"4. INDEX line  : in {p['index_md']}")


def _execute(p, no_commit=False):
    # 1) agents.json entry
    data = _load_json(p["agents_file"])
    before = len(data["agents"])
    if any(a.get("id") == p["id"] for a in data["agents"]):
        print(f"ERROR: agent id '{p['id']}' already exists in agents.json.", file=sys.stderr)
        return 2
    data["agents"].append(p["entry"])
    with open(p["agents_file"], "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)
    print(f"  agents.json: added '{p['id']}' ({before} -> {len(data['agents'])})")

    # 2) leaf index
    os.makedirs(p["leaf_dir"], exist_ok=True)
    with open(p["leaf_index"], "w", encoding="utf-8") as fh:
        fh.write(_leaf_index(p["name"], p["id"]))
    print(f"  leaf index: {p['leaf_index']}")

    # 3) goal file
    os.makedirs(os.path.dirname(p["goals_file"]), exist_ok=True)
    with open(p["goals_file"], "w", encoding="utf-8") as fh:
        fh.write(_goal_skeleton(p["name"], p["entry"]["blurb"]))
    print(f"  goal file: {p['goals_file']}")

    # 4) INDEX line
    _insert_index_line(p["index_md"], p["id"], p["entry"]["blurb"])
    print(f"  INDEX line: added in {p['index_md']}")

    if not no_commit:
        subprocess.run(["git", "add", "-A"], check=False, capture_output=True)
        r = subprocess.run(
            ["git", "commit", "-m", f"onboard: {p['id']} added to fleet ({_today()})"],
            check=False, capture_output=True, text=True,
        )
        if r.returncode == 0:
            print(f"  committed: onboard: {p['id']}")
        else:
            print(f"  git commit skipped (rc={r.returncode}): {(r.stderr or r.stdout).strip()[:100]}", file=sys.stderr)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Onboard a new fleet agent end-to-end.")
    ap.add_argument("--name", help="display name")
    ap.add_argument("--id", help="agent id (default: slug of name)")
    ap.add_argument("--role", choices=list(ROLE_TEMPLATES.keys()), help="role template")
    ap.add_argument("--model", help="model id / alias")
    ap.add_argument("--tools", help="comma-separated tool subset")
    ap.add_argument("--blurb", help="override blurb")
    ap.add_argument("--persona", help="override persona")
    ap.add_argument("--emoji", help="override emoji")
    ap.add_argument("--color", help="override hex color")
    ap.add_argument("--max-tool-calls", type=int, default=99)
    ap.add_argument("--force", action="store_true", help="allow model not in catalog/aliases")
    ap.add_argument("--dry-run", action="store_true", help="print plan only, change nothing")
    ap.add_argument("--no-commit", action="store_true", help="skip git commit")
    ap.add_argument("--agents-file", default="agents.json")
    ap.add_argument("--memory-dir", default="memory")
    ap.add_argument("--catalog", default=DEFAULT_CATALOG)
    args = ap.parse_args(argv)

    if not os.path.exists(args.agents_file):
        print(f"ERROR: agents file not found: {args.agents_file}", file=sys.stderr)
        return 3

    # Interactive only when tty AND name not supplied.
    interactive = sys.stdin.isatty() and not args.name
    if interactive:
        try:
            name, agent_id, role, model, tools_csv = _collect_interactive(args)
        except EOFError:
            print("ERROR: interactive mode needs a tty; pass flags instead.", file=sys.stderr)
            return 2
    else:
        if not args.name:
            ap.error("--name is required in non-interactive mode")
            return 2
        name = args.name
        agent_id = args.id or _slugify(name)
        role = (args.role or "generic").lower()
        model = args.model or _known_models(args.catalog, args.agents_file)[0]
        tools_csv = args.tools or ",".join(ROLE_TEMPLATES[role][2])

    tools = [t.strip() for t in tools_csv.split(",") if t.strip()]
    bad_tools = [t for t in tools if t not in ALL_TOOLS]
    if bad_tools:
        print(f"WARNING: unknown tool(s) {bad_tools} (allowed: {ALL_TOOLS}).", file=sys.stderr)

    known_models = _known_models(args.catalog, args.agents_file)
    tpl = ROLE_TEMPLATES.get(role, ROLE_TEMPLATES["generic"])
    entry = _build_entry(name, agent_id, role, model, tools,
                         args.blurb or tpl[0], args.persona or tpl[1],
                         args.emoji, args.color, args.max_tool_calls)
    p = _plan(args, name, agent_id, role, model, tools, entry)

    if p["model"] not in known_models and not args.force:
        print(f"ERROR: model '{p['model']}' not in catalog/aliases. Known: {known_models}", file=sys.stderr)
        print("       Add --force to override.", file=sys.stderr)
        return 2

    if args.dry_run:
        _print_plan(p, known_models)
        print("[dry-run] no files changed, no commit.")
        return 0

    if interactive:
        ans = input(f"Confirm onboarding of {name} ({agent_id})? [yes/no] ")
        if ans.strip().lower() not in ("y", "yes"):
            print("Aborted.")
            return 0

    print(f"Executing onboarding of {p['name']}...")
    return _execute(p, no_commit=args.no_commit)


if __name__ == "__main__":
    sys.exit(main())