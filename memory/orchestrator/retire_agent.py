#!/usr/bin/env python3
"""Retirement Checklist Automation (Orchestrator goal #4, cycle-5).

Usage:
  python memory/orchestrator/retire_agent.py <agent-id> --dry-run
  python memory/orchestrator/retire_agent.py <agent-id>          # confirm + execute
       [--agents-file PATH] [--memory-dir PATH] [--no-commit]

What it does:
  DRY-RUN (default-safe): scans the workspace and prints a retirement checklist:
    - files to archive (goals file, agent memory dir)
    - references to update (other goal files mentioning the agent by name/id)
    - INDEX lines to strike (memory/INDEX.md + sub-indexes referencing the agent)
    - agents.json entry to remove

  CONFIRM (no --dry-run): executes the plan:
    1. archives memory/goals/<id>.md -> memory/goals/archive/<id>-<YYYY-MM-DD>.md
    2. renames memory/<id>/ -> memory/<id>_archived_<YYYY-MM-DD>/  (if dir exists)
    3. removes the agent entry from agents.json
    4. strikes (prefixes with ~~) INDEX lines referencing the agent in memory/INDEX.md
       and any sub-index under memory/*/INDEX.md that mention the agent id or name.
    5. appends a retirement note to TODO.md.

Exit codes: 0 ok, 2 usage/unknown agent, 3 file not found.
"""
import argparse
import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import sys


def _find_agent(agents, key):
    for a in agents:
        if a.get("id") == key or a.get("name", "").lower() == key.lower():
            return a
    return None


def _today():
    return _dt.date.today().isoformat()


def _scan_references(memory_dir, agent_id, agent_name):
    """Return list of (file_path, line_number, line_text) for lines mentioning the agent."""
    refs = []
    id_pat = re.compile(rf"\b{re.escape(agent_id)}\b", re.IGNORECASE)
    name_pat = re.compile(rf"\b{re.escape(agent_name)}\b", re.IGNORECASE)

    # Scan all .md files under memory/ (skip the agent's own dir and archive)
    skip_dirs = {os.path.join(memory_dir, agent_id), os.path.join(memory_dir, f"{agent_id}_archived")}
    for root, dirs, files in os.walk(memory_dir):
        if any(root == sd or root.startswith(sd + os.sep) for sd in skip_dirs):
            continue
        for fname in files:
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, encoding="utf-8", errors="replace") as fh:
                    for i, line in enumerate(fh.read().splitlines(), 1):
                        if id_pat.search(line) or name_pat.search(line):
                            # skip the agent's own goals file (handled separately)
                            if fpath == os.path.join(memory_dir, "goals", f"{agent_id}.md"):
                                continue
                            refs.append((fpath, i, line.strip()[:100]))
            except OSError:
                pass
    return refs


def _scan_index_lines(memory_dir, agent_id, agent_name):
    """Return list of (file_path, line_number, line_text) for INDEX lines referencing the agent."""
    idx_refs = []
    id_pat = re.compile(rf"\b{re.escape(agent_id)}\b", re.IGNORECASE)
    name_pat = re.compile(rf"\b{re.escape(agent_name)}\b", re.IGNORECASE)

    index_files = [os.path.join(memory_dir, "INDEX.md")]
    for sub in sorted(os.listdir(memory_dir)):
        sub_idx = os.path.join(memory_dir, sub, "INDEX.md")
        if os.path.isfile(sub_idx):
            index_files.append(sub_idx)

    for fpath in index_files:
        try:
            with open(fpath, encoding="utf-8", errors="replace") as fh:
                lines = fh.read().splitlines()
            for i, line in enumerate(lines, 1):
                if (id_pat.search(line) or name_pat.search(line)) and not line.strip().startswith("~~"):
                    idx_refs.append((fpath, i, line.rstrip()))
        except OSError:
            pass
    return idx_refs


def _build_checklist(agents_data, agent, memory_dir):
    """Build the retirement checklist dict."""
    agent_id = agent["id"]
    agent_name = agent.get("name", agent_id)
    date = _today()

    files_to_archive = []
    goals_file = os.path.join(memory_dir, "goals", f"{agent_id}.md")
    if os.path.exists(goals_file):
        dest = os.path.join(memory_dir, "goals", "archive", f"{agent_id}-{date}.md")
        files_to_archive.append({"src": goals_file, "dst": dest, "action": "move"})

    agent_mem_dir = os.path.join(memory_dir, agent_id)
    if os.path.isdir(agent_mem_dir):
        dest = os.path.join(memory_dir, f"{agent_id}_archived_{date}")
        files_to_archive.append({"src": agent_mem_dir, "dst": dest, "action": "rename-dir"})

    refs = _scan_references(memory_dir, agent_id, agent_name)
    idx_refs = _scan_index_lines(memory_dir, agent_id, agent_name)

    return {
        "agent_id": agent_id,
        "agent_name": agent_name,
        "date": date,
        "files_to_archive": files_to_archive,
        "references_found": refs,
        "index_lines_to_strike": idx_refs,
        "agents_json_entry_removed": True,
    }


def _print_checklist(cl):
    print(f"\n=== RETIREMENT CHECKLIST: {cl['agent_name']} ({cl['agent_id']}) ===")
    print(f"Date: {cl['date']}\n")

    if cl["files_to_archive"]:
        print("FILES TO ARCHIVE:")
        for f in cl["files_to_archive"]:
            print(f"  [{f['action']}] {f['src']} -> {f['dst']}")
    else:
        print("FILES TO ARCHIVE: (none found)")

    if cl["index_lines_to_strike"]:
        print(f"\nINDEX LINES TO STRIKE ({len(cl['index_lines_to_strike'])}):")
        for fpath, ln, text in cl["index_lines_to_strike"][:20]:
            rel = os.path.relpath(fpath)
            print(f"  {rel}:{ln}  {text[:80]}")
        if len(cl["index_lines_to_strike"]) > 20:
            print(f"  ... and {len(cl['index_lines_to_strike']) - 20} more")
    else:
        print("\nINDEX LINES TO STRIKE: (none found)")

    if cl["references_found"]:
        print(f"\nREFERENCES IN OTHER FILES ({len(cl['references_found'])}) [informational, not auto-stripped]:")
        for fpath, ln, text in cl["references_found"][:15]:
            rel = os.path.relpath(fpath)
            print(f"  {rel}:{ln}  {text}")
        if len(cl["references_found"]) > 15:
            print(f"  ... and {len(cl['references_found']) - 15} more")
    else:
        print("\nREFERENCES IN OTHER FILES: (none found)")

    print(f"\nAGENTS.JSON: entry '{cl['agent_id']}' will be removed.")
    print("TODO.md: retirement note will be appended.\n")


def _execute(cl, agents_data, agents_file, memory_dir, no_commit=False):
    """Execute the retirement plan."""
    agent_id = cl["agent_id"]
    date = cl["date"]

    # 1) Archive files
    for f in cl["files_to_archive"]:
        src, dst, action = f["src"], f["dst"], f["action"]
        os.makedirs(os.path.dirname(dst), exist_ok=True) if not dst.endswith("/") else None
        if action == "move":
            shutil.move(src, dst)
            print(f"  archived: {src} -> {dst}")
        elif action == "rename-dir":
            shutil.move(src, dst)
            print(f"  renamed: {src} -> {dst}")

    # 2) Remove from agents.json
    data = json.loads(open(agents_file, encoding="utf-8").read())
    before = len(data["agents"])
    data["agents"] = [a for a in data["agents"] if a.get("id") != agent_id]
    after = len(data["agents"])
    with open(agents_file, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)
    print(f"  agents.json: removed '{agent_id}' ({before} -> {after} agents)")

    # 3) Strike INDEX lines
    for fpath, ln, _text in cl["index_lines_to_strike"]:
        with open(fpath, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        if 1 <= ln <= len(lines):
            orig = lines[ln - 1]
            if not orig.strip().startswith("~~"):
                lines[ln - 1] = "~~" + orig + ("~~" if not orig.endswith("~~") else "")
                with open(fpath, "w", encoding="utf-8") as fh:
                    fh.write("\n".join(lines) + "\n")
    print(f"  struck {len(cl['index_lines_to_strike'])} INDEX lines")

    # 4) TODO.md note
    todo_path = os.path.join(os.path.dirname(memory_dir), "TODO.md")
    if os.path.exists(todo_path):
        with open(todo_path, encoding="utf-8") as fh:
            content = fh.read()
        note = f"\n## RETIREMENT {date}: {cl['agent_name']} ({agent_id}) removed from fleet. Files archived to memory/goals/archive/ and memory/{agent_id}_archived_{date}/.\n"
        if not content.endswith("\n"):
            content += "\n"
        with open(todo_path, "w", encoding="utf-8") as fh:
            fh.write(content + note)
        print(f"  TODO.md: retirement note appended")

    # 5) Commit
    if not no_commit:
        try:
            subprocess.run(["git", "add", "-A"], check=False, capture_output=True)
            r = subprocess.run(
                ["git", "commit", "-m", f"retire: {agent_id} removed from fleet ({date})"],
                check=False, capture_output=True, text=True,
            )
            if r.returncode == 0:
                print(f"  committed: retire: {agent_id} ({date})")
            else:
                print(f"  git commit skipped (rc={r.returncode}): {(r.stderr or r.stdout).strip()[:100]}", file=sys.stderr)
        except FileNotFoundError:
            print("  git not available; changes applied but not committed.", file=sys.stderr)

    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Retirement checklist + executor for a fleet agent.")
    ap.add_argument("agent", help="agent id (e.g. scribe) or display name")
    ap.add_argument("--dry-run", action="store_true", help="print checklist only, change nothing")
    ap.add_argument("--agents-file", default="agents.json")
    ap.add_argument("--memory-dir", default="memory")
    ap.add_argument("--no-commit", action="store_true", help="skip git commit")
    args = ap.parse_args(argv)

    if not os.path.exists(args.agents_file):
        print(f"ERROR: agents file not found: {args.agents_file}", file=sys.stderr)
        return 3
    with open(args.agents_file, encoding="utf-8") as fh:
        data = json.load(fh)

    agent = _find_agent(data["agents"], args.agent)
    if agent is None:
        known = ", ".join(a.get("id", "?") for a in data["agents"])
        print(f"ERROR: unknown agent '{args.agent}'. Known ids: {known}", file=sys.stderr)
        return 2

    cl = _build_checklist(data, agent, args.memory_dir)

    if args.dry_run:
        _print_checklist(cl)
        print("[dry-run] no files changed, no commit.")
        return 0

    # Confirm prompt (skip in non-interactive / auto-loop context)
    import sys as _sys
    if _sys.stdin.isatty():
        ans = input(f"Confirm retirement of {agent['name']} ({agent['id']})? [yes/no] ")
        if ans.strip().lower() not in ("y", "yes"):
            print("Aborted.")
            return 0

    print(f"Executing retirement of {cl['agent_name']}...")
    return _execute(cl, data, args.agents_file, args.memory_dir, no_commit=args.no_commit)


if __name__ == "__main__":
    sys.exit(main())
