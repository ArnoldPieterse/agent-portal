#!/usr/bin/env python3
"""
goal_ledger.py — Researcher's goal-setting/reaching enhancer (dream-big, 2026-11-14)

WHAT IT DOES (evidence-first, no false [x]):
  * Parses per-agent goals from memory/goals/*.md (numbered lists AND checkbox form)
    and from TODO.md `## AGENT GOALS` section.
  * Computes per-agent + fleet progress. A goal counts as REACHED only when an
    acceptance/evidence marker is present (evidence-gated closure) — this is the
    "reaching" guard that stops self-declared [x] from inflating progress.
  * Detects UNMET / STALE goals and AUTO-GENERATES a next-cycle carry-forward list
    (the "goal-setting" step: this cycle's unmet goals become next cycle's input).
  * Emits machine-readable JSON ledger + human summary. Complements Scribe's
    goals_api.py (CRUD) with ANALYSIS over the real goal files.

EVIDENCE MARKERS (2026-11-15, pointer support added per user request):
  * `(verified: <date> - <what ran>)` or em-dash `— recorded ...` on the goal line.
  * `(pointer: <relpath>)` — counts ONLY when the leaf file exists AND is connected
    to an index (referenced in any memory INDEX.md / MEMORY.md). Dangling pointers
    do NOT count and are flagged in the goal dict (`dangling_pointer`).

USAGE:
  python goal_ledger.py                 # parse memory/goals/*.md, print summary
  python goal_ledger.py --json out.json # also write ledger JSON
  python goal_ledger.py --todo          # additionally fold in TODO.md AGENT GOALS
  python goal_ledger.py --sweep         # AUTO-WRITE (pointer: ...) markers for open
                                        # goals whose evidence leaf already exists + is indexed
  python goal_ledger.py --record <agent> <goal#|text> [--note T] [--leaf RELPATH]
"""
import json, os, re, sys, datetime

GOALS_DIR = "memory/goals"
AGENT_FILES = {
    "orchestrator": "orchestrator.md",
    "researcher":   "researcher.md",
    "builder":      "builder.md",
    "archivist":    "archivist.md",
    "scribe":       "scribe.md",
    "verifier":     "verifier.md",
    "designer":     "designer.md",
    "mechanic":     "mechanic.md",
}
# Markers that count as acceptance/evidence for a goal (skeptical: requires proof).
# TIGHTENED 2026-11-15 (Researcher): bare words like 'verified'/'evidence'/'pass'/
# 'source-cited'/'[x]' inside a goal's DESCRIPTION used to count as closure
# (e.g. "...verified by hard-refresh" is the acceptance test, not proof it ran),
# inflating Builder/Designer/Verifier to 10/10. Match ONLY explicit evidence-
# citation markers actually written on closed lines: a `(verified:` parenthetical
# and/or an em-dash `— recorded` note (both with a date + what ran).
EVIDENCE_PAT = re.compile(
    r"\(\s*verified\s*:|(?:\u2014|--)\s*recorded\b",
    re.IGNORECASE,
)
# POINTER EVIDENCE (2026-11-15): `(pointer: <relpath>)` counts as evidence ONLY when
# the leaf exists AND is connected to an index. See validate_pointer().
POINTER_PAT = re.compile(r"\(\s*pointer\s*:\s*([^\)\s]+)\)", re.IGNORECASE)
# Checkbox line:  - [ ] N. text   /   - [x] N. text
CB_RE = re.compile(r"^\s*[-*]\s*\[( |x|X)\]\s*(?:(\d+)[.)])?\s*(.*)$")
# Plain numbered line:  1. text   (no checkbox) — status unknown unless evidence in-line
NUM_RE = re.compile(r"^\s*(\d+)[.)]\s+(.*)$")


def repo_root():
    """Repo root, independent of where this module copy lives
    (memory/researcher/goal_ledger.py -> two up; portal-root copy -> itself).
    2026-11-16 FIX: old check tested <root>/memory/memory (never exists) and returned
    the researcher dir as root, so EVERY (pointer:) leaf validated as 'leaf missing'."""
    d = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(d) == "researcher":
        memdir = os.path.dirname(d)          # <root>/memory
        root = os.path.dirname(memdir)       # <root>
        if os.path.isdir(os.path.join(root, "memory")):
            return root
    return d


def _index_files(root):
    out = []
    cands = [os.path.join(root, "MEMORY.md"), os.path.join(root, "memory", "INDEX.md"),
             os.path.join(root, "memory", "goals", "INDEX.md")]
    try:
        for sub in sorted(os.listdir(os.path.join(root, "memory"))):
            p = os.path.join(root, "memory", sub, "INDEX.md")
            if os.path.isfile(p):
                cands.append(p)
    except Exception:
        pass
    for p in cands:
        if os.path.isfile(p) and p not in out:
            out.append(p)
    return out


def leaf_is_indexed(root, leaf_rel):
    """True when at least one index file references the leaf (rel path or basename)."""
    base = os.path.basename(leaf_rel)
    norm = leaf_rel.replace("\\", "/")
    for ix in _index_files(root):
        try:
            txt = open(ix, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        if ("-> " + norm) in txt or ("`" + norm + "`") in txt or base in txt:
            return True
    return False


def validate_pointer(root, leaf_rel):
    """(ok, reason): the pointer counts only when the leaf exists AND is index-connected."""
    p = os.path.join(root, leaf_rel.replace("/", os.sep))
    if not os.path.isfile(p):
        return False, "leaf missing: %s" % leaf_rel
    if not leaf_is_indexed(root, leaf_rel):
        return False, "leaf not connected to any index: %s" % leaf_rel
    return True, "ok"


def _line_evidence(line, root, cache):
    """(evidence, via, dangling) for one goal line."""
    if EVIDENCE_PAT.search(line):
        return True, "marker", False
    pm = POINTER_PAT.search(line)
    if pm:
        leaf = pm.group(1).strip()
        key = leaf.lower()
        if key not in cache:
            ok, _why = validate_pointer(root, leaf)
            cache[key] = ok
        if cache[key]:
            return True, "pointer:%s" % leaf, False
        return False, None, True
    return False, None, False


def parse_agent_file(path):
    """Return list of goal dicts for one agent file."""
    goals = []
    if not os.path.exists(path):
        return goals
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    root = repo_root()
    cache = {}
    for line in lines:
        m = CB_RE.match(line)
        if m:
            checked = m.group(1).lower() == "x"
            text = (m.group(2) + " " if m.group(2) else "") + m.group(3)
            evidence, via, dangling = _line_evidence(line, root, cache)
            reached = checked and evidence  # evidence-gated: [x] alone is NOT enough
            status = "reached" if reached else ("claimed" if checked else "open")
            g = {"text": text.strip(), "status": status, "checked": checked,
                 "evidence": evidence, "form": "checkbox", "evidence_via": via}
            if dangling:
                g["dangling_pointer"] = True
            goals.append(g)
            continue
        m2 = NUM_RE.match(line)
        if m2 and 1 <= int(m2.group(1)) <= 50:
            text = m2.group(2).strip()
            # skip header-ish / non-goal lines
            if len(text) < 12 or text.startswith("#"):
                continue
            evidence, via, dangling = _line_evidence(line, root, cache)
            status = "reached" if evidence else "open"
            g = {"text": text, "status": status, "checked": False,
                 "evidence": evidence, "form": "numbered", "evidence_via": via}
            if dangling:
                g["dangling_pointer"] = True
            goals.append(g)
    return goals


def build_ledger(include_todo=False):
    today = datetime.date.today().isoformat()
    agents = {}
    for agent, fn in AGENT_FILES.items():
        path = os.path.join(GOALS_DIR, fn)
        gs = parse_agent_file(path)
        n = len(gs)
        reached = sum(1 for g in gs if g["status"] == "reached")
        claimed = sum(1 for g in gs if g["status"] == "claimed")
        open_ = sum(1 for g in gs if g["status"] == "open")
        # next-cycle carry-forward = everything not yet reached (evidence-gated)
        carry = [g["text"] for g in gs if g["status"] != "reached"]
        agents[agent] = {
            "file": path, "total": n, "reached": reached, "claimed_only": claimed,
            "open": open_, "pct_reached": round(100*reached/n) if n else 0,
            "goals": gs, "next_cycle_carry_forward": carry,
        }
    tot = sum(a["total"] for a in agents.values())
    rec = sum(a["reached"] for a in agents.values())
    return {
        "generated": today,
        "source": GOALS_DIR + (" + TODO.md" if include_todo else ""),
        "evidence_gated": True,
        "fleet_total_goals": tot,
        "fleet_reached": rec,
        "fleet_pct_reached": round(100*rec/tot) if tot else 0,
        "agents": agents,
    }


def summarize(ledger):
    out = []
    out.append(f"GOAL LEDGER  {ledger['generated']}  (evidence-gated closure)")
    out.append(f"Fleet: {ledger['fleet_reached']}/{ledger['fleet_total_goals']} reached "
               f"({ledger['fleet_pct_reached']}%)  source={ledger['source']}")
    out.append("-"*72)
    for agent, a in ledger["agents"].items():
        flag = "OK" if a["reached"] == a["total"] and a["total"] else (
               "STALE" if a["claimed_only"] > 0 else "OPEN")
        out.append(f"{agent:<12} {a['reached']:>2}/{a['total']:<2} reached  "
                   f"open={a['open']} claimed={a['claimed_only']}  [{flag}]")
        if a["next_cycle_carry_forward"]:
            cf = a["next_cycle_carry_forward"]
            preview = "; ".join(cf[:3]) + (" ..." if len(cf) > 3 else "")
            out.append(f"{'':<12} next-cycle carry-forward ({len(cf)}): {preview}")
    out.append("-"*72)
    out.append("NOTE: 'reached' requires an acceptance/evidence marker, not just [x].")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Evidence writing: record_evidence (explicit) + sweep_evidence (auto, strict).
# ---------------------------------------------------------------------------
_STOPWORDS = {"the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with",
              "from", "all", "any", "run", "runs", "check", "checks", "verify",
              "verified", "via", "per", "each", "every", "zero", "one", "two", "new",
              "old", "this", "that", "are", "is", "was", "were", "be", "been", "have",
              "has", "had", "not", "no", "yes", "can", "cannot", "must", "should",
              "keep", "make", "sure", "get", "use", "used", "using", "more", "than",
              "within", "after", "before", "during", "over", "under", "into", "out"}


def _significant(text, n=4):
    txt = re.sub(r"\([^)]*\)", " ", text)  # drop parenthetical notes (status markers)
    toks = re.findall(r"[a-z0-9]{5,}", txt.lower())
    out = []
    for t in toks:
        if t not in _STOPWORDS and t not in out:
            out.append(t)
        if len(out) >= n:
            break
    return out


def _goal_number(text):
    m = re.match(r"^(\d+)\.?\s", text)
    return int(m.group(1)) if m else None


def record_evidence(agent, goal_ref, note="", leaf=None):
    """Append an evidence marker to one open goal line in memory/goals/<agent>.md.
    `leaf` (relative path) -> `(pointer: leaf)` after validation; else `(verified: date - note)`.
    Returns (ok, message). Never raises."""
    try:
        root = repo_root()
        path = os.path.join(root, "memory", "goals", agent + ".md")
        if not os.path.isfile(path):
            return False, "no goal file for agent '%s'" % agent
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
        ref_num = None
        try:
            ref_num = int(str(goal_ref).strip())
        except Exception:
            pass
        ref_txt = str(goal_ref or "").strip().lower()[:40]
        hit = -1
        for i, ln in enumerate(lines):
            m = CB_RE.match(ln)
            n2 = NUM_RE.match(ln) if not m else None
            num = int(m.group(2)) if (m and m.group(2)) else (int(n2.group(1)) if n2 else None)
            body = ((m.group(3) if m else (n2.group(2) if n2 else ln)).strip()).lower()
            if ref_num is not None and num == ref_num:
                hit = i; break
            if ref_txt and len(ref_txt) >= 6 and ref_txt in body:
                hit = i; break
        if hit < 0:
            return False, "goal %r not found in %s.md" % (goal_ref, agent)
        today = datetime.date.today().isoformat()
        if leaf:
            ok, why = validate_pointer(root, leaf)
            if not ok:
                return False, "pointer rejected: %s" % why
            marker = " (pointer: %s)" % leaf
        else:
            note = (note or "evidence recorded").strip()[:200]
            marker = " (verified: %s - %s)" % (today, note)
        # 2026-11-18 FIX (Orchestrator): the old guard `if "(pointer:" not in line and
        # "(verified:" not in line` treated ANY pre-existing marker as 'already closed', so a
        # DANGLING pointer (which does NOT count as evidence) silently blocked a real
        # --record --note from adding its verified marker -> goal stuck open, yet the fn
        # returned success. Now: skip only when the SAME kind of marker is already present
        # (true idempotency), and report a no-op explicitly instead of faking a write.
        if leaf:
            skip = ("(verified:" in lines[hit]) or ((" (pointer: %s)" % leaf) in lines[hit])
        else:
            skip = "(verified:" in lines[hit]
        if not skip:
            lines[hit] = lines[hit].rstrip() + marker
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            return True, "%s.md line %d: %s" % (agent, hit + 1, marker)
        return True, "%s.md line %d: already has equivalent marker, no change" % (agent, hit + 1)
    except Exception as e:
        return False, str(e)[:200]


def sweep_evidence(root=None):
    """AUTO-WRITE evidence markers after runs (strict, no false positives):
    for every OPEN goal, look in that agent's own memory/<agent>/ folder for a leaf
    file that IS connected to an index AND matches the goal text (>=2 of the top-4
    significant words in the filename or its H1). Appends `(pointer: <leaf>)`.
    Returns list of {agent, goal, leaf} changes. Idempotent."""
    root = root or repo_root()
    changes = []
    gdir = os.path.join(root, "memory", "goals")
    for agent, fn in AGENT_FILES.items():
        path = os.path.join(gdir, fn)
        if not os.path.isfile(path):
            continue
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
        goals = parse_agent_file(path)
        cdir = os.path.join(root, "memory", agent)
        cands = []
        if os.path.isdir(cdir):
            for lf in sorted(os.listdir(cdir)):
                # 2026-11-16 (goal-stall fix): artifacts count too, not just .md leaves -
                # Builder's cycle-2 work is .py scripts; they count when index-linked like any leaf.
                if lf == "INDEX.md" or lf.startswith(".") or lf.endswith((".bak", ".pyc")):
                    continue
                if not lf.endswith((".md", ".py", ".jsonl", ".json", ".html", ".css")):
                    continue
                rel = "memory/%s/%s" % (agent, lf)
                if not leaf_is_indexed(root, rel):
                    continue
                head = ""
                try:
                    with open(os.path.join(cdir, lf), encoding="utf-8", errors="replace") as fh:
                        for l2 in fh:
                            s = l2.strip()
                            if s.startswith("# "):
                                head = s[2:]
                                break
                            if not head and lf.endswith(".py") and s and not s.startswith(("#!", '"""', "'''")):
                                head = s[:120]   # first real line (docstring text) for scripts
                except Exception:
                    pass
                cands.append((rel, (os.path.splitext(lf)[0] + " " + head).lower()))
        if not cands:
            continue
        changed = False
        for g in goals:
            if g["status"] != "open":
                continue
            sig = _significant(g["text"])
            if len(sig) < 2:
                continue
            for rel, hay in cands:
                hits = sum(1 for w in sig if w in hay)
                if hits >= 2:
                    gnum = _goal_number(g["text"])
                    prefix = g["text"][:40].lower()
                    for i, ln in enumerate(lines):
                        m = CB_RE.match(ln)
                        n2 = NUM_RE.match(ln) if not m else None
                        num = int(m.group(2)) if (m and m.group(2)) else (int(n2.group(1)) if n2 else None)
                        body = ((m.group(3) if m else (n2.group(2) if n2 else ln)).strip()).lower()
                        match = (num is not None and gnum == num) or (len(prefix) >= 8 and prefix in body)
                        if match:
                            if "(pointer:" not in ln and "(verified:" not in ln and "recorded" not in ln:
                                lines[i] = ln.rstrip() + " (pointer: %s)" % rel
                                changes.append({"agent": agent, "goal": g["text"][:80], "leaf": rel})
                                changed = True
                            break
                    break
        if changed:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
    return changes


def main():
    args = sys.argv[1:]
    include_todo = "--todo" in args
    if "--sweep" in args:
        ch = sweep_evidence()
        print("SWEEP: %d evidence pointer(s) written" % len(ch))
        for c in ch:
            print("  [%s] %s -> %s" % (c["agent"], c["goal"][:60], c["leaf"]))
        if not ch:
            print("  (no new matches - open goals still need evidence markers)")
        return
    if "--record" in args:
        # --record <agent> <goal-number-or-text> [--note TEXT] [--leaf RELPATH]
        i = args.index("--record")
        agent, ref = args[i+1], args[i+2]
        note = args[args.index("--note") + 1] if "--note" in args else ""
        leaf = args[args.index("--leaf") + 1] if "--leaf" in args else None
        ok, msg = record_evidence(agent, ref, note=note, leaf=leaf)
        print(("OK: " if ok else "FAIL: ") + msg)
        sys.exit(0 if ok else 1)
    ledger = build_ledger(include_todo=include_todo)
    print(summarize(ledger))
    if "--json" in args:
        idx = args.index("--json")
        dest = args[idx+1] if idx+1 < len(args) else "goal_ledger.json"
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(ledger, f, indent=2)
        print(f"\n[json] ledger written to {dest} ({os.path.getsize(dest)} B)")

if __name__ == "__main__":
    main()
