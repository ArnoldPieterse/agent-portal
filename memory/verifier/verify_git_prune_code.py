#!/usr/bin/env python3
"""Extract and display the git + prune handler code for static verification."""
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
lines = open(os.path.join(ROOT, "agent_portal.py"), encoding="utf-8").read().split("\n")

# Git status handler (line 2226 area)
print("=== _git_status() function ===")
for i in range(2225, 2260):
    if i < len(lines):
        print(f"{i+1:4d}: {lines[i]}")

print("\n=== GET /api/git dispatch (line 2400) ===")
for i in range(2398, 2410):
    if i < len(lines):
        print(f"{i+1:4d}: {lines[i]}")

print("\n=== POST /api/git dispatch (line 2719) ===")
for i in range(2717, 2745):
    if i < len(lines):
        print(f"{i+1:4d}: {lines[i]}")

print("\n=== _prune_todo() function (line 2149) ===")
for i in range(2148, 2215):
    if i < len(lines):
        print(f"{i+1:4d}: {lines[i]}")

print("\n=== POST /api/todo/prune dispatch (line 2699) ===")
for i in range(2697, 2720):
    if i < len(lines):
        print(f"{i+1:4d}: {lines[i]}")