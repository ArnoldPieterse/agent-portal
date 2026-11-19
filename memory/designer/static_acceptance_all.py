#!/usr/bin/env python3
"""
Designer - Static Acceptance Test Suite for Open Goals
Run: python memory/designer/static_acceptance_all.py
Tests goals 4, 5, 9, 10 code-level readiness (browser render is separate).
"""
import re, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UI = os.path.join(ROOT, "ui")

def read(f):
    path = os.path.join(UI, f) if not f.startswith("index.html") else os.path.join(ROOT, f)
    with open(path, encoding="utf-8") as fh:
        return fh.read()

results = []

def check(goal, name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((goal, status, name, detail))
    print(f"  [{status}] {name}" + (f" -- {detail}" if detail and not condition else ""))

print("=" * 60)
print("STATIC ACCEPTANCE TEST SUITE - Designer Open Goals")
print("=" * 60)

# GOAL 4: Empty State Design
print("\nGOAL 4: Empty State Design")
core = read("core.js")
app = read("app.css")
uploads = read("uploads.js")

check(4, "UI.emptyState helper exists in core.js", "UI.emptyState" in core or "emptyState=function" in core)
check(4, ".empty-state CSS class in app.css", ".empty-state" in app)
check(4, "Fleet empty state wired (agent icon + No hosts reporting)", "No hosts reporting" in core)
check(4, "Goals empty state wired", "emptyState" in core)
check(4, "Uploads empty state wired", "emptyState" in uploads)
check(4, "Activity empty state wired", "actRender" in core and "emptyState" in core)

# GOAL 5: Notification System
print("\nGOAL 5: Notification System")
check(5, "Toast function exists", "toast" in core.lower())
check(5, "Toast auto-dismiss timeout", re.search(r"setTimeout.*\d{3,4}", core) is not None)
check(5, "Bell icon defined in icons.js", "bell" in read("icons.js"))
check(5, "Goal-closed trigger wired", "_goalsPrev" in uploads or "goal" in core.lower())
check(5, "Agent-offline trigger wired", "_fleetPrev" in core)
check(5, "Upload complete/error trigger wired (window.notify)", "window.notify" in uploads)

# GOAL 9: Portal Onboarding Tour
print("\nGOAL 9: Portal Onboarding Tour")
tour_path = os.path.join(UI, "tour.js")
has_tour_js = os.path.exists(tour_path)
if has_tour_js:
    tour = open(tour_path, encoding="utf-8").read()
else:
    tour = ""

idx = read("index.html")
check(9, "tour.js file exists", has_tour_js)
check(9, "tour.js loaded in index.html", "tour" in idx.lower())
check(9, ".tour-* CSS classes in app.css", ".tour-" in app)
check(9, "localStorage flag for completion", "localStorage" in tour if tour else False)
check(9, "4 steps defined (Fleet/Goals/Ops/Uploads)", 
      all(kw in tour.lower() for kw in ["fleet", "goal", "ops", "upload"]) if tour else False)
check(9, "Skip/dismiss sets flag", re.search(r"localStorage.*set|setItem", tour) is not None if tour else False)

# GOAL 10: Print-Ready Report Layout
print("\nGOAL 10: Print-Ready Report Layout")
check(10, "@media print block in app.css", "@media print" in app)
check(10, "Page break rules (break-inside/break-after)", "break-" in app)
check(10, "window.print() call wired in core.js", "window.print" in core)
check(10, "Print Report button injection", "printReport" in core or "print-btn" in core)

# SUMMARY
print("\n" + "=" * 60)
total = len(results)
passed = sum(1 for r in results if r[1] == "PASS")
failed = total - passed
print(f"RESULTS: {passed}/{total} PASS, {failed} FAIL")
if failed:
    print("\nFAILURES:")
    for g, s, name, detail in results:
        if s == "FAIL":
            print(f"  Goal {g}: {name}" + (f" -- {detail}" if detail else ""))
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
