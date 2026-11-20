#!/usr/bin/env python3
"""Acceptance test for Scribe goal #9: Institutional Memory Search."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from memory_search import search_memory

queries = [
    ("hotload", ["hotload"]),
    ("winrm reboot", ["winrm", "reboot"]),
    ("designer animation", ["designer", "animation"]),
    ("goal ledger", ["ledger", "goal"]),
    ("mirror revert", ["mirror", "revert"]),
    ("cycle narrative", ["narrative", "cycle"]),
    ("stall watchdog", ["stall", "watchdog"]),
    ("agents.json alias", ["agents", "alias"]),
    ("portal upload", ["upload", "portal"]),
    ("knowledge distill", ["distill", "knowledge"]),
    ("fleet health", ["fleet", "health"]),
]

passed = 0
for q, expected_terms in queries:
    results = search_memory(q, top=5)
    # Acceptance: no false negatives - at least one result must contain an expected term
    # (in path or snippet). This verifies the search finds relevant files.
    if not results:
        print(f"FAIL: '{q}' -> NO RESULTS")
        continue
    all_text = " ".join((r["path"] + " " + r["snippet"]).lower() for r in results)
    if any(exp in all_text for exp in expected_terms):
        print(f"PASS: '{q}' -> {results[0]['path']} (score={results[0]['score']}, {len(results)} results)")
        passed += 1
    else:
        print(f"FAIL: '{q}' -> top={results[0]['path']} but no expected term in any of {len(results)} results")

print(f"\n{'='*50}")
print(f"Results: {passed}/{len(queries)} passed")
if passed >= 10:
    print("ACCEPTANCE PASS (>=10 queries return relevant results)")
else:
    print("ACCEPTANCE FAIL")
