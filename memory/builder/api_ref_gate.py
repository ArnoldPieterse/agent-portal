#!/usr/bin/env python3
"""api_ref_gate.py - CI gate suite (A#3, 2026-11-18).
Runs archivist/gen_api_ref.py --diff: regenerates memory/portal/api-reference.md from
agent_portal.py and diffs against the previous doc. Removed routes = breaking change
-> exit 2 -> pre_commit_gate blocks the commit. Added routes are reported, non-breaking.
"""
import os, sys, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
r = subprocess.run([sys.executable, os.path.join(ROOT, "memory", "archivist", "gen_api_ref.py"), "--diff"],
                   capture_output=True, text=True)
sys.stdout.write(r.stdout or "")
sys.stderr.write(r.stderr or "")
sys.exit(0 if r.returncode == 0 else 1)
