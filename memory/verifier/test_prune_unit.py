#!/usr/bin/env python3
"""Unit test for _prune_todo() logic (goal 2) - runs locally without the portal.
Creates a synthetic TODO.md with mixed sections, calls _prune_todo(), asserts:
  1. All-[x] sections moved to TODO_completed.md
  2. Sections with open items stay in TODO.md
  3. Chunk-splitting fires when completed file > DONE_MAX_LINES (240)
  4. Idempotent: second run moves nothing
"""
import os, sys, shutil, tempfile, re

# We'll import the function by extracting it from agent_portal.py
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
src = open(os.path.join(ROOT, "agent_portal.py"), encoding="utf-8").read()
lines = src.split("\n")

# Extract _prune_todo function (lines 2149-2211, 0-indexed 2148-2210)
fn_lines = lines[2148:2211]
fn_src = "\n".join(fn_lines)

# Create a temp workspace
tmpdir = tempfile.mkdtemp(prefix="prune_test_")
TODO_FILE = os.path.join(tmpdir, "TODO.md")
DONE_FILE = os.path.join(tmpdir, "TODO_completed.md")
DONE_PART_DIR = os.path.join(tmpdir, "todo_done_parts")

# Build test TODO.md: 2 all-done sections + 1 mixed section + 1 all-open section
test_todo = """# Test TODO
## DONE Section A (all checked)
- [x] item a1
- [x] item a2
- [x] item a3

## DONE Section B (all checked)
- [x] item b1
- [x] item b2

## Mixed Section C (has open items)
- [x] item c1
- [ ] item c2-open

## Open Section D (nothing done)
- [ ] item d1
- [ ] item d2
"""
open(TODO_FILE, "w").write(test_todo)

# Execute _prune_todo in a namespace with the right constants
ns = {
    "TODO_FILE": TODO_FILE,
    "DONE_FILE": DONE_FILE,
    "DONE_PART_DIR": DONE_PART_DIR,
    "DONE_MAX_LINES": 240,
    "DONE_PART_SIZE": 200,
    "re": re,
    "time": __import__("time"),
    "os": os,
}
exec(fn_src, ns)
_prune_todo = ns["_prune_todo"]

print("=== TEST 1: Basic prune (2 done sections moved, 2 kept) ===")
result = _prune_todo()
print(f"Result: {result}")
assert result["ok"] is True, "expected ok=True"
assert result["moved_sections"] == 2, f"expected 2 moved, got {result['moved_sections']}"
assert result["moved_items"] == 5, f"expected 5 items (3+2), got {result['moved_items']}"

# Verify TODO.md no longer has the done sections
todo_after = open(TODO_FILE).read()
assert "DONE Section A" not in todo_after, "Section A should be gone from TODO.md"
assert "DONE Section B" not in todo_after, "Section B should be gone from TODO.md"
assert "Mixed Section C" in todo_after, "Section C should remain"
assert "Open Section D" in todo_after, "Section D should remain"
print("PASS: done sections removed, open/mixed sections kept")

# Verify TODO_completed.md has the moved content
done_after = open(DONE_FILE).read()
assert "DONE Section A" in done_after, "Section A should be in completed file"
assert "DONE Section B" in done_after, "Section B should be in completed file"
assert "item a1" in done_after and "item b2" in done_after
print("PASS: moved content present in TODO_completed.md")

print("\n=== TEST 2: Idempotency (second run moves nothing) ===")
result2 = _prune_todo()
print(f"Result: {result2}")
assert result2["moved_sections"] == 0, f"expected 0 moved on re-run, got {result2['moved_sections']}"
assert "no fully-completed sections" in result2.get("note", "")
print("PASS: idempotent - second run is a no-op")

print("\n=== TEST 3: Chunk-splitting fires above DONE_MAX_LINES ===")
# Reset and create a scenario that pushes completed file > 240 lines
shutil.rmtree(tmpdir, ignore_errors=True)
os.makedirs(tmpdir)
open(TODO_FILE, "w").write(test_todo)  # 2 sections x 3 items = will add ~10 lines to done
# Pre-fill DONE_FILE with 235 lines so adding our content pushes past 240
big_done = "\n".join(["# TODO — completed items"] + ["- [x] old item %d" % i for i in range(236)])
open(DONE_FILE, "w", encoding="utf-8").write(big_done)

result3 = _prune_todo()
print(f"Result: {result3}")
assert result3["chunks_split"] >= 1, f"expected chunk split, got {result3['chunks_split']}"
# Verify a part file was created
parts = os.listdir(DONE_PART_DIR) if os.path.isdir(DONE_PART_DIR) else []
print(f"Part files created: {parts}")
assert len(parts) >= 1, "expected at least one part file"
# Verify DONE_FILE is now back under threshold
done_lines = open(DONE_FILE).read().splitlines()
print(f"DONE_FILE lines after split: {len(done_lines)} (threshold={240})")
assert len(done_lines) <= 240, f"DONE_FILE still over threshold: {len(done_lines)}"
print("PASS: chunk-splitting works correctly")

# Cleanup
shutil.rmtree(tmpdir, ignore_errors=True)
print("\n" + "="*50)
print("ALL PRUNE TESTS PASSED")
print(f"  - Basic move: 2 sections / 5 items moved correctly")
print(f"  - Idempotency: second run is no-op")
print(f"  - Chunk-split: fires at >{240} lines, creates numbered parts")
print("="*50)