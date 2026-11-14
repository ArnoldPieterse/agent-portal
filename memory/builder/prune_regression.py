#!/usr/bin/env python3
"""builder/prune_regression.py - prune regression suite (Builder goal: 4 cases).

Covers: (1) all-complete section moves, (2) partially-open section stays,
(3) >240-line chunking math into todo_done_parts/, (4) idempotent double-run.
Runs against FIXTURES in a temp dir - never touches the real TODO.md.
Usage:  python memory/builder/prune_regression.py   (exit 0 = all PASS)
"""
import importlib.util, os, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
spec = importlib.util.spec_from_file_location("ap_under_test",
                                              os.path.join(ROOT, "agent_portal.py"))
ap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ap)

fails = []
def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ("  " + detail if detail and not cond else ""))
    if not cond: fails.append(name)

tmp = tempfile.mkdtemp(prefix="prune_regr_")
ap.TODO_FILE = os.path.join(tmp, "TODO.md")
ap.DONE_FILE = os.path.join(tmp, "TODO_completed.md")
ap.DONE_PART_DIR = os.path.join(tmp, "todo_done_parts")
ap.DONE_MAX_LINES = 240
ap.DONE_PART_SIZE = 200

def write_todo(body):
    open(ap.TODO_FILE, "w", encoding="utf-8").write(body)

def read(p):
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""

# ---- fixture: preamble + 3 sections (A all done, B mixed, C no boxes) ----
write_todo("""# TODO — fixture

## A all done
- [x] a1
- [x] a2
- [x] a3

## B mixed
- [x] b1
- [x] b2
- [ ] b3 open

## C no boxes
- plain note line
""")

# CASE 1: all-complete section moves
r = ap._prune_todo()
todo, done = read(ap.TODO_FILE), read(ap.DONE_FILE)
check("c1 moved_sections==1", r.get("moved_sections") == 1, str(r))
check("c1 A in completed file", "## A all done" in done and "- [x] a3" in done)
check("c1 A removed from TODO", "## A all done" not in todo)

# CASE 2: partially-open + no-box sections stay
check("c2 B stays (has open item)", "## B mixed" in todo and "- [ ] b3 open" in todo)
check("c2 C stays (no checkboxes)", "## C no boxes" in todo)
check("c2 completed file has no B/C", "## B mixed" not in done and "## C no boxes" not in done)

# CASE 3: chunking math - prefill DONE past threshold, prune a small section
big = ["# TODO — completed items (pruned from TODO.md)"] + [f"- [x] old line {i}" for i in range(250)]
open(ap.DONE_FILE, "w", encoding="utf-8").write("\n".join(big))
write_todo("# TODO — fixture\n\n## D all done\n- [x] d1\n- [x] d2\n")
r = ap._prune_todo()
dlines = read(ap.DONE_FILE).splitlines()
parts = sorted(os.listdir(ap.DONE_PART_DIR)) if os.path.isdir(ap.DONE_PART_DIR) else []
check("c3 one part created", parts == ["TODO_done_part_001.md"], str(parts))
if parts:
    plines = read(os.path.join(ap.DONE_PART_DIR, parts[0])).splitlines()
    check("c3 part holds 200 content lines", len(plines) == 201, f"got {len(plines)}")
    check("c3 part is oldest-first", "- [x] old line 0" in plines and "- [x] old line 199" in plines)
check("c3 DONE file back under 240", len(dlines) <= 240, f"got {len(dlines)}")
check("c3 newest section retained in DONE file", "## D all done" in read(ap.DONE_FILE))
check("c3 order preserved (old lines before D)",
      read(ap.DONE_FILE).find("old line") < read(ap.DONE_FILE).find("## D all done"))

# CASE 4: idempotent double-run
r = ap._prune_todo()
check("c4 second run moves nothing", r.get("moved_sections") == 0 and r.get("moved_items") == 0, str(r))
check("c4 no new part files", sorted(os.listdir(ap.DONE_PART_DIR) if os.path.isdir(ap.DONE_PART_DIR) else []) == ["TODO_done_part_001.md"])

shutil.rmtree(tmp, ignore_errors=True)
print()
if fails:
    print(f"RESULT: FAIL ({len(fails)}): {fails}"); sys.exit(1)
print("RESULT: ALL PASS (4/4 cases)")
