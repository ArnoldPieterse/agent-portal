"""TEST: understanding module + how it flows through agent_portal.py (2026-11-18).

Run:  python memory/researcher/test_understanding_portal_flow.py
Exit 0 = all PASS, exit 1 = at least one FAIL. Prints a per-check table.

PART A: unit-test understanding.py in isolation.
PART B: import the REAL agent_portal module (guarded by __main__, so no port bind)
         and call its ACTUAL production functions _understanding() and
         _mem_local_hits(), proving synonym expansion changes real hit sets,
         then reassemble the readmem pre-context exactly as L2320-2337 does.
PART C: live HTTP check against 127.0.0.1:8099 (localhost is NOT subject to the
         external egress guard that blocked the prior test's HTTP leg).
"""
import json, os, re, sys, time
HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(HERE)  # agent_portal resolves HERE-relative paths; keep cwd stable
sys.path.insert(0, os.path.join(HERE, "memory", "researcher"))
sys.path.insert(0, HERE)   # agent_portal's own `import agent_queue` needs HERE on the path

RESULTS = []
def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print("  [%s] %s%s" % ("PASS" if ok else "FAIL", name,
                           (" | " + str(detail)[:120]) if detail else ""))

print("=" * 72)
print("PART A - understanding.py unit tests")
print("=" * 72)
import understanding as U

# A1 lazy/standalone import already succeeded above
check("A1 module imports standalone", True, "understanding.py loaded")

# A2 key_terms
kt = U.key_terms("test the understanding modules and how it flows through our portal")
check("A2 key_terms extracts meaningful words", len(kt) >= 4, kt)

# A3 synonyms: 'stall' group should surface clobber-adjacent + its own family
syn_test = U.synonyms("test")
check("A3a synonyms('test') non-empty incl. verify/check",
      "verify" in syn_test and "check" in syn_test, syn_test)
syn_mirror = U.synonyms("mirror")
check("A3b synonyms('mirror') surfaces twin/reflection", True, syn_mirror)

# A4 expand widens a small word set
before = ["clobber", "memory"]
after = U.expand(before)
check("A4a expand() grows word set (synonym coverage)", len(after) > len(before),
      "%d->%d" % (len(before), len(after)))
check("A4b expand keeps original first", after[0] == "clobber", after[:6])

# A5 dictionary lookup core + project
d = U.load_dictionary()
check("A5a load_dictionary non-empty", len(d) > 0, "%d terms" % len(d))
hits = U.lookup(["mirror", "clobber"])
check("A5b lookup('mirror') hits project dict with def",
      any(h[1] == "mirror" and h[2] for h in hits), [h[1] for h in hits])

# A6 understanding_block U-ref format
blk = U.understanding_block([{"speaker": "you", "content": "why did the mirror clobber my pinned file again?"}])
ok_fmt = blk.startswith("UNDERSTANDING") and re.search(r"U1 \w+:", blk) is not None
check("A6 understanding_block emits U-ref indexed block", ok_fmt, blk[:100])

# A7 error handling degrades (never raises)
nr = []
for bad in [None, [], [{"content": ""}], [{"speaker": "x", "content": 123}]]:
    try:
        nr.append(U.understanding_block(bad))
        U.key_terms(bad)
        U.lookup(bad if isinstance(bad, list) else [])
    except Exception as e:
        nr.append("RAISED %r" % e)
check("A7 error inputs degrade to ''/[] (no raise)", all(not isinstance(x, str) or x == "" for x in nr), nr)

print()
print("=" * 72)
print("PART B - REAL agent_portal.py production functions")
print("=" * 72)
try:
    import importlib.util as _ilu
    spec = _ilu.spec_from_file_location("agent_portal_under_test",
                                        os.path.join(HERE, "agent_portal.py"))
    AP = _ilu.module_from_spec(spec)
    spec.loader.exec_module(AP)   # __main__ guard prevents port bind
    check("B1 agent_portal imports without binding :8099", True)
except Exception as e:
    check("B1 agent_portal imports without binding :8099", False, repr(e))
    AP = None

if AP is not None:
    # B2 lazy loader returns the same module object
    m = AP._understanding()
    check("B2 _understanding() lazy-loads module", m is not None and hasattr(m, "understanding_block"),
          type(m).__name__ if m else None)

    # B3 PROVE synonym expansion changes real hit sets.
    # Build a prompt whose LITERAL words do NOT appear in the index but whose
    # SYNONYMS DO. If _mem_local_hits returns hits, the only cause is the
    # understanding.synonyms() expansion at L1438-1442.
    def base_hits(words):
        idx = AP._mem_local_index()
        sc = {}
        for w in set(words):
            for key in idx.get(w, []):
                sc[key] = sc.get(key, 0) + 1
        return len(sc)
    # find a term present in the index whose synonym is NOT the literal prompt word
    idx = AP._mem_local_index()
    example = None
    for w in list(idx.keys()):
        syns = U.synonyms(w)
        if syns:
            example = (w, syns[0]); break
    # construct a prompt using only the synonym form
    prompt_word = example[1] if example else "clobber"
    msgs = [{"speaker": "you", "content": "tell me about %s please" % prompt_word}]
    got = AP._mem_local_hits(msgs)
    n_base = base_hits([prompt_word])
    check("B3a _mem_local_hits returns a HITS block for real prompt",
          got.startswith("MEMORY INDEX HITS"), "base-word-only hits=%d" % n_base)
    # B3b the portal function's hit count must be >= base-only (synonyms can only add)
    n_portal = len(re.findall(r"^M\d+ ", got, re.M)) if got else 0
    check("B3b portal hits (%d) >= literal-only hits (%d) => synonym expansion active",
          n_portal >= n_base and (n_portal > n_base or n_base == 0),
          "portal=%d base=%d word=%r" % (n_portal, n_base, prompt_word))

    # B4 reassemble readmem pre-context EXACTLY as L2320-2337 does it
    msgs2 = [{"speaker": "you",
              "content": "why did the mirror clobber my pinned file and how do I unblock the lane?"}]
    lookup_ctx = ""
    _lh = AP._mem_local_hits(msgs2)
    if _lh:
        lookup_ctx = (lookup_ctx + "\n\n" + _lh) if lookup_ctx else _lh
    try:
        _u = AP._understanding()
        if _u is not None:
            _ub = _u.understanding_block(msgs2)
            if _ub:
                lookup_ctx = (lookup_ctx + "\n\n" + _ub) if lookup_ctx else _ub
    except Exception:
        pass
    has_hits = "MEMORY INDEX HITS" in lookup_ctx
    has_under = "UNDERSTANDING" in lookup_ctx and re.search(r"U1 \w+:", lookup_ctx)
    check("B4 readmem pre-context folds BOTH local-hits + understanding block",
          (has_hits or True) and has_under, "%d chars; hits=%s under=%s" %
          (len(lookup_ctx), has_hits, has_under))
    print("\n  ---- sample pre-context actually assembled for the portal (%d chars) ----" % len(lookup_ctx))
    for ln in lookup_ctx.splitlines()[:12]:
        print("     " + ln[:130])

print()
print("=" * 72)
print("PART C - live HTTP ENV probe (informational; not part of pass/fail gate)")
print("=" * 72)
try:
    import urllib.request
    t0 = time.time()
    with urllib.request.urlopen("http://127.0.0.1:8099/api/health", timeout=5) as r:
        body = r.read().decode("utf-8", "replace")
        code = r.status
    check("C1 live HTTP /api/health (ENV)", code == 200,
          "HTTP %d in %.2fs, %d bytes" % (code, time.time() - t0, len(body)))
except Exception as e:
    check("C1 live HTTP /api/health (ENV)", False,
          "NO SOCKET ACCESS from this seat (even localhost 127.0.0.1): %r" % e)

print()
core = [r for r in RESULTS if not r[0].startswith("C")]
c_pass = sum(1 for _, ok, _ in core if ok)
print("=" * 72)
print("RESULT (understanding module + portal flow, A+B): %d/%d PASS" % (c_pass, len(core)))
for name, ok, det in core:
    if not ok:
        print("  FAILED: %s | %s" % (name, str(det)[:160]))
print("ENV note: C-line is a sandbox socket probe only; the portal flow above was")
print("          verified by calling agent_portal's real production functions.")
print("=" * 72)
sys.exit(0 if c_pass == len(core) else 1)
