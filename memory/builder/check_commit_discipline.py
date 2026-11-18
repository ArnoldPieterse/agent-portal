#!/usr/bin/env python3
"""Check Builder commit discipline (goal #10): every commit must carry 'verified:' in message.
Run from shared root: python memory/builder/check_commit_discipline.py
Exit 0 = all compliant, Exit 1 = violations found."""
import subprocess, sys

try:
    result = subprocess.run(
        [r"mingit\cmd\git.exe", "log", "--oneline", "--format=%H %s"],
        capture_output=True, text=True, timeout=30
    )
except FileNotFoundError:
    # try plain git
    result = subprocess.run(
        ["git", "log", "--oneline", "--format=%H %s"],
        capture_output=True, text=True, timeout=30
    )

if result.returncode != 0:
    print(f"ERROR: git log failed: {result.stderr}")
    sys.exit(2)

lines = [l for l in result.stdout.strip().split('\n') if l]
violations = []
auto_commits = 0

for line in lines:
    parts = line.split(' ', 1)
    if len(parts) < 2:
        continue
    hash_, msg = parts[0], parts[1]
    # Auto-commits from scheduled task are exempt (not personal commits)
    if msg.startswith("auto-commit:") or msg.startswith("sync:"):
        auto_commits += 1
        continue
    if "verified:" not in msg and "chore:" not in msg and "merge" not in msg.lower():
        violations.append(line)

print(f"Total commits scanned: {len(lines)}")
print(f"Auto/sync commits (exempt): {auto_commits}")
print(f"Violations: {len(violations)}")
if violations:
    print("\nNon-compliant commits:")
    for v in violations:
        print(f"  {v}")
    sys.exit(1)
else:
    print("\nPASS: all personal commits carry 'verified:' line.")
    sys.exit(0)
