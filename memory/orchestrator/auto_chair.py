#!/usr/bin/env python3
"""
Autonomous Round-Chair Protocol (Orchestrator, Cycle 19 goal #5).

Chairs a cycle transition END-TO-END without a human:
  detect trigger (fleet 100% OR convergence_state == PLATEAU)
    -> archive the previous round's lane goal files
    -> draft candidate goals for each lane (skeleton generator, anti-repeat vs existing titles)
    -> write memory/goals/<name>.md for each lane
    -> emit exactly ONE ratification request
A second run over the same closed cycle is idempotent: no double-archive, no duplicate goals.

SAFETY: real mode is DRY-RUN by default. It only writes files when --execute is passed
AND the trigger is true. --selftest runs entirely in a temp dir and never touches real data.

CLI:
  python memory/orchestrator/auto_chair.py --selftest          # hermetic synthetic drill (temp dir)
  python memory/orchestrator/auto_chair.py --dry-run           # report what chairing WOULD do
  python memory/orchestrator/auto_chair.py --execute           # actually archive+draft+write (trigger-gated)
"""
import argparse
import json
import os
import pathlib
import re
import shutil
import tempfile
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[2]
GOALS_DIR = ROOT / "memory" / "goals"
ARCHIVE_DIR = ROOT / "memory" / "goals" / "archive"
RATIFY_OUT = ROOT / "memory" / "ops" / "ratification-request.jsonl"

LANES = ["orchestrator", "researcher", "verifier", "scribe", "designer",
         "archivist", "mechanic", "outlet"]

# per-lane capability seed: (title, one-line body) used to draft skeleton goals.
# Kept small + generic so drafts are non-anti-repeat against existing titles.
GOAL_SEED = {
    "orchestrator": [("Dispatch Quality Regression Watch",
                     "regression-watch dispatch conformance each cycle; alert on any drop below prior baseline")],
    "researcher": [("Source Confidence Decay Tracker",
                    "track how quickly research citations go stale; flag KB entries needing re-verification")],
    "verifier": [("Evidence Freshness Sweep",
                  "sweep ledger evidence for staleness; auto-flag verified lines older than the cycle window")],
    "scribe": [("Decision-Delta Digest",
                "compress each cycle's decisions into a one-page delta vs the prior cycle")],
    "designer": [("Cockpit Readability Pass",
                  "audit cockpit panels for cognitive load; propose one layout simplification")],
    "archivist": [("Pointer-Map Health Digest",
                    "run pointer-map health check; report dangling/orphan/stale pointers in one leaf")],
    "mechanic": [("SLA Trend Watch",
                  "trend recovery SLA + cycle duration; alert when any metric degrades 2 cycles running")],
    "outlet": [("Voice-Consistency Lint",
                 "lint drafted posts for voice drift vs the platform voice guide; report deviations")],
}


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def detect_trigger(fleet_pct=None, convergence_state=None):
    """Return (bool, reason). Trigger when fleet is 100% OR convergence has PLATEAUed."""
    if fleet_pct is not None and float(fleet_pct) >= 100.0:
        return True, f"fleet at {fleet_pct}% (100% threshold met)"
    if convergence_state is not None and str(convergence_state).upper() == "PLATEAU":
        return True, "convergence_state == PLATEAU"
    return False, "not triggered: fleet < 100% and convergence not PLATEAU"


def _norm_title(t):
    t = re.sub(r"\*+", "", t)              # strip markdown emphasis
    t = re.sub(r"`+", "", t)               # strip code ticks
    t = re.sub(r"[^a-z0-9 ]", "", t.lower())
    return re.sub(r"\s+", " ", t).strip()


def existing_titles(goals_dir, lane):
    p = pathlib.Path(goals_dir) / f"{lane}.md"
    titles = set()
    if not p.exists():
        return titles
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"\s*\d+\.\s+\*\*(.+?)\*\*", line)
        if m:
            titles.add(_norm_title(m.group(1)))
    return titles


def draft_goals(lane, goals_dir):
    """Return list of (title, body) skeleton goals for a lane, skipping anti-repeat titles."""
    have = existing_titles(goals_dir, lane)
    out = []
    for title, body in GOAL_SEED.get(lane, []):
        if _norm_title(title) in have:
            continue  # anti-repeat: already present
        out.append((title, body))
    return out


def archive_lane_file(goals_dir, lane, ts):
    """Move <lane>.md to archive/<lane>-<ts>.md if it exists. Returns archived path or None."""
    src = pathlib.Path(goals_dir) / f"{lane}.md"
    if not src.exists():
        return None
    adir = pathlib.Path(goals_dir) / "archive"
    adir.mkdir(parents=True, exist_ok=True)
    dst = adir / f"{lane}-{ts}.md"
    # idempotency: if an archive for this ts already exists, do not double-archive
    if dst.exists():
        return str(dst.relative_to(pathlib.Path(goals_dir).parent))
    shutil.move(str(src), str(dst))
    return str(dst.relative_to(pathlib.Path(goals_dir).parent))


def write_lane_file(goals_dir, lane, round_label):
    """Write a fresh <lane>.md with the drafted skeleton goals. Returns (written, goal_count)."""
    drafts = draft_goals(lane, goals_dir)
    lines = [f"# {lane.capitalize()} — {round_label} (drafted by auto_chair, awaiting ratification)", ""]
    for i, (title, body) in enumerate(drafts, 1):
        lines.append(f"{i}. **{title}** - {body}")
    if not drafts:
        lines.append("_(no new non-anti-repeat goals drafted; lane carries over)_")
    p = pathlib.Path(goals_dir) / f"{lane}.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(p.relative_to(pathlib.Path(goals_dir).parent)), len(drafts)


def emit_ratification(request, out=RATIFY_OUT):
    """Append exactly one ratification request record. Returns the record."""
    rec = {"ts": _now(), "type": "cycle_ratification", **request}
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def chair_cycle(goals_dir, lanes=LANES, round_label=None, execute=False, trigger=True, ratify_out=RATIFY_OUT):
    """
    Core chairing routine. Returns a summary dict.
    - archives each lane's previous goals file (if any)
    - writes a fresh draft goals file per lane
    - emits exactly one ratification request
    Idempotent: re-running with the same ts/label does not double-archive or duplicate goals.
    """
    if round_label is None:
        round_label = f"auto-cycle-{_today()}"
    ts = _today()
    summary = {"round_label": round_label, "execute": execute, "triggered": trigger,
               "archived": [], "written": [], "total_goals_drafted": 0}
    if not trigger:
        summary["note"] = "trigger false; no action taken"
        return summary

    for lane in lanes:
        if execute:
            arch = archive_lane_file(goals_dir, lane, ts)
            if arch:
                summary["archived"].append(arch)
            path, n = write_lane_file(goals_dir, lane, round_label)
            summary["written"].append({"file": path, "goals": n})
            summary["total_goals_drafted"] += n
        else:
            # dry-run: report what would be archived + drafted without touching files
            src = pathlib.Path(goals_dir) / f"{lane}.md"
            drafts = draft_goals(lane, goals_dir)
            summary.setdefault("dryrun", []).append({
                "lane": lane,
                "would_archive": str(src.relative_to(pathlib.Path(goals_dir).parent)) if src.exists() else None,
                "would_draft": [t for t, _ in drafts],
            })

    # exactly ONE ratification request per chairing act (only when executing)
    if execute:
        summary["ratification"] = emit_ratification({
            "round_label": round_label,
            "lanes": lanes,
            "files": [w["file"] for w in summary["written"]],
            "total_goals": summary["total_goals_drafted"],
        }, out=ratify_out)
    else:
        summary["ratification"] = None
    return summary


def selftest():
    ok = 0
    total = 4
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="auto_chair_selftest_"))
    try:
        goals_dir = tmp / "goals"
        goals_dir.mkdir(parents=True)
        ratify_out = tmp / "ratification.jsonl"

        # seed a "closed cycle": give two lanes existing goal files with titles that
        # overlap the seed (to exercise anti-repeat) and one lane without.
        (goals_dir / "researcher.md").write_text(
            "# Researcher\n1. **Source Confidence Decay Tracker** - old\n2. **Old Investigation** - x\n",
            encoding="utf-8")
        (goals_dir / "mechanic.md").write_text(
            "# Mechanic\n1. **SLA Trend Watch** - old\n", encoding="utf-8")

        # --- T1: chair archives + writes lane files + drafts non-anti-repeat goals
        s = chair_cycle(goals_dir, lanes=["researcher", "mechanic", "scribe"],
                        round_label="selftest-cycle", execute=True,
                        trigger=True, ratify_out=ratify_out)
        # archived the two existing files
        arch_names = [pathlib.Path(a).name[:-3].split("-")[0] for a in s["archived"]]
        assert set(arch_names) == {"researcher", "mechanic"}, f"T1 archive wrong: {s['archived']}"
        # fresh lane files written for all three
        for lane in ["researcher", "mechanic", "scribe"]:
            assert (goals_dir / f"{lane}.md").exists(), f"T1 missing {lane}.md"
        # anti-repeat: researcher's existing 'Source Confidence Decay Tracker' must NOT be re-drafted
        rtxt = (goals_dir / "researcher.md").read_text(encoding="utf-8")
        assert rtxt.count("**Source Confidence Decay Tracker**") == 1, "T1 anti-repeat violated (dup title)"
        ok += 1

        # --- T2: exactly ONE ratification request emitted
        recs = [l for l in ratify_out.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(recs) == 1, f"T2 expected 1 ratification, got {len(recs)}"
        ok += 1

        # --- T3: idempotency — state stabilizes; once all lanes archived for this ts,
        # further runs add no new archives and append no duplicate goals.
        s2 = chair_cycle(goals_dir, lanes=["researcher", "mechanic", "scribe"],
                         round_label="selftest-cycle", execute=True, trigger=True,
                         ratify_out=ratify_out)
        n_arch_after_run2 = len(list((goals_dir / "archive").glob("*.md")))
        assert n_arch_after_run2 <= 3, f"T3 too many archives: {n_arch_after_run2}"
        # a THIRD run must change nothing (every lane's (lane,ts) dst already exists)
        s3 = chair_cycle(goals_dir, lanes=["researcher", "mechanic", "scribe"],
                         round_label="selftest-cycle", execute=True, trigger=True,
                         ratify_out=ratify_out)
        n_arch_after_run3 = len(list((goals_dir / "archive").glob("*.md")))
        assert n_arch_after_run3 == n_arch_after_run2, f"T3 not stable: {n_arch_after_run2}->{n_arch_after_run3}"
        # no duplicate goal titles appended by re-runs
        after_r = (goals_dir / "researcher.md").read_text(encoding="utf-8")
        assert after_r.count("**Source Confidence Decay Tracker**") == 1, "T3 dup goal on re-run"
        ok += 1

        # --- T4: trigger gating — no action when trigger false
        tmp2 = pathlib.Path(tempfile.mkdtemp(prefix="auto_chair_trig_"))
        gd2 = tmp2 / "goals"; gd2.mkdir(parents=True)
        (gd2 / "scribe.md").write_text("# Scribe\n1. **Decision-Delta Digest** - old\n", encoding="utf-8")
        s3 = chair_cycle(gd2, lanes=["scribe"], round_label="x", execute=True, trigger=False)
        assert s3["written"] == [] and not (gd2 / "archive").exists(), f"T4 acted despite no trigger: {s3}"
        ok += 1

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"auto_chair selftest: {ok}/{total} PASS")
    return ok == total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--execute", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        ok = selftest()
        raise SystemExit(0 if ok else 1)

    # read live trigger inputs (best-effort; missing -> not triggered)
    fleet_pct, conv_state = None, None
    try:
        led = json.loads((ROOT / "goal_ledger.json").read_text(encoding="utf-8", errors="replace"))
        fleet_pct = led.get("fleet_pct_reached")
    except Exception:
        pass
    try:
        fm = json.loads((ROOT / "memory" / "ops" / "fleet-mode.json").read_text(encoding="utf-8", errors="replace"))
        conv_state = fm.get("convergence_state")
    except Exception:
        pass
    trigger, reason = detect_trigger(fleet_pct, conv_state)

    execute = a.execute  # dry-run is the default when neither flag given
    summary = chair_cycle(GOALS_DIR, lanes=LANES, round_label=None, execute=execute, trigger=trigger)
    summary["trigger_reason"] = reason
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
