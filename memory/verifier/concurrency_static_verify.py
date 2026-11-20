#!/usr/bin/env python3
"""Static concurrency leg for Verifier goal #5 (cycle-8 Concurrency Verification).

The live leg (3 simultaneous /api/chat -> confirm serialization) needs :8099 egress and is
wall-blocked in a sandbox seat (see memory/ops/blockers.md). This module verifies the STATIC
safety invariant that the portal's own docstring asserts (agent_portal.py ~L2528):

    "Concurrency is safe: journal writes take _journal_lock per event, memory RMWs take
     _lock, UMQ takes _umq_lock - no lock is ever held across a generation."

We check that invariant structurally: for every `with <lock>:` block in agent_portal.py,
capture the held body and FAIL if it contains a model-generation call (stream_chat /
run_turn_captured / the underlying LLM turn). If NO lock-hold spans a generation, the
parallel_slots=1 design is sound by construction: overlapping turns only ever race on
short, per-event critical sections.

Also reports the parallel execution topology (ThreadPoolExecutor fan-out) so the report
distinguishes 'agents overlap across hosts' from 'a single host serializes internally'.
"""
import re, sys, datetime, os

HERE = os.path.dirname(os.path.abspath(__file__))
# locate agent_portal.py by walking up absolute paths (sandbox _open can't take '..')
def _find_portal():
    d = HERE
    for _ in range(8):
        cand = os.path.join(d, "agent_portal.py")
        if os.path.exists(cand):
            return cand
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    raise FileNotFoundError("agent_portal.py not found walking up from %s" % HERE)
PORTAL = _find_portal()
OUT = os.path.join(HERE, "concurrency-test-2026-11-20.md")

# Lock names the docstring says are used for short critical sections.
LOCK_NAMES = ["_lock", "_journal_lock", "_umq_lock", "_history_lock",
              "_act_lock", "_fleet_lock", "_group_run_lock", "_autoloop_lock"]

# Markers of a model generation / LLM turn INSIDE the file. If any appears inside a
# lock-hold body, that lock is held across a generation -> invariant VIOLATED.
GEN_MARKERS = [
    ("stream_chat(", "stream_chat call"),
    ("run_turn_captured(", "run_turn_captured call"),
    ("_call_llm(", "_call_llm call"),
    ("client.chat.", "openai client.chat."),
    (".create(  # generation", "generation create"),
    ("completion =", "completion assignment"),
]

with open(PORTAL, encoding="utf-8") as f:
    lines = f.read().splitlines()

# --- find lock definitions ---
def_locks = {}
for i, l in enumerate(lines):
    m = re.match(r"^\s*(\w*lock\w*)\s*=\s*threading\.(RLock|Lock)\(\)", l)
    if m:
        def_locks[m.group(1)] = (i + 1, m.group(2))

# --- find every `with <lock>:` and capture the held body by indentation ---
def block_body(lines, start_idx):
    """Return list of lines in the with-body, based on indentation."""
    # header line is lines[start_idx]; find its indent
    hdr = lines[start_idx]
    m = re.match(r"^(\s*)with\b", hdr)
    base_indent = len(m.group(1))
    body = []
    j = start_idx + 1
    while j < len(lines):
        ln = lines[j]
        if not ln.strip():
            body.append(ln); j += 1; continue
        cur = len(ln) - len(ln.lstrip())
        if cur <= base_indent:
            break
        body.append(ln); j += 1
    return body

hits = []          # (lineno, lockname, [markers found])
with_blocks = 0
for i, l in enumerate(lines):
    for ln_name in LOCK_NAMES:
        if re.search(r"\bwith\s+%s\s*:" % re.escape(ln_name), l):
            body = block_body(lines, i)
            text = "\n".join(body)
            found = [desc for needle, desc in GEN_MARKERS if needle in text]
            with_blocks += 1
            hits.append((i + 1, ln_name, found))
            break

violations = [(no, lk, f) for (no, lk, f) in hits if f]
clean = [(no, lk) for (no, lk, f) in hits if not f]

# --- parallel topology: find ThreadPoolExecutor fan-out ---
topology = []
for i, l in enumerate(lines):
    if "ThreadPoolExecutor" in l:
        topology.append((i + 1, l.strip()))

# --- parallel_slots reference (Studio-side) ---
slot_refs = [(i + 1, l.strip()) for i, l in enumerate(lines) if "parallel_slots" in l]

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
ok = not violations

report = []
report.append("# Concurrency Verification (cycle-8 goal #5) - STATIC leg")
report.append("")
report.append("Generated: %s" % now)
report.append("Source: agent_portal.py (%d lines)" % len(lines))
report.append("")
report.append("## Invariant under test")
report.append('Docstring (agent_portal.py L2528): "Concurrency is safe: ... no lock is ever held across a generation."')
report.append("We structurally verify that NO `with <lock>:` block contains a model-generation call.")
report.append("")
report.append("## Lock definitions found")
for name in LOCK_NAMES:
    if name in def_locks:
        ln, kind = def_locks[name]
        report.append("- `%s` -> threading.%s  (L%d)" % (name, kind, ln))
report.append("")
report.append("## Lock-hold blocks scanned: %d" % with_blocks)
for no, lk in clean:
    report.append("- L%d `with %s:` -> body holds NO generation call  [OK]" % (no, lk))
report.append("")
if violations:
    report.append("## VIOLATIONS (%d) - lock held across a generation" % len(violations))
    for no, lk, f in violations:
        report.append("- L%d `with %s:` contains: %s  [FAIL]" % (no, lk, ", ".join(f)))
else:
    report.append("## Violations: 0 - every lock-hold is a short critical section")
report.append("")
report.append("## Parallel execution topology")
for no, txt in topology:
    report.append("- L%d: %s" % (no, txt))
report.append("- Design: one worker thread per agent; DIFFERENT Studio hosts truly overlap;")
report.append("  the local pair is serialized by White's Studio internally (parallel_slots=1).")
report.append("")
report.append("## parallel_slots references")
for no, txt in slot_refs:
    report.append("- L%d: %s" % (no, txt))
report.append("")
report.append("## Live leg (NOT run here - wall-blocked)")
report.append("3 simultaneous /api/chat -> confirm serialization in logs. Requires :8099 egress;")
report.append("sandbox seat returns WinError 10013 (see memory/ops/blockers.md, Verifier #4).")
report.append("Deferred to a non-sandbox White seat - do NOT re-probe from here.")
report.append("")
report.append("## STATIC RESULT: %s" % ("PASS" if ok else "FAIL"))
report.append("- 0 locks held across a generation: %s" % ("YES" if not violations else "NO"))
report.append("- invariant holds by construction: %s" % ("YES" if ok else "NO"))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(report) + "\n")

print("locks defined:", {k: v[1] for k, v in def_locks.items()})
print("with-blocks scanned:", with_blocks)
print("violations:", len(violations))
for no, lk, f in violations:
    print("  FAIL L%d %s -> %s" % (no, lk, f))
print("topology sites:", [t[0] for t in topology])
print("parallel_slots refs:", [s[0] for s in slot_refs])
print("RESULT:", "PASS" if ok else "FAIL")
print("report:", OUT)
sys.exit(0 if ok else 1)
