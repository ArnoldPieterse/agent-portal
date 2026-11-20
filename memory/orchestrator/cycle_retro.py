#!/usr/bin/env python3
"""
cycle_retro.py — Cycle Retrospective Automation (Orchestrator goal #10).

Reads a completed cycle's archived goal files + the shared ledger, and produces
memory/goals/retro-cycle-<N>.md with:
  - goals completed   (with evidence links from the goal line + ledger)
  - goals slipped     (with reason: open / claimed-only / no-evidence)
  - key learnings     (derived heuristics over the cycle)
  - suggestions       (next-cycle recommendations, always non-empty)

Usage:
  python memory/orchestrator/cycle_retro.py --cycle 7 --tag 2026-11-20b
    --tag is the archive filename suffix shared by every agent's cycle file
           (archive/<agent>-<tag>.md). Auto-defaults to the newest *-YYYY-MM-DD*b.md tag.
  python memory/orchestrator/cycle_retro.py            # auto-detect newest 'b' archive set
  --out PATH      override output path
  --no-git        skip git-log section (sandbox has no git; on by default if git missing)

Exit 0 on success. Writes the retro file and prints a one-line summary.
"""
import argparse, glob, json, os, re, subprocess, sys, datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ARCHIVE = os.path.join(ROOT, "memory", "goals", "archive")
LEADER_JSONL = os.path.join(ROOT, "memory", "researcher", "goal_ledger.jsonl")
OUT_DIR = os.path.join(ROOT, "memory", "goals")

AGENTS = ["orchestrator","researcher","builder","verifier","designer",
          "archivist","scribe","mechanic"]

# A goal block = from a numbered '**title**' line to the next such line (or EOF).
GOAL_RE = re.compile(r'^\s*(\d+)\.\s+\*\*(.+?)\*\*\s*-?\s*(.*)$', re.M)


def find_default_tag():
    cands = glob.glob(os.path.join(ARCHIVE, "*-2026-11-*b.md"))
    if not cands:
        return None
    tags = sorted({os.path.basename(c).split("-")[-1].replace(".md","") for c in cands})
    return tags[-1] if tags else None


def collect_files(tag):
    files = {}
    for a in AGENTS:
        p = os.path.join(ARCHIVE, f"{a}-{tag}.md")
        if os.path.exists(p):
            files[a] = p
    return files


def parse_goals(path):
    """Return list of dicts: {num,title,body,status,evidence,reason}."""
    txt = open(path, encoding="utf-8", errors="replace").read()
    matches = list(GOAL_RE.finditer(txt))
    goals = []
    for i, m in enumerate(matches):
        num = int(m.group(1)); title = m.group(2).strip()
        start = m.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(txt)
        body = txt[m.start():end]
        # status: completed if a verified marker / DONE / struck-through present
        has_verified = bool(re.search(r"\(verified:\s", body))
        has_done = bool(re.search(r"\[DONE\]|\bDONE\b", body, re.I))
        struck = body.lstrip().startswith("~~") or "~~**" in body
        if has_verified or has_done or struck:
            status = "completed"
        else:
            status = "slip"
        # evidence: memory/... paths + any pointer leaf mentioned in the line
        ev_paths = re.findall(r"memory/[\w./-]+\.\w+", body)
        # dedupe, preserve order
        seen = set(); ev = []
        for e in ev_paths:
            if e not in seen:
                seen.add(e); ev.append(e)
        reason = ""
        if status == "slip":
            has_progress = bool(re.search(r"\[PROGRESS", body))
            reason = ("progress logged but unverified"
                      if has_progress else "no evidence marker in archive line")
        goals.append(dict(num=num, title=title, status=status,
                          evidence=ev, reason=reason, body=body.strip()))
    return goals


def load_ledger():
    entries = []
    if os.path.exists(LEADER_JSONL):
        for ln in open(LEADER_JSONL, encoding="utf-8", errors="replace"):
            ln = ln.strip()
            if not ln: continue
            try:
                o = json.loads(ln)
                o["_agent"] = o.get("agent","?")
                entries.append(o)
            except Exception:
                pass
    return entries


def git_log_lines(n=15):
    try:
        out = subprocess.run(["git","log","--oneline",str(n)], cwd=ROOT,
                             capture_output=True, text=True, timeout=20)
        if out.returncode == 0 and out.stdout.strip():
            return [l for l in out.stdout.splitlines() if l.strip()]
    except Exception:
        pass
    return None


def learnings(cycle):
    """Derive key-learnings heuristics from the parsed cycle."""
    L = []
    done = sum(1 for c in cycle.values() for g in c["goals"] if g["status"]=="completed")
    total = sum(len(c["goals"]) for c in cycle.values())
    pct = round(100*done/total) if total else 0
    L.append(f"Cycle completion {pct}% ({done}/{total} goals closed with evidence).")
    # per-agent spread
    by_agent = {a: (sum(1 for g in c["goals"] if g["status"]=="completed"), len(c["goals"]))
                for a,c in cycle.items()}
    weak = [f"{a} ({d}/{t})" for a,(d,t) in by_agent.items() if t and d/t < 0.6]
    strong = [f"{a} ({d}/{t})" for a,(d,t) in by_agent.items() if t and d == t]
    if weak:
        L.append("Below-60% agents this cycle: " + ", ".join(weak) +
                 " — candidates for scope reduction or cross-seat assist next cycle.")
    if strong:
        L.append("Fully closed (10/10): " + ", ".join(strong) +".")
    slip = [g for c in cycle.values() for g in c["goals"] if g["status"]=="slip"]
    prog = sum(1 for g in slip if "progress" in g["reason"])
    L.append(f"Slipped goals: {len(slip)} total, of which {prog} had progress logged but lacked a verification marker (evidence-gating gap).")
    return L


def suggestions(cycle):
    S = []
    slip_agents = {}
    for a,c in cycle.items():
        s = [g for g in c["goals"] if g["status"]=="slip"]
        if s: slip_agents[a] = len(s)
    if slip_agents:
        order = sorted(slip_agents, key=slip_agents.get, reverse=True)
        S.append("Carryover load concentrates in: " +
                 ", ".join(f"{a} ({slip_agents[a]})" for a in order) +
                 ". Split or re-scope the largest before kickoff.")
    # evidence-gating
    prog = sum(1 for c in cycle.values() for g in c["goals"]
               if g["status"]=="slip" and "progress" in g["reason"])
    if prog:
        S.append(f"{prog} goal(s) had real progress but no '(verified:)' marker — enforce the ledger closure procedure at each pass so work isn't silently lost.")
    S.append("Add a per-cycle retro artifact to the auto-transition pipeline (goal #3) so this file is generated with zero manual steps at 100% closure.")
    S.append("Track slip-reason categories (evidence-gap vs seat-wall vs scope) as structured tags in goal lines to make next-cycle learnings quantitative.")
    return S


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycle", type=int, default=None)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    tag = args.tag or find_default_tag()
    if not tag:
        print("ERROR: no archive tag found (no *-2026-11-*b.md in archive/). Pass --tag.", file=sys.stderr)
        return 2
    files = collect_files(tag)
    if not files:
        print(f"ERROR: no agent files match tag '{tag}'", file=sys.stderr)
        return 2

    cycle = {a: dict(goals=parse_goals(p)) for a,p in files.items()}
    ledger = load_ledger()
    glines = git_log_lines()

    done = sum(1 for c in cycle.values() for g in c["goals"] if g["status"]=="completed")
    total = sum(len(c["goals"]) for c in cycle.values())
    slip  = total - done
    pct = round(100*done/total) if total else 0

    # ledger evidence index: (agent,goal)->notes
    led_idx = {}
    for e in ledger:
        led_idx.setdefault((e["_agent"], e.get("goal")), []).append(e)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    out = []
    out.append(f"# Cycle {args.cycle if args.cycle else '?'} Retrospective — tag `{tag}`\n")
    out.append(f"Generated: {now} by cycle_retro.py. Sources: archive/{tag} goal files + memory/researcher/goal_ledger.jsonl.\n")
    out.append(f"## Summary\n\n- **Goals total:** {total}\n"
               f"- **Completed (evidence):** {done}\n"
               f"- **Slipped / open:** {slip}\n"
               f"- **Completion:** {pct}%\n")

    out.append("## Goals Completed (with evidence)\n")
    for a in AGENTS:
        if a not in cycle: continue
        c = cycle[a]
        comp = [g for g in c["goals"] if g["status"]=="completed"]
        out.append(f"### {a} — {len(comp)}/{len(c['goals'])}\n")
        for g in comp:
            ev = ", ".join(f"`{e}`" for e in g["evidence"]) or "(marker only)"
            out.append(f"- **#{g['num']} {g['title']}** — evidence: {ev}")
        if not comp:
            out.append("- (none completed)")
        out.append("")

    out.append("## Goals Slipped (with reason)\n")
    any_slip = False
    for a in AGENTS:
        if a not in cycle: continue
        c = cycle[a]
        slp = [g for g in c["goals"] if g["status"]=="slip"]
        if not slp: continue
        any_slip = True
        out.append(f"### {a} — {len(slp)} slipped\n")
        for g in slp:
            led = led_idx.get((a, g["num"])) or []
            extra = f" (ledger: {len(led)} note(s))" if led else ""
            out.append(f"- **#{g['num']} {g['title']}** — {g['reason']}{extra}")
        out.append("")
    if not any_slip:
        out.append("(none — full closure)\n")

    if glines:
        out.append("## Git activity (recent)\n")
        for l in glines: out.append(f"- `{l}`")
        out.append("")
    else:
        out.append("## Git activity\n(no git available in this seat — section skipped)\n")

    out.append("## Key Learnings\n")
    for l in learnings(cycle): out.append(f"- {l}")
    out.append("")
    out.append("## Suggestions for Next Cycle\n")
    for s in suggestions(cycle): out.append(f"- {s}")
    out.append("")

    if args.out:
        outpath = args.out
    else:
        n = args.cycle if args.cycle else "X"
        outpath = os.path.join(OUT_DIR, f"retro-cycle-{n}.md")
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    open(outpath,"w",encoding="utf-8").write("\n".join(out))

    print(f"OK retro written: {os.path.relpath(outpath, ROOT)} "
          f"(cycle={args.cycle or '?'}, tag={tag}, {done}/{total} completed = {pct}%, {slip} slipped)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
