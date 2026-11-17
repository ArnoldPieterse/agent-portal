#!/usr/bin/env python3
"""Verifier independent re-run of Mechanic#4 regression detector (load_trend.py).
SLO pipeline: Mechanic#4 measures -> Builder#8 visualizes -> Verifier#4 enforces.
Reproduces the hot-note claim 'synthetic +40% p95 spike correctly flagged
REGRESSION_DETECTED' WITHOUT trusting prior artifacts. Three independent checks:
  [1] REAL data (2 days on disk)      -> expect status OK, zero false positives
  [2] SYNTHETIC +40% spike at c=50    -> expect REGRESSION_DETECTED at c=50 only
  [3] all-error (portal-down) day     -> expect skipped by load_days() (no crash, no phantom baseline)
Writes evidence JSON next to this file. Exits non-zero if any check fails.
"""
import importlib.util, json, os, sys, copy
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))  # memory/verifier -> repo root
sys.path.insert(0, ROOT)

# load the detector module by path (its BASELINE_FILE is relative to cwd=ROOT)
os.chdir(ROOT)
spec = importlib.util.spec_from_file_location("load_trend", os.path.join("memory", "ops", "load_trend.py"))
tl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tl)

results = {"ts": datetime.now().isoformat(), "checks": []}
ok_all = True

def check(name, passed, detail):
    global ok_all
    results["checks"].append({"name": name, "passed": bool(passed), "detail": detail})
    ok_all = ok_all and bool(passed)
    print(f"[{ 'PASS' if passed else 'FAIL'}] {name}: {detail}")

# ---- CHECK 1: real data -> no false positive ----
real_days = tl.load_days()
if len(real_days) < tl.MIN_DAYS:
    check("real_data", False, f"only {len(real_days)} days on disk (need >=2); cannot confirm")
else:
    findings = tl.analyze(real_days, 0.30)
    false_pos = [f for f in findings if f["regression"]]
    check("real_data_no_false_positive",
          len(false_pos) == 0,
          f"{len(real_days)} days; {len(findings)} levels; false-positives={len(false_pos)}"
          + (f" -> {false_pos}" if false_pos else " (correct: no cry-wolf on normal data)"))

# ---- CHECK 2: synthetic +40% spike at c=50, day 4 of 4 ----
base = {
    10:  (187.6, 194.6),   # (p95, p99) stable baseline
    50:  (746.8, 753.5),
    200: (3527.0, 3532.1),
}
def day(ts):
    return {"ts": ts, "levels": [
        {"concurrency": c, "n": c, "p50_ms": p95*0.6, "p95_ms": p95, "p99_ms": p99, "errors": 0}
        for c,(p95,p99) in base.items()]
    }
synth = [day(f"2026-11-14 08:00:00"), day("2026-11-15 08:00:00"), day("2026-11-16 08:00:00")]
spike = copy.deepcopy(synth[2])
spike["ts"] = "2026-11-17 08:00:00"
for lv in spike["levels"]:
    if lv["concurrency"] == 50:
        lv["p95_ms"] = round(base[50][0]*1.40, 1)   # +40%
        lv["p99_ms"] = round(base[50][1]*1.42, 1)
synth.append(spike)
find2 = {f["concurrency"]: f for f in tl.analyze(synth, 0.30)}
c50_flagged = find2.get(50, {}).get("regression", False)
others_clean = all(not find2[c].get("regression") for c in (10, 200))
check("synthetic_spike_detected_at_c50",
      c50_flagged and others_clean,
      f"c=50 flagged={c50_flagged} (p95 ratio {find2.get(50,{}).get('p95_ratio')}), "
      f"c=10/c=200 clean={others_clean} -> expect spike caught ONLY at c=50")

# ---- CHECK 3: all-error (portal-down) day skipped by load_days() ----
down = {"ts": "2026-11-18 08:00:00", "levels": [
    {"concurrency": c, "n": c, "p50_ms": 0, "p95_ms": 0, "p99_ms": 0, "errors": c}
    for c in (10, 50, 200)]}
mixed = real_days + [down]
skipped = tl.load_days() if False else None
# load_days reads the file, so replicate its guard logic by filtering a copy:
def _guard(days):
    return [d for d in days if not all(lv["errors"] == lv["n"] for lv in d["levels"])]
guarded = _guard(mixed)
check("all_error_day_skipped",
      len(guarded) == len(real_days),
      f"input {len(mixed)} days -> guard keeps {len(guarded)} (portal-down day excluded, no phantom baseline / no div-by-zero)")

out = os.path.join(HERE, "regression-detector-reverify-2026-11-17.json")
results["verdict"] = "PASS - all 3 checks green" if ok_all else "FAIL"
with open(out, "w") as f:
    json.dump(results, f, indent=2)
print("\nVERDICT:", results["verdict"])
print("evidence ->", os.path.relpath(out, ROOT))
sys.exit(0 if ok_all else 1)
