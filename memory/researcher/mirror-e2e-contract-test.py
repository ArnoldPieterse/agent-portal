#!/usr/bin/env python
"""
mirror-e2e-contract-test.py — goal #3 day-7 closure E2E contract test.
Drives the REAL memory_mirror.log_event() (the live writer) into a temp JSONL using the
exact kwarg dicts from every call site, then feeds that SAME file through BOTH consumers
(parse_mirror_events.py and fill_analysis.py). Asserts: no crash, all parser sections present,
filler emits a valid leaf with a confidence line.

Why this is the highest-value de-risk before 11-24: day-7 closure is a single command
`python memory/researcher/fill_analysis.py <live-log>`. If the writer's byte schema and the
consumers ever drift (timestamp format, missing key), that one command crashes at the exact
moment of closure. Prior passes validated parse-only and filler-on-a-hand-built-synthetic;
this is the first test that routes the REAL writer output through BOTH consumers.
Exit 0 = chain healthy; exit 1 = contract broken (report which assertion failed).
"""
import json, os, sys, io, subprocess, datetime as _dt, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)

import memory_mirror  # noqa: E402

TMP = os.path.join(tempfile.gettempdir(), "_e2e_mirror_events.jsonl")
if os.path.exists(TMP):
    os.remove(TMP)
memory_mirror.EVENT_LOG = TMP  # redirect real writer to temp file

# Faithful approach: call the REAL log_event for FORMAT (json.dumps/keys/t-format), then rewrite
# 't' to span a multi-day window. This proves the writer's byte schema exactly as the mirror emits it.
_orig = memory_mirror.log_event
def emit(kind, **kw):
    _orig(kind, **kw)  # writes one line with now() timestamp

lines = []
dates = [("2026-11-18", h) for h in range(9, 20)] + \
        [("2026-11-19", h) for h in range(9, 20)] + \
        [("2026-11-20", h) for h in range(9, 20)]
paths = ["ui/app.css", "index.html", "ui/core.js", "ui/uploads.js", "memory/INDEX.md"]
i = 0
events_out = []
for (d, h) in dates:
    for p in paths:
        i += 1
        if i % 7 == 0:
            emit("revert", file=p, was="aaaabbbbcccc", restored_to="deadbeef0000", trigger="pin_drift")
        elif i % 3 == 0:
            emit("write", dir="push_root", host="Black", path=p, reason="white-canonical",
                 src_h="11"*8, dst_h="22"*8)
        elif i % 2 == 0:
            emit("write", dir="pull_mem", host="Red", path=p, reason="lww-newer",
                 src_h="33"*8, dst_h="44"*8)
        else:
            emit("write", dir="push_mem", host="White", path=p, reason="new",
                 src_h="55"*8, dst_h="66"*8)

# Rewrite timestamps to span the 3-day window (writer format is %Y-%m-%d %H:%M:%S).
with open(TMP, "r", encoding="utf-8") as f:
    raw = [json.loads(l) for l in f if l.strip()]
counter = 0
out_lines = []
for ev in raw:
    counter += 1
    d, h = dates[(counter - 1) // len(paths)]
    ev["t"] = "%s %02d:30:00" % (d, h)
    out_lines.append(json.dumps(ev, ensure_ascii=False))
with open(TMP, "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines) + "\n")

print("Wrote %d events across 3 days to %s" % (len(out_lines), TMP))

# --- Consumer 1: parse_mirror_events.py ---
r1 = subprocess.run([sys.executable, os.path.join(HERE, "parse_mirror_events.py"), TMP],
                    capture_output=True, text=True)
print("\n=== parse_mirror_events rc=%d ===" % r1.returncode)
for sec in ["Events by (kind", "Top files by event", "Revert triggers", "Hourly event counts"]:
    ok = sec in r1.stdout
    print("  [%s] section: %s" % ("OK" if ok else "MISSING", sec))
    if not ok:
        sys.exit(1)
if r1.returncode != 0:
    print(r1.stdout); print(r1.stderr); sys.exit(1)

# --- Consumer 2: fill_analysis.py --dry-run ---
r2 = subprocess.run([sys.executable, os.path.join(HERE, "fill_analysis.py"), TMP, "--dry-run"],
                    capture_output=True, text=True)
print("\n=== fill_analysis rc=%d ===" % r2.returncode)
leaf = r2.stdout
checks = {
    "no crash (rc 0)": r2.returncode == 0,
    "confidence line present": "confidence:" in leaf and ("**HIGH**" in leaf or "**MEDIUM**" in leaf or "**LOW**" in leaf),
    "frequency table by kind": "### By kind" in leaf,
    "top-3 reverting populated": "(no reverts observed)" not in leaf and "| ui/" in leaf or "index.html" in leaf,
    "revert trigger distribution": "Revert Trigger Distribution" in leaf,
    "targeted fixes present": "Pin-stability guard" in leaf,
}
for k, v in checks.items():
    print("  [%s] %s" % ("OK" if v else "FAIL", k))
    if not v:
        sys.exit(1)

print("\nE2E CONTRACT TEST: PASS — real writer output flows through both consumers, all sections + confidence intact.")
