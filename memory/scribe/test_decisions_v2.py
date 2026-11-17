"""Scribe goal #1 (Decision trace API v2: search+filter) - in-process verification.
Execs the _decisions_snapshot source from agent_portal.py with a stub namespace
(no network / no C:\\Users listing), cap removed, and asserts every returned item
satisfies its filter predicate. Run: python memory/scribe/test_decisions_v2.py"""
import os, re, time

t = open("agent_portal.py", encoding="utf-8").read()
s = t.index("def _decisions_snapshot")
e = t.index("\ndef ", s)
src = t[s:e].replace("out[:50]", "out")  # remove cap so we see full filtered sets
NS = {
    "os": os, "re": re, "time": time, "HERE": os.getcwd(),
    "load_agents": lambda: {"agents": [{"name": n} for n in
        ["Scribe", "Orchestrator", "Researcher", "Builder", "Verifier", "Designer", "Archivist", "Mechanic"]]},
}
exec(src, NS)
f = NS["_decisions_snapshot"]

full = f()["decisions"]
print("FULL total decisions:", len(full))

# NOTE: params must be parse_qs-shaped (dict of single-element lists), exactly as the
# HTTP route builds it via urllib.parse.parse_qs. Plain strings would break [0] indexing.
checks = [
    ("agent=Scribe", {"agent": ["Scribe"]}, lambda d: "scribe" in [o.lower() for o in d["owners"]]),
    ("status=closed", {"status": ["closed"]}, lambda d: d["status"] == "closed"),
    ("q=superseded", {"q": ["superseded"]}, lambda d: "superseded" in d["text"].lower()),
    ("since=2026-11-16", {"since": ["2026-11-16"]}, lambda d: (d["mtime"][:10] or "0000") >= "2026-11-16"),
    ("agent=Scribe+status=open", {"agent": ["Scribe"], "status": ["open"]},
     lambda d: "scribe" in [o.lower() for o in d["owners"]] and d["status"] == "open"),
]

all_ok = True
for name, p, pred in checks:
    r = f(p)["decisions"]
    ok = all(pred(d) for d in r)
    all_ok = all_ok and ok
    print(f"  {name:26s} n={len(r):3d}  {'PRED_OK' if ok else 'PRED_FAIL'}")

# subset property vs full set
full_keys = set((d["file"], d["line"]) for d in full)
for name, p, _ in checks:
    r = f(p)["decisions"]
    sub = all((d["file"], d["line"]) in full_keys for d in r)
    if not sub:
        all_ok = False
        print(f"  {name:26s} SUBSET_FAIL")

print("RESULT:", "ALL_PASS" if all_ok else "FAIL")
