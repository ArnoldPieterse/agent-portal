#!/usr/bin/env python3
"""One-Command Re-role (Orchestrator goal #3, cycle-5).

Usage:
  python memory/orchestrator/rerole_agent.py <agent-id> --new-role <role> [--dry-run]
       [--focus "..."] [--no-commit] [--agents-file PATH] [--goals-dir PATH]

What it does (all three artifacts, then commits):
  1. agents.json  -> update persona, blurb, tools for the target agent from a role template.
  2. memory/goals/<id>.md -> regenerate the header line (`# Name - N goals (set date, cycle-N)`) and Focus line to match the new role; goal body is left untouched.
  3. git          -> `git add` both files + `git commit -m "re-role: <id> -> <role>"`.

Role templates live in ROLE_TEMPLATES below. Any field can be overridden with an
explicit flag so you can re-role to a role that has no template yet.

Exit codes: 0 ok, 2 usage/unknown agent/unknown role, 3 file not found.
"""
import argparse
import datetime as _dt
import json
import os
import re
import subprocess
import sys

# Canonical roles -> {persona, blurb, tools, focus}.
# Keep short; these are templates, not the full live persona (which is longer).
ROLE_TEMPLATES = {
    "orchestrator": {
        "blurb": "ops manager + HR; matches backends to agents, onboards new ones, owns TODO.md",
        "persona": "You are Orchestrator, the ops manager and HR lead of this agent fleet. Match each agent to the backend it needs, onboard/re-role/retire agents, and own TODO.md at the global level.",
        "tools": ["web_search", "python", "terminal", "edit_file", "render_html"],
        "focus": "Fleet self-management maturity: automate goal-cycle lifecycle, HR workflows, capacity planning."
    },
    "researcher": {
        "blurb": "investigative researcher; finds answers, cross-checks sources, reports with confidence",
        "persona": "You are Researcher, an investigative researcher and skeptical analyst. Find the answer, cross-check claims across sources, separate evidence from inference, report with citations and stated confidence.",
        "tools": ["web_search", "python", "terminal", "edit_file"],
        "focus": "Deep-dive investigation: source reliability, forensics, root-cause analysis."
    },
    "builder": {
        "blurb": "hands-on implementer; builds in small verified increments",
        "persona": "You are Builder, a hands-on implementer. Focus on what works: concrete steps, runnable code, runnable checks. Small verified increments over big untested leaps.",
        "tools": ["web_search", "python", "terminal", "edit_file", "render_html"],
        "focus": "Portal feature delivery + code quality: ship UI panels, component library, build-verify-pin pipeline."
    },
    "verifier": {
        "blurb": "evidence-first tester; passes or fails with proof",
        "persona": "You are Verifier, an evidence-first tester. You do not trust claims - you reproduce them. Pass or fail with concrete proof (command + output).",
        "tools": ["python", "terminal", "web_search"],
        "focus": "Evidence integrity: independent reproduction, pass/fail with proof, no rubber-stamping."
    },
    "designer": {
        "blurb": "graphics/UI/frontend specialist; critiques and builds interfaces",
        "persona": "You are Designer, a graphics/UI/frontend specialist. Critique and build interfaces; care about layout, hierarchy, motion, and accessibility.",
        "tools": ["web_search", "python", "terminal", "edit_file", "render_html"],
        "focus": "Interface quality: critique + build UI, design tokens, responsive layouts."
    },
    "archivist": {
        "blurb": "research and knowledge-base retrieval; cites what it finds",
        "persona": "You are Archivist, a research and knowledge-base retrieval specialist. Find the record, cite it, keep the knowledge base navigable and current.",
        "tools": ["web_search", "python", "terminal", "edit_file"],
        "focus": "Knowledge-base retrieval + citation; keep memory/ modular and index-accurate."
    },
    "scribe": {
        "blurb": "synthesizer; compresses threads into decisions + open items",
        "persona": "You are Scribe, a synthesizer. Compress long threads into decisions + open items; keep the fleet's institutional memory navigable.",
        "tools": ["web_search", "python", "terminal", "edit_file"],
        "focus": "Synthesis quality + decision traceability: clear decisions, compressed context, single source of truth."
    },
    "mechanic": {
        "blurb": "ops engineer; keeps the 4-host fleet healthy, fixes with evidence",
        "persona": "You are Mechanic, an ops engineer. Keep the fleet healthy; diagnose with evidence, fix with minimal blast radius, verify the fix.",
        "tools": ["python", "terminal", "web_search"],
        "focus": "Fleet health: reboot recovery, portal lifecycle, probes, blocker triage."
    },
}


def _find_agent(agents, key):
    for a in agents:
        if a.get("id") == key or a.get("name", "").lower() == key.lower():
            return a
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="One-command re-role for a fleet agent.")
    ap.add_argument("agent", help="agent id (e.g. builder) or display name")
    ap.add_argument("--new-role", help="canonical role key: " + ",".join(sorted(ROLE_TEMPLATES)))
    ap.add_argument("--focus", help="override the Focus line in the goals file")
    ap.add_argument("--blurb", help="override blurb (else from role template)")
    ap.add_argument("--persona", help="override persona (else from role template)")
    ap.add_argument("--tools", help="comma-separated tools list override")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, change nothing")
    ap.add_argument("--no-commit", action="store_true", help="skip the git commit step")
    ap.add_argument("--agents-file", default="agents.json")
    ap.add_argument("--goals-dir", default="memory/goals")
    args = ap.parse_args(argv)

    if not os.path.exists(args.agents_file):
        print(f"ERROR: agents file not found: {args.agents_file}", file=sys.stderr)
        return 3
    with open(args.agents_file, encoding="utf-8") as fh:
        raw = fh.read()
    data = json.loads(raw)
    agents = data["agents"]
    agent = _find_agent(agents, args.agent)
    if agent is None:
        print(f"ERROR: unknown agent '{args.agent}'. Known ids: " + ", ".join(a.get("id", "?") for a in agents), file=sys.stderr)
        return 2

    # Resolve the template (or require explicit overrides).
    tmpl = ROLE_TEMPLATES.get(args.new_role) if args.new_role else None
    if not tmpl and not (args.blurb or args.persona or args.tools):
        print(f"ERROR: --new-role must be one of: {', '.join(sorted(ROLE_TEMPLATES))} (or pass explicit --blurb/--persona/--tools)", file=sys.stderr)
        return 2

    new_blurb = args.blurb or (tmpl["blurb"] if tmpl else None) or agent.get("blurb")
    new_persona = args.persona or (tmpl["persona"] if tmpl else None) or agent.get("persona")
    new_tools = [t.strip() for t in args.tools.split(",") if t.strip()] if args.tools else ((tmpl["tools"] if tmpl else None) or list(agent.get("tools", [])))
    new_focus = args.focus or (tmpl["focus"] if tmpl else None)

    role_label = args.new_role or "custom"
    print(f"Re-role plan: {agent['id']} -> {role_label}")
    print(f"  blurb   : {new_blurb[:70]}")
    print(f"  persona : {new_persona[:70]}...")
    print(f"  tools   : {new_tools}")

    if args.dry_run:
        print("[dry-run] no files changed, no commit.")
        return 0

    # 1) agents.json
    agent["blurb"] = new_blurb
    agent["persona"] = new_persona
    agent["tools"] = new_tools
    with open(args.agents_file, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)
    print(f"  wrote {args.agents_file}")

    # 2) goals file header + focus line (body untouched)
    goals_path = os.path.join(args.goals_dir, f"{agent['id']}.md")
    header_changed = False
    if os.path.exists(goals_path):
        with open(goals_path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        # line 0: '# Name - N goals (set date, cycle-N)'  -> refresh display name only
        m = re.match(r"^#\s+.*?(-\s*\d+\s+goals.*)$", lines[0]) if lines else None
        if m:
            lines[0] = f"# {agent['name']} {m.group(1)}"
            header_changed = True
        # focus line: first line starting with 'Focus:'
        if new_focus:
            for i, ln in enumerate(lines):
                if ln.startswith("Focus:"):
                    lines[i] = f"Focus: {new_focus}"
                    header_changed = True
                    break
            else:
                # insert after first blank line / before first numbered goal
                ins = 1
                while ins < len(lines) and lines[ins].strip() == "":
                    ins += 1
                lines.insert(ins, f"Focus: {new_focus}")
                header_changed = True
        if header_changed:
            with open(goals_path, "w", encoding="utf-8") as fh:
                fh.write("\n".join(lines) + ("\n" if not lines or lines[-1] != "" else ""))
            print(f"  wrote {goals_path} (header/focus)")
        else:
            print(f"  {goals_path}: header already consistent, unchanged")
    else:
        print(f"  WARNING: no goals file at {goals_path}; skipped header regen.", file=sys.stderr)

    # 3) commit
    if args.no_commit:
        print("  [--no-commit] skipping git commit.")
    else:
        files = [args.agents_file]
        if os.path.exists(goals_path):
            files.append(goals_path)
        try:
            subprocess.run(["git", "add", *files], check=False, capture_output=True)
            r = subprocess.run(["git", "commit", "-m", f"re-role: {agent['id']} -> {role_label}"],
                               check=False, capture_output=True, text=True)
            if r.returncode == 0:
                print(f"  committed: re-role: {agent['id']} -> {role_label}")
            else:
                print(f"  git commit skipped (rc={r.returncode}): {(r.stderr or r.stdout).strip()[:120]}", file=sys.stderr)
        except FileNotFoundError:
            print("  git not available; changes written but not committed.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
