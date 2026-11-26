#!/usr/bin/env python3
"""convergence_e2e_drill.py - Forge goal #10: Full Convergence-Loop E2E Drill (CAPSTONE)

Proves the Fleet Autonomy Convergence claim end-to-end by simulating a WHOLE cycle
autonomously inside an isolated sandbox and driving the REAL lifecycle code paths:

    SEED            12 agents all at 10/10 reached  -> a closed cycle N
    CLOSE+CHAIR     real auto_cycle_transition.py --run  (archive + draft + kickoff)
    DRAFT+DISPATCH  fill new-cycle goals, run real forecast_engine.py -> next10.json
    REACH 100%      simulate the auto-loop sweeping every new goal to reached
    RE-CLOSE        real auto_cycle_transition.py --check  -> "ALL CLOSED" again
    HUMAN-TOUCH     audit: every step classified AUTONOMOUS vs HUMAN-REQUIRED

A "human touch" is any step that (a) invokes external admin/elevation, (b) hits an
approval gate, (c) requires a manual edit, or (d) FAILS (a failed autonomous step is
one that would need a human to proceed). The drill asserts total == 0 and, when not,
names the EXACT first step that needed a human.

The auto-loop's actual goal-work (stage REACH 100%) is inherently LLM/time-based and is
simulated; everything around it - close, chair, dispatch, re-close gating - drives real
code. That is the plumbing autonomy this capstone exists to prove.

Exit codes:
    0 = PASS (full loop closed with zero human touches)
    1 = FAIL (a step needed a human / an invariant broke)  -> first_human_step recorded
    2 = SETUP ERROR (sandbox could not be built)

Usage:
    python memory/forge/convergence_e2e_drill.py            # run the drill
    python memory/forge/convergence_e2e_drill.py --selftest # prove the detector fires

Outputs:
    appends one record to  memory/forge/convergence-drill.jsonl
    writes                memory/forge/convergence_e2e_drill_last.json
    writes                memory/forge/convergence-e2e-drill-report.md
"""
import os, re, sys, json, shutil, subprocess, datetime, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent            # memory/forge
ROOT = HERE.parent.parent                          # project root
TRANSITION_SRC = ROOT / "memory" / "orchestrator" / "auto_cycle_transition.py"
FORECAST_SRC = ROOT / "memory" / "goals" / "forecast_engine.py"
LEDGER_SRC = ROOT / "memory" / "researcher" / "goal_ledger.py"

DRILL_JSONL = HERE / "convergence-drill.jsonl"
LAST_JSON = HERE / "convergence_e2e_drill_last.json"
REPORT_MD = HERE / "convergence-e2e-drill-report.md"

AGENTS = ["orchestrator", "researcher", "builder", "archivist", "scribe", "verifier",
          "designer", "mechanic", "outlet", "pixel", "forge"]   # 11 seats (goal_ledger tracks these)
GOALS_PER_AGENT = 10
CYCLE_N = 19                                                    # the cycle we close in the drill
DRILL_DATE = "2026-11-27"

# Kinds that count as a HUMAN TOUCH.
HUMAN_KINDS = {"external_admin", "approval_block", "manual_edit_required",
               "subprocess_needs_human"}
AUTONOMOUS_KINDS = {"file_write", "file_read", "subprocess_local_ok", "simulated_loop"}

# Realistic per-agent goal templates for the DRAFTED new cycle (gives dispatch real content).
DRAFT_GOALS = {
    "orchestrator": ["Autonomous round-chair protocol idempotency guard",
                     "Seat-sizing recommendation replay vs outcomes",
                     "Dispatch-conformance gate wired to canary phase -1",
                     "Idle-floor enforcer escalation + mode-flip confirm",
                     "Convergence-plateau frequency-reduction safety invariant",
                     "Forecast-calibration backtest A/B over historical cycles",
                     "Regression-sentinel precision/recall boundary table",
                     "Cycle-transition roster snapshot diff audit",
                     "Level-up ETA projection from lane end times",
                     "Cross-lane assist-log contract fixture"],
    "researcher":   ["Slip-model v3 recalibration on cycle-19 data",
                     "Open-questions log SLA enforcement sweep",
                     "Evidence-quality trend report delta vs prior cycle",
                     "Source-citation provenance spot audit",
                     "Cross-check two conflicting KB entries",
                     "Goal-ledger SSOT drift detector",
                     "Anomaly baseline library threshold re-fit",
                     "Fleet convergence-rate measurement",
                     "Dictionary LOD cursor staleness check",
                     "Research-brief to draft pipeline timing"],
    "builder":      ["Frontend pin-file forensics + clobber-loop guard",
                     "Model-swap automation canary phase",
                     "Event-bus smoke test on live seat",
                     "Knowledge-stream end-to-end latency probe",
                     "Swap-guard idempotency negative injection",
                     "UI asset binary-size pre-pin gate",
                     "CDP live screenshot leg on non-sandbox seat",
                     "Delta-strip localStorage delta correctness",
                     "Token-enforcement contrast audit",
                     "Build-script exit-code discipline pass"],
    "archivist":    ["Autonomy-progression model R^2 fit >=3 cycles",
                     "Anomaly baseline library 5-type thresholds",
                     "Onboarding pack auto-generation byte budget",
                     "Decay report pointer-map health sweep",
                     "Provenance report for new KB leaves",
                     "Index-check dangling/orphan/stale scan",
                     "Knowledge-base size guard threshold",
                     "Archive rotation retention policy",
                     "Cross-lane citation graph build",
                     "Stale-claim closure verification"],
    "scribe":       ["Runbook coverage audit vs incident log",
                     "Completion-analysis compression ratio check",
                     "Cycle narrative auto-digest length gate",
                     "Pattern library dedupe + merge",
                     "Daily snapshot field completeness",
                     "Stakeholder brief voice lint",
                     "Mode narrative drift detector",
                     "Fleet history compression fidelity",
                     "Human operating manual residual-role spec",
                     "Goal-set synthesizer lane coverage"],
    "verifier":     ["Auto-trigger regression battery on commit hook",
                     "Chaos-recovery verification drill <120s",
                     "Cross-lane contract test golden fixtures",
                     "Acceptance-test auto-generation stub validity",
                     "Verification coverage map pct computation",
                     "Dispatch fuzzer negative injection",
                     "Steady-state transition invariant check",
                     "Cycle quality scoring boundary table",
                     "Time-to-convergence regression alert",
                     "Goal-lifecycle audit orphan detection"],
    "designer":     ["Regression alert banner <2s + cooldown",
                     "Cross-lane assist graph SVG edge scaling",
                     "Fleet health composite gauge weight sum=1",
                     "Goal pipeline flow bottleneck badge",
                     "Convergence velocity sparkline slope arrow",
                     "Mind-room floor plan legibility audit",
                     "High-contrast token enforcement pass",
                     "Outreach pack visual spec render",
                     "Panel overflow check at 375/768",
                     "Reduced-motion safe animation gate"],
    "mechanic":     ["Autonomous OOM recovery loop <60s MTTR",
                     "Fleet health heartbeat single JSON <2KB",
                     "Cycle timeout auto-diagnostic capture",
                     "Elevated command audit trail + weekly summary",
                     "Mirror sync drift monitor >10min alert",
                     "Model lifecycle load-balance replay",
                     "Host idle investigation probe",
                     "Fleet capacity forecast calibration",
                     "Transition gap SLA measurement",
                     "Recovery runbook coverage audit"],
    "outlet":       ["First live account connection end-to-end ship",
                     "Milestone auto-detect threshold draft",
                     "Trend-to-draft pipeline voice lint <5min",
                     "Hard verification gate queue_check block",
                     "Per-platform voice variant lint constraints",
                     "Platform connection runbook",
                     "Outreach offer draft staging",
                     "Timeline event->draft->ship <4h log",
                     "Voice consistency score >85% check",
                     "Milestone trigger 3-cycle false-positive scan"],
    "pixel":        ["Close live CDP screenshot leg goal #5",
                     "Debug-artifact purge + asset size gate",
                     "Since-last-cycle delta strip sr-only announce",
                     "Token-enforcement high-contrast audit",
                     "Widget legibility check 4-visible rule",
                     "Horizontal overflow regression at 375px",
                     "localStorage delta auto-clear on fetch",
                     "Live-region change announcement",
                     "Binary asset pre-pin reject gate",
                     "UI change log byte-budget guard"],
    "forge":        ["Full convergence-loop E2E drill capstone",
                     "Forecast-calibration backtest harness",
                     "Convergence-plateau detection gate",
                     "Dispatch-correctness deploy gate",
                     "Idle-productivity floor enforcer",
                     "Regression sentinel precision test",
                     "Chair idempotency guard",
                     "Seat-sizing decision audit replay",
                     "Canary perf-gate threshold",
                     "Gate health scheduled-task monitor"],
}


# --------------------------------------------------------------------------- #
# Audit log: the human-touch detector                                          #
# --------------------------------------------------------------------------- #
class AuditLog:
    def __init__(self):
        self.entries = []          # ordered list of {stage, action, kind, detail}
        self.first_human_step = None

    def record(self, stage, action, kind, detail=""):
        e = {"stage": stage, "action": action, "kind": kind, "detail": detail}
        self.entries.append(e)
        if kind in HUMAN_KINDS and self.first_human_step is None:
            self.first_human_step = {"stage": stage, "action": action,
                                     "kind": kind, "detail": detail}

    @property
    def human_touch_count(self):
        return sum(1 for e in self.entries if e["kind"] in HUMAN_KINDS)

    @property
    def autonomous_count(self):
        return sum(1 for e in self.entries if e["kind"] in AUTONOMOUS_KINDS)


def run_subprocess(cmd, sandbox, audit, stage, label, timeout=60):
    """Run a lifecycle subprocess. Classify the result for the human-touch audit.
    A non-zero exit is a HUMAN TOUCH: an autonomous step that failed is one that
    would need a human to proceed - exactly what the capstone must name."""
    try:
        r = subprocess.run(cmd, cwd=str(sandbox), capture_output=True,
                           text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        audit.record(stage, label, "subprocess_needs_human", f"TIMEOUT after {timeout}s")
        return 124, "", f"timeout"
    if r.returncode == 0:
        audit.record(stage, label, "subprocess_local_ok",
                     (r.stdout or "").strip().splitlines()[-1] if r.stdout else "ok")
    else:
        tail = (r.stderr or r.stdout or "").strip().splitlines()[-2:]
        audit.record(stage, label, "subprocess_needs_human",
                     f"exit {r.returncode}: {' | '.join(tail)}")
    return r.returncode, r.stdout or "", r.stderr or ""


# --------------------------------------------------------------------------- #
# Sandbox build                                                                #
# --------------------------------------------------------------------------- #
def _goal_line(text, reached):
    marker = f" (verified: {DRILL_DATE} - drill seed)" if reached else ""
    return f"**{text}** - acceptance criterion green{marker}"


def setup_sandbox():
    root = Path(tempfile.mkdtemp(prefix="forge_e2e_"))
    for sub in ("memory/goals/archive", "memory/orchestrator", "memory/researcher",
                "memory/goals", "memory/fleet/roster-snapshots"):
        (root / sub).mkdir(parents=True, exist_ok=True)

    # Copy the REAL lifecycle code so the drill drives genuine paths.
    for src in (TRANSITION_SRC, FORECAST_SRC, LEDGER_SRC):
        if not src.exists():
            shutil.rmtree(root, ignore_errors=True)
            raise FileNotFoundError(f"required lifecycle source missing: {src}")
    shutil.copy2(TRANSITION_SRC, root / "memory/orchestrator/auto_cycle_transition.py")
    shutil.copy2(FORECAST_SRC,   root / "memory/goals/forecast_engine.py")
    shutil.copy2(LEDGER_SRC,     root / "memory/researcher/goal_ledger.py")

    # Stub cycle_retro.py (enrichment only; transition tolerates its absence) so the
    # close+chair subprocess is deterministic and never blocks on a missing retro.
    (root / "memory/orchestrator/cycle_retro.py").write_text(
        "#!/usr/bin/env python3\nimport sys, os\n"
        "out = sys.argv[sys.argv.index('--out')+1] if '--out' in sys.argv else None\n"
        "if out: open(out,'w').write('# Retro (drill stub)\n')\n"
        "print('retro done')\nsys.exit(0)\n", encoding="utf-8")

    # SEED: a CLOSED cycle N - every agent at 10/10 reached.
    for agent in AGENTS:
        lines = [f"# {agent.capitalize()} - {GOALS_PER_AGENT} goals (set {DRILL_DATE}, cycle-{CYCLE_N})",
                 "", f"Focus: Fleet Autonomy Convergence (drill seed)", "", ""]
        for i, gt in enumerate(DRAFT_GOALS[agent], 1):
            lines.append(f"{i}. {_goal_line(gt, reached=True)}")
        (root / "memory/goals" / f"{agent}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # TODO.md with the cycle marker the transition reads.
    (root / "TODO.md").write_text(
        f"# TODO\n\n## LIVE PLAN - cycle-{CYCLE_N}\nStatus: all goals closed, ready to chair.\n",
        encoding="utf-8")

    # agents.json minimal roster (snapshot step reads it).
    (root / "agents.json").write_text(
        json.dumps({"agents": [{"id": a} for a in AGENTS]}), encoding="utf-8")

    return root


# --------------------------------------------------------------------------- #
# Stage helpers                                                                #
# --------------------------------------------------------------------------- #
def count_goals(path):
    if not path.exists():
        return 0, 0
    total = reached = 0
    for ln in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*(\d+)[.)]\s+(.*)", ln)
        if m and len(m.group(2).strip()) >= 12:
            total += 1
            if "(verified:" in ln or "[REACHED" in ln or "— recorded" in ln:
                reached += 1
    return total, reached


def stage_close_chair(sandbox, audit):
    """Drive REAL auto_cycle_transition.py --run. Returns (ok, evidence)."""
    stage = "CLOSE+CHAIR"
    cmd = [sys.executable, "memory/orchestrator/auto_cycle_transition.py", "--run"]
    rc, out, err = run_subprocess(cmd, sandbox, audit, stage,
                                  "auto_cycle_transition.py --run")
    gdir = sandbox / "memory/goals"
    adir = gdir / "archive"
    archived = [f for f in os.listdir(adir) if f.endswith(".md")] if adir.exists() else []
    skeletons = [a + ".md" for a in AGENTS if (gdir / (a + ".md")).exists()]
    kickoff = [f for f in os.listdir(gdir)
               if f.startswith(f"cycle{CYCLE_N+1}-kickoff-")] if gdir.exists() else []
    ev = {"exit": rc, "archived_files": len(archived), "skeletons_created": len(skeletons),
          "kickoff_files": kickoff}
    ok = (rc == 0 and len(archived) == len(AGENTS)
          and len(skeletons) == len(AGENTS) and len(kickoff) >= 1)
    return ok, ev


def stage_draft_dispatch(sandbox, audit):
    """Fill the freshly-chaired skeletons with real drafted goals (autonomous draft),
    then drive REAL forecast_engine.py to produce the dispatch plan (next10.json).
    Assert conformance: no open goal is dropped from any lane."""
    stage = "DRAFT+DISPATCH"
    gdir = sandbox / "memory/goals"

    # DRAFT: replace TBD skeletons with concrete drafted goals (orchestrator drafting, autonomous).
    for agent in AGENTS:
        lines = [f"# {agent.capitalize()} - {GOALS_PER_AGENT} goals (set {DRILL_DATE}, cycle-{CYCLE_N+1})",
                 "", f"Focus: Fleet Autonomy Convergence (drafted)", "", ""]
        for i, gt in enumerate(DRAFT_GOALS[agent], 1):
            lines.append(f"{i}. {_goal_line(gt, reached=False)}")
        (gdir / f"{agent}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        audit.record(stage, f"draft {agent}.md ({GOALS_PER_AGENT} goals)", "file_write")

    # DISPATCH: real forecast engine.
    cmd = [sys.executable, "memory/goals/forecast_engine.py", "--refresh"]
    rc, out, err = run_subprocess(cmd, sandbox, audit, stage,
                                  "forecast_engine.py --refresh")
    next10_path = gdir / "next10.json"
    ev = {"exit": rc}
    if not (rc == 0 and next10_path.exists()):
        return False, ev
    doc = json.loads(next10_path.read_text(encoding="utf-8"))
    lanes = doc.get("lanes", {})
    dispatched_open = sum(v.get("total", 0) - v.get("done", 0) for v in lanes.values())
    expected_open = len(AGENTS) * GOALS_PER_AGENT
    # Conformance: every drafted open goal appears in exactly one lane (none lost/duped).
    conformance_ok = (dispatched_open == expected_open and doc.get("fleet", {}).get("total") == expected_open)
    n_items = len(doc.get("next10", []))
    items_well_formed = all(all(k in it for k in ("agent", "eta", "rank", "steps",
                                                   "title", "type")) for it in doc.get("next10", []))
    ev.update({"next10_items": n_items, "dispatched_open": dispatched_open,
               "expected_open": expected_open, "conformance_100pct": conformance_ok,
               "items_well_formed": items_well_formed,
               "fleet_pct": doc.get("fleet", {}).get("pct")})
    ok = conformance_ok and items_well_formed and n_items >= 1
    return ok, ev


def stage_reach_100(sandbox, audit):
    """Simulate the auto-loop sweeping every new-cycle goal to reached (the agents'
    LLM work - inherently simulated). Then RE-CLOSE via the REAL all-closed gate."""
    stage = "REACH 100% + RE-CLOSE"
    gdir = sandbox / "memory/goals"
    # Sweep: append a verified marker to each open goal line across all lanes.
    for agent in AGENTS:
        p = gdir / f"{agent}.md"
        txt = p.read_text(encoding="utf-8").splitlines()
        new = []
        for ln in txt:
            m = re.match(r"^(\s*\d+[.)]\s+)(.*)$", ln)
            if m and "(verified:" not in ln and len(m.group(2).strip()) >= 12:
                body = m.group(2)
                if not body.endswith(")"):
                    ln = f"{m.group(1)}{body} (verified: {DRILL_DATE} - drill auto-loop sweep)"
            new.append(ln)
        p.write_text("\n".join(new) + "\n", encoding="utf-8")
    audit.record(stage, f"auto-loop sweep -> all {len(AGENTS)} lanes reached", "simulated_loop")

    # RE-CLOSE: real transition --dry-run (truly read-only) must report ALL CLOSED,
    # proving the next close can fire autonomously. NOTE: we deliberately use --dry-run
    # and NOT --check: the transition's --check mode is documented "report status only"
    # but falls through with dry=False and actually EXECUTES (archives + recreates
    # skeletons) - a real bug surfaced by this drill, handed to Orchestrator.
    cmd = [sys.executable, "memory/orchestrator/auto_cycle_transition.py", "--dry-run"]
    rc, out, err = run_subprocess(cmd, sandbox, audit, stage,
                                  "auto_cycle_transition.py --dry-run")
    all_closed = (rc == 0 and "ALL CLOSED" in out)
    reached_total = sum(count_goals(gdir / f"{a}.md")[1] for a in AGENTS)
    ev = {"reached_total": reached_total, "expected_total": len(AGENTS) * GOALS_PER_AGENT,
          "all_closed_gate_fires": all_closed}
    ok = (reached_total == len(AGENTS) * GOALS_PER_AGENT) and all_closed
    return ok, ev


def inject_human_touch(sandbox, audit):
    """SELFTEST ONLY: simulate a step that genuinely requires a human (an elevation /
    admin command), to prove the detector is not vacuously reporting zero."""
    stage = "SELFTEST-INJECTION"
    # A stand-in for `python elev.py <admin cmd>`: external admin by definition.
    audit.record(stage, "elev.py admin (simulated elevation)", "external_admin",
                 "injected to prove detector fires")
    return True


def inject_failing_transition(sandbox):
    """SELFTEST-FAIL ONLY: overwrite the sandbox's transition script so the close+chair
    subprocess exits non-zero. Proves a FAILED autonomous step is caught + named as the
    human-touch (the 'exact step that needed a human' branch, not just admin injection)."""
    p = sandbox / "memory/orchestrator/auto_cycle_transition.py"
    p.write_text("#!/usr/bin/env python3\nimport sys\n"
                 "print('simulated transition failure: disk full (injected)')\n"
                 "sys.exit(1)\n", encoding="utf-8")
    return True


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def run_drill(selftest=False, selftest_fail=False):
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    audit = AuditLog()
    sandbox = None
    stages = {}
    setup_error = None
    try:
        sandbox = setup_sandbox()
        audit.record("SEED", f"sandbox with {len(AGENTS)} agents @ 10/10 reached (cycle-{CYCLE_N})",
                     "file_write")
        if selftest_fail:
            inject_failing_transition(sandbox)
    except Exception as e:  # noqa: BLE001 - report setup failure, exit 2
        setup_error = str(e)

    if sandbox is None:
        return {"ts": ts, "result": "SETUP_ERROR", "setup_error": setup_error,
                "selftest": selftest, "stages": {},
                "human_touch_count": audit.human_touch_count,
                "first_human_step": audit.first_human_step}

    try:
        ok1, ev1 = stage_close_chair(sandbox, audit);  stages["close_chair"] = {"ok": ok1, **ev1}
        ok2, ev2 = stage_draft_dispatch(sandbox, audit); stages["draft_dispatch"] = {"ok": ok2, **ev2}
        ok3, ev3 = stage_reach_100(sandbox, audit);      stages["reach_reclose"] = {"ok": ok3, **ev3}
    finally:
        pass  # cleanup below (after selftest injection which reuses sandbox)

    if selftest:
        inject_human_touch(sandbox, audit)   # must make the detector fire
        stages["selftest_injection"] = {"ok": True,
                                        "detector_fired": audit.first_human_step is not None}

    finally_cleanup = None
    shutil.rmtree(sandbox, ignore_errors=True)

    loop_closed = all(stages[s]["ok"] for s in ("close_chair", "draft_dispatch", "reach_reclose"))
    ht = audit.human_touch_count

    if selftest_fail:
        # Fail-injection PASSES when close+chair FAILS, the loop does NOT close,
        # and the detector names that exact step as subprocess_needs_human.
        fh = rec_fh = audit.first_human_step
        detected = (fh is not None and fh["kind"] == "subprocess_needs_human"
                    and fh["stage"] == "CLOSE+CHAIR")
        result = "PASS" if (not loop_closed and detected) else "FAIL"
        stages["selftest_fail_injection"] = {"ok": True, "detector_named_failing_step": detected,
                                             "first_human_kind": (fh["kind"] if fh else None)}
    elif selftest:
        # Selftest PASSES when the detector correctly catches the injected touch AND
        # the real loop stages still closed cleanly.
        result = "PASS" if (stages["selftest_injection"]["detector_fired"] and loop_closed) else "FAIL"
    else:
        # Real drill PASSES only when the whole loop closed AND zero human touches.
        result = "PASS" if (loop_closed and ht == 0) else "FAIL"

    rec = {
        "ts": ts,
        "result": result,
        "selftest": selftest,
        "selftest_fail": selftest_fail,
        "cycle_closed": CYCLE_N, "cycle_chaired": CYCLE_N + 1,
        "loop_closed_end_to_end": loop_closed,
        "human_touch_count": ht,
        "autonomous_steps": audit.autonomous_count,
        "total_audited_steps": len(audit.entries),
        "first_human_step": audit.first_human_step,
        "stages": stages,
    }

    # Append to the drill ledger (append-only evidence).
    with open(DRILL_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    LAST_JSON.write_text(json.dumps(rec, indent=2), encoding="utf-8")

    # Human-readable report.
    _write_report(rec)
    return rec


def _write_report(rec):
    L = ["# Convergence-Loop E2E Drill — Report", "",
         f"Generated: {rec['ts']}",
         f"Result: **{rec['result']}**  (selftest={rec['selftest']})",
         f"Loop closed end-to-end: **{rec['loop_closed_end_to_end']}**",
         f"Human touches: **{rec['human_touch_count']}** of {rec['total_audited_steps']} audited steps "
         f"({rec['autonomous_steps']} autonomous)", ""]
    if rec["first_human_step"]:
        fh = rec["first_human_step"]
        L += [f"FIRST STEP THAT NEEDED A HUMAN: **{fh['stage']} / {fh['action']}** "
              f"({fh['kind']}) — {fh.get('detail','')}", ""]
    else:
        L += ["First step that needed a human: **none** (zero-touch loop).", ""]
    L += ["## Stages", ""]
    for name, ev in rec["stages"].items():
        ok = ev.get("ok", False) if isinstance(ev, dict) else False
        body = {k: v for k, v in ev.items() if k != "ok"} if isinstance(ev, dict) else {}
        L.append(f"- **{name}**: {'PASS' if ok else 'FAIL'} — {json.dumps(body)}")
    L += ["---", "*Generated by convergence_e2e_drill.py (Forge goal #10 capstone)*"]
    REPORT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    selftest = "--selftest" in sys.argv
    selftest_fail = "--selftest-fail" in sys.argv
    mode = "SELFTEST-FAIL" if selftest_fail else ("SELFTEST" if selftest else "DRILL")
    print(f"=== Forge Goal #10: Full Convergence-Loop E2E Drill ({mode}) ===\n")
    rec = run_drill(selftest=selftest, selftest_fail=selftest_fail)

    print(f"Cycle closed:  {rec.get('cycle_closed')} -> chaired {rec.get('cycle_chaired')}")
    for name, ev in rec.get("stages", {}).items():
        ok = ev.get("ok", False) if isinstance(ev, dict) else False
        body = {k: v for k, v in ev.items() if k != "ok"} if isinstance(ev, dict) else {}
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {json.dumps(body)}")
    print(f"\nLoop closed end-to-end: {rec['loop_closed_end_to_end']}")
    print(f"Human touches:          {rec['human_touch_count']} "
          f"({rec['autonomous_steps']} autonomous / {rec['total_audited_steps']} total)")
    if rec["first_human_step"]:
        fh = rec["first_human_step"]
        print(f"First human step:       {fh['stage']} / {fh['action']} ({fh['kind']})")
    else:
        print("First human step:       NONE (zero-touch)")
    print(f"\nRESULT: {rec['result']}")
    print(f"Evidence: {DRILL_JSONL.name} (appended), {LAST_JSON.name}, {REPORT_MD.name}")

    if rec["result"] == "PASS":
        sys.exit(0)
    if rec["result"] == "SETUP_ERROR":
        sys.exit(2)
    sys.exit(1)


if __name__ == "__main__":
    main()
