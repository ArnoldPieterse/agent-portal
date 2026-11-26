#!/usr/bin/env python3
"""
Knowledge-Stream Smoke Test (Builder, 2026-11-26)
=================================================
MIND LAB idea: "verify knowledge streams feed the portal." This is the concrete next step.

What a "knowledge stream" is in this codebase:
  * Deterministic veins (_ml_vein) harvested by collectors into `knowledge` each tick.
  * Ideas are broadcast into the agent portal via umq_add (op == "idea").
  * Accepted results solidify to memory/mind-lab/solidified.jsonl.

The single most failure-prone invariant: the PYTHON vein hash and the JS client's
ToInt32-XOR hash MUST agree bit-for-bit, else the server harvests veins the canvas
never renders (and vice-versa) = knowledge streams desync between brain and display.

This test EXECs the real MIND LAB source out of agent_portal.py (zero drift), in an
isolated temp HERE with a stubbed umq_add (no clobber of the live world.json, no server
import side-effects), then asserts:
  T1 vein determinism            same (x,y,seed) -> same result, repeatable
  T2 JS<->Python bit parity      independent ToInt32 oracle matches _ml_vein over a wide grid
  T3 knowledge streams flow       a collector on a vein yields earned>0 and raises knowledge
  T4 idea feeds the portal        op=idea -> fed_to_portal True + umq_add called with the text
  T5 solidify persists           accepted result lands in solidified.jsonl
  T6 full-stream determinism     same seed -> identical harvest over N ticks

Usage:  python memory/builder/knowledge_stream_smoke_test.py [--verbose]
Exit:   0 all pass, 1 any fail.
"""
import os
import sys
import json
import time
import shutil
import tempfile
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
PORTAL = os.path.normpath(os.path.join(HERE, "..", "..", "agent_portal.py"))

VERBOSE = "--verbose" in sys.argv

# ---------------------------------------------------------------------------
# Independent JS oracle: mirror ECMAScript ToInt32 + >>>0 exactly.
# ui/pages/mind-lab.html:70  function h32(x,y,seed){return ((x*73856093)^(y*19349663)^(seed*83492791))>>>0;}
# JS computes each product as a Number (double), XOR coerces operands via ToInt32,
# and the final >>>0 yields an unsigned 32-bit value.
# ---------------------------------------------------------------------------
def js_to_int32(d):
    n = int(d)                      # Trunc toward zero (exact integer doubles in our range)
    m = n & 0xFFFFFFFF              # mod 2^32
    return m - 0x100000000 if m >= 0x80000000 else m

def js_h32(x, y, seed):
    return (js_to_int32(x * 73856093) ^ js_to_int32(y * 19349663)
            ^ js_to_int32(seed * 83492791)) & 0xFFFFFFFF

def js_vein(x, y, seed):
    return js_h32(x, y, seed) % 23 == 0

# ---------------------------------------------------------------------------
# Extract + exec the REAL MIND LAB block from agent_portal.py in an isolated ns.
# ---------------------------------------------------------------------------
def load_mindlab(tmp_here):
    src = open(PORTAL, encoding="utf-8", errors="replace").read().splitlines()
    start = end = None
    for i, l in enumerate(src):
        if start is None and "# MIND LAB" in l:
            start = i
        elif start is not None and l.startswith("def start_group_run"):
            end = i
            break
    assert start is not None and end is not None, "MIND LAB block not found in agent_portal.py"
    block = "\n".join(src[start:end])
    calls = []
    def umq_add(text, mentions=None):
        calls.append({"text": text, "mentions": mentions})
        return {"id": "umq-stub-%d" % len(calls), "text": text}
    g = {"os": os, "json": json, "time": time, "threading": threading,
         "umq_add": umq_add, "HERE": tmp_here}
    exec(compile(block, PORTAL, "exec"), g)
    return g, calls

# ---------------------------------------------------------------------------
RESULTS = []
def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))
    print("  [%s] %s%s" % ("PASS" if cond else "FAIL", name, (" - " + detail) if detail and VERBOSE else ""))
    return cond

def main():
    tmp = tempfile.mkdtemp(prefix="ml_smoke_")
    try:
        g, calls = load_mindlab(tmp)
        _ml_vein = g["_ml_vein"]
        _ml_tick_ai = g["_ml_tick_ai"]
        _ml_read = g["_ml_read"]
        _mind_lab = g["_mind_lab"]

        print("T1 vein determinism")
        ok, mism = True, 0
        for seed in (1337, 1, 99999):
            for x in range(-40, 41, 7):
                for y in range(-40, 41, 7):
                    if _ml_vein(x, y, seed) != _ml_vein(x, y, seed):
                        mism += 1
        ok = (mism == 0)
        check("deterministic repeatable", ok, "mismatches=%d" % mism)

        print("T2 JS<->Python bit parity (knowledge-stream invariant)")
        checked = agree = 0
        for seed in (1337, 1, 99999, 4294967295):
            for x in list(range(-300, 301, 11)) + [255, -255, 12345 % 1000]:
                for y in list(range(-300, 301, 13)) + [255, -255]:
                    checked += 1
                    py = ((x * 73856093) ^ (y * 19349663) ^ (seed * 83492791)) & 0xFFFFFFFF
                    js = js_h32(x, y, seed)
                    if py == js and _ml_vein(x, y, seed) == js_vein(x, y, seed):
                        agree += 1
        check("bit-for-bit parity over grid", checked == agree,
              "%d/%d (incl. negative + >2^31 seeds)" % (agree, checked))

        print("T3 knowledge streams flow")
        w = _ml_read()  # fresh world under temp HERE
        # place an axiom collector and find a vein in its 3x3 to guarantee harvest
        hx, hy = g["ML_FACTIONS"]["axiom"]["home"]
        placed = None
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if _ml_vein(hx + dx, hy + dy, w["seed"]):
                    placed = (hx + dx, hy + dy)
                    break
            if placed:
                break
        assert placed, "no vein near axiom home for seed %d (test assumption)" % w["seed"]
        w["claims"]["%d,%d" % placed] = "axiom"
        w["buildings"].append({"id": "b0", "x": placed[0], "y": placed[1],
                               "type": "collector", "faction": "axiom",
                               "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
        # expected harvest = 2 per vein in the collector's 3x3 neighborhood
        exp = sum(2 for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                  if _ml_vein(placed[0] + dx, placed[1] + dy, w["seed"]))
        te0, t0 = w.get("total_earned", 0), w.get("tick_n", 0)
        earned = _ml_tick_ai(w)
        # NOTE: net knowledge delta != earned, because the same tick also spends
        # knowledge on AI builds. total_earned is harvest-only (never reduced by
        # spend), so it is the clean proof that exactly `earned` streamed in.
        check("collector harvests veins", earned >= exp and exp > 0,
              "earned=%d expected>=%d" % (earned, exp))
        check("streamed knowledge == earned", w.get("total_earned", 0) - te0 == earned,
              "total_earned +%d for earned=%d" % (w.get("total_earned", 0) - te0, earned))
        check("tick advanced", w.get("tick_n") == t0 + 1)

        print("T4 idea feeds the portal")
        calls.clear()
        r = _mind_lab("idea", {"text": "verify knowledge streams feed the portal"})
        check("op=idea ok + fed_to_portal", r.get("ok") and r.get("fed_to_portal") is True)
        check("umq_add broadcast fired", len(calls) == 1,
              "%d call(s)" % len(calls))
        if calls:
            check("broadcast text well-formed",
                  calls[0]["text"].startswith("[MIND LAB IDEA]")
                  and "verify knowledge streams feed the portal" in calls[0]["text"]
                  and "world tick" in calls[0]["text"], calls[0]["text"][:60])
        check("idea_reactor built for 'you'",
              any(b["type"] == "idea_reactor" and b["faction"] == "you"
                  for b in r["world"]["buildings"]))

        print("T5 solidify persists")
        w2 = _ml_read()
        # force >=3 buildings + reach a 5-tick boundary so a result card is minted
        for i, tname in enumerate(("collector", "collector", "researcher")):
            fn = list(g["ML_FACTIONS"].keys())[1]
            kx, ky = g["ML_FACTIONS"][fn]["home"]
            w2["claims"]["%d,%d" % (kx + i, ky)] = fn
            w2["buildings"].append({"id": "b%d" % (10 + i), "x": kx + i, "y": ky,
                                    "type": tname, "faction": fn, "ts": "t"})
        while not any(x.get("kind") == "efficiency-scan" for x in w2.get("results", [])):
            _ml_tick_ai(w2)
            if w2["tick_n"] > 60:
                break
        res = next((x for x in w2["results"] if x.get("kind") == "efficiency-scan"), None)
        check("result card minted", res is not None, res and res["id"])
        if res:
            g["_ml_write"](w2)   # persist in-memory world so solidify's _ml_read() sees it
            r5 = _mind_lab("solidify", {"id": res["id"], "accept": True})
            check("solidify ok + status set",
                  r5.get("ok") and next(x for x in r5["world"]["results"] if x["id"] == res["id"])["status"] == "solidified")
            sj = os.path.join(tmp, "memory", "mind-lab", "solidified.jsonl")
            okfile = os.path.exists(sj) and any(res["id"] in ln for ln in open(sj, encoding="utf-8"))
            check("solidified.jsonl has the record", okfile)

        print("T6 full-stream determinism (same seed -> same harvest)")
        def run_stream(seed, n=25):
            w = {"seed": seed, "knowledge": 50, "unlocks": ["collector", "researcher"],
                 "buildings": [], "claims": {}, "ideas": [], "results": [], "solidified": [],
                 "tick_n": 0, "next_id": 1}
            for fn, meta in g["ML_FACTIONS"].items():
                w["claims"]['%d,%d' % tuple(meta["home"])] = fn
            tot = 0
            for _ in range(n):
                tot += _ml_tick_ai(w)
            return (tot, len(w["buildings"]), tuple(sorted(w["claims"].keys())))
        a = run_stream(20261126)
        b = run_stream(20261126)
        check("identical harvest over 25 ticks", a == b, str(a) + " vs " + str(b))

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("-" * 48)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    print("SMOKE TEST: %d/%d checks passed" % (passed, len(RESULTS)))
    for name, ok, detail in RESULTS:
        if not ok:
            print("  FAILED: %s%s" % (name, (" - " + detail) if detail else ""))
    return 0 if passed == len(RESULTS) else 1

if __name__ == "__main__":
    sys.exit(main())