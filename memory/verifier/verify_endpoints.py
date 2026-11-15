#!/usr/bin/env python3
"""Verifier: code-level verification of /api/git, /api/todo/prune, and other endpoints.
Goal 1 (smoke-test), Goal 2 (prune), Goal 3 (git) - static analysis when live access unavailable."""
import re, sys, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
src = open(os.path.join(ROOT, "agent_portal.py"), encoding="utf-8").read()
lines = src.split("\n")

print(f"agent_portal.py: {len(lines)} lines, {os.path.getsize(os.path.join(ROOT,'agent_portal.py'))} bytes")
print()

# Find all route handlers
routes = re.findall(r'@app\.route\(["\']([^"\']+)["\'][^)]*\)', src)
routes += re.findall(r'@app\.get\(["\']([^"\']+)["\'][^)]*\)', src)
routes += re.findall(r'@app\.post\(["\']([^"\']+)["\'][^)]*\)', src)
# Also find Flask-style or custom dispatch
routes += re.findall(r'path\s*==\s*["\']([^"\']+)["\']', src)
routes += re.findall(r'elif\s+path\s*==\s*["\']([^"\']+)["\']', src)

# Find def handlers
defs = re.findall(r'def\s+(\w+)\(', src)

print("=== ROUTES (from decorators + dispatch) ===")
for r in sorted(set(routes)):
    print(f"  {r}")
print(f"Total unique routes: {len(set(routes))}")
print()

# Git-specific
print("=== GIT-RELATED CODE ===")
git_lines = []
for i, l in enumerate(lines):
    if any(kw in l for kw in ['GIT_EXE', 'api/git', 'git_', 'def.*git']):
        git_lines.append(f"  {i+1:4d}: {l.rstrip()[:100]}")
for gl in git_lines[:30]:
    print(gl)
print(f"  ... ({len(git_lines)} total git-related lines)")
print()

# Prune-specific
print("=== PRUNE-RELATED CODE ===")
prune_lines = []
for i, l in enumerate(lines):
    if any(kw in l for kw in ['prune', 'TODO_completed', 'DONE_MAX_LINES', 'DONE_PART_SIZE', 'todo_done_parts']):
        prune_lines.append(f"  {i+1:4d}: {l.rstrip()[:100]}")
for pl in prune_lines[:30]:
    print(pl)
print(f"  ... ({len(prune_lines)} total prune-related lines)")

# Check for .gitignore
print()
gi = os.path.join(ROOT, ".gitignore")
if os.path.exists(gi):
    gi_content = open(gi).readlines()
    print(f"=== .gitignore: {len(gi_content)} lines ===")
    print("  " + "\n  ".join(l.rstrip() for l in gi_content[:20]))
    if len(gi_content) > 20:
        print(f"  ... ({len(gi_content)} total)")
else:
    print(".gitignore NOT FOUND")

# Check git repo existence
print()
git_dir = os.path.join(ROOT, ".git")
if os.path.isdir(git_dir):
    print(f".git/ EXISTS ({os.path.getsize(os.path.join(git_dir,'HEAD'))} byte HEAD)")
    try:
        head = open(os.path.join(git_dir, "HEAD")).read().strip()
        print(f"  HEAD: {head}")
    except Exception as e:
        print(f"  HEAD read error: {e}")
else:
    print(".git/ NOT FOUND")
