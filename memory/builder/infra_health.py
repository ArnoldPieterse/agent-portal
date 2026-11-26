#!/usr/bin/env python3
"""
Builder Goal #4 — Autonomy-Infra Self-Health Probe.
Liveness probe over Builder's own autonomy scripts. Emits one JSONL record per
script to memory/builder/infra-health.jsonl with {ok, exists, compiles,
last_run, age_hours, latency_ms, error, flag} plus a trailing summary line the
watchdog (Pixel widget / Forge gate) reads.

Liveness model:
  ok   = exists AND compiles AND has a fresh last-run marker.
  A script's "last run" is the mtime of its real output artifact (honest liveness:
did this automation produce output recently?). For controlled/selftest runs pass
--stamps-dir DIR, where each <name>.json holds {"ts": epoch}; the probe then reads
markers from there instead of live artifacts. This lets a test clear one marker and
watch that exact script get flagged within one run.

Watchdog thresholds (cycles ~ hours): a script is 'stale' when its last_run is older
than --max-age-hours (default 48h ~= a couple of cycles), 'missing' when the marker
cannot be found, or 'compile-error' when the source no longer parses.

Usage:
  python memory/builder/infra_health.py                 # live probe -> append JSONL
  python memory/builder/infra_health.py --selftest      # controlled scenario, asserts criteria
  python memory/builder/infra_health.py --max-age-hours 24 --stamps-dir DIR
"""
import argparse, json, os, py_compile, sys, tempfile, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # repo root (…/AgentPortal)
BUILDER = ROOT / "memory" / "builder"
OPS = ROOT / "memory" / "ops"
OUT_JSONL = BUILDER / "infra-health.jsonl"

# registry: script -> its real output artifact used as the last-run marker.
SCRIPTS = {
    "fleet_mode_writer":  {"src": BUILDER / "fleet_mode_writer.py",   "marker": OPS / "fleet-mode.json"},
    "convergence_fsm":    {"src": BUILDER / "convergence_fsm.py",     "marker": OPS / "fsm-events.jsonl"},
    "dispatch_filter":    {"src": BUILDER / "dispatch_filter.py",     "marker": OPS / "dispatch-cache.json"},
    "status_propagator":  {"src": BUILDER / "status_propagator.py",   "marker": OPS / "mode-freshness.json"},
    "cycle_closeout":     {"src": BUILDER / "cycle_closeout.py",      "marker": OPS / "cycle-closeout.jsonl"},
}

REQUIRED_KEYS = ["ts", "script", "ok", "exists", "compiles",
                 "last_run", "age_hours", "latency_ms", "error", "flag"]


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _epoch(p: Path):
    try:
        return p.stat().st_mtime
    except OSError:
        return None


def compile_ok(src: Path):
    """Parse-check without leaving a .pyc next to the source."""
    if not src.exists():
        return False, "missing-source"
    with tempfile.TemporaryDirectory() as td:
        try:
            py_compile.compile(str(src), cfile=os.path.join(td, "x.pyc"), doraise=True)
            return True, None
        except Exception as e:  # noqa: BLE001
            return False, f"compile-error:{e.__class__.__name__}"


def resolve_marker(name: str, stamps_dir):
    """Return (epoch_seconds, source_label) for a script's last run."""
    if stamps_dir is not None:
        sp = Path(stamps_dir) / f"{name}.json"
        if sp.exists():
            try:
                return float(json.loads(sp.read_text(encoding="utf-8"))["ts"]), "stamps"
            except Exception:  # noqa: BLE001
                return None, "stamps-bad"
        return None, "stamps-none"
    m = SCRIPTS[name]["marker"]
    e = _epoch(m)
    return (e, "artifact") if e is not None else (None, "artifact-none")


def probe(max_age_hours=48.0, stamps_dir=None):
    now = time.time()
    records = []
    for name, spec in SCRIPTS.items():
        t0 = time.perf_counter()
        exists = spec["src"].exists()
        compiles, cerr = compile_ok(spec["src"])
        epoch, src_label = resolve_marker(name, stamps_dir)
        age_hours = None
        error = None
        flag = None
        if not exists:
            error = "missing-source"
            flag = "missing"
        elif not compiles:
            error = cerr
            flag = "compile-error"
        elif epoch is None:
            error = f"no-last-run:{src_label}"
            flag = "missing"
        else:
            age_hours = round((now - epoch) / 3600.0, 3)
            if age_hours > max_age_hours:
                error = f"stale:{age_hours}h>{max_age_hours}h"
                flag = "stale"
        ok = exists and compiles and (flag is None)
        last_run = datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat(timespec="seconds") if epoch else None
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        rec = {
            "ts": _now(), "script": name, "ok": ok,
            "exists": exists, "compiles": compiles,
            "last_run": last_run, "age_hours": age_hours,
            "latency_ms": latency_ms, "error": error, "flag": flag,
            "marker_source": src_label,
        }
        records.append(rec)
    flagged = [r["script"] for r in records if not r["ok"]]
    summary = {"type": "summary", "ts": _now(), "all_healthy": not flagged,
               "flagged": flagged, "max_age_hours": max_age_hours}
    return records + [summary]


def emit(records):
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with OUT_JSONL.open("a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def _selftest():
    import shutil
    tmp = Path(tempfile.mkdtemp(prefix="infra_selftest_"))
    failures = []
    try:
        # (a) clean state: fresh stamps for all -> all healthy, schema stable.
        now = time.time()
        for name in SCRIPTS:
            (tmp / f"{name}.json").write_text(json.dumps({"ts": now}), encoding="utf-8")
        recs = probe(max_age_hours=48.0, stamps_dir=tmp)
        scripts = [r for r in recs if "script" in r]
        assert len(scripts) == len(SCRIPTS), f"expected {len(SCRIPTS)} records, got {len(scripts)}"
        for r in scripts:
            missing_keys = [k for k in REQUIRED_KEYS if k not in r]
            if missing_keys:
                failures.append(f"schema drift on {r.get('script')}: missing {missing_keys}")
            if not r["ok"]:
                failures.append(f"clean-state should be healthy: {r['script']} -> {r['error']}")
        # (b) clear one marker -> that exact script flagged within this run.
        victim = "convergence_fsm"
        (tmp / f"{victim}.json").unlink()
        recs2 = [r for r in probe(max_age_hours=48.0, stamps_dir=tmp) if "script" in r]
        vrec = next(r for r in recs2 if r["script"] == victim)
        if vrec["ok"]:
            failures.append(f"cleared-marker not flagged: {victim}")
        elif vrec["flag"] != "missing":
            failures.append(f"cleared-marker wrong flag: {victim} -> {vrec['flag']}")
        others = [r for r in recs2 if r["script"] != victim]
        if not all(r["ok"] for r in others):
            failures.append("collateral: non-victim script got flagged")
        # (c) stale marker -> flagged 'stale'.
        old = time.time() - 72 * 3600.0
        (tmp / f"{victim}.json").write_text(json.dumps({"ts": old}), encoding="utf-8")
        recs3 = [r for r in probe(max_age_hours=48.0, stamps_dir=tmp) if "script" in r]
        vrec3 = next(r for r in recs3 if r["script"] == victim)
        if vrec3["flag"] != "stale":
            failures.append(f"stale-marker not flagged 'stale': {victim} -> {vrec3['flag']}")
        # (d) live probe runs side-effect-free and emits valid JSONL.
        live = probe(max_age_hours=48.0)  # no stamps_dir -> real artifacts
        for r in live:
            json.dumps(r)  # must be serializable
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if failures:
        print("SELFTEST FAIL")
        for f_ in failures:
            print("  -", f_)
        return 1
    print("SELFTEST PASS: all-healthy on clean state; cleared marker flagged (missing); "
          "stale marker flagged (stale); JSONL schema stable; live probe serializable.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Builder autonomy-infra self-health probe")
    ap.add_argument("--max-age-hours", type=float, default=48.0)
    ap.add_argument("--stamps-dir", default=None)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--no-emit", action="store_true", help="print only, do not append JSONL")
    args = ap.parse_args(argv)
    if args.selftest:
        return _selftest()
    records = probe(max_age_hours=args.max_age_hours, stamps_dir=args.stamps_dir)
    for r in records:
        print(json.dumps(r))
    if not args.no_emit:
        emit(records)
        print(f"[infra_health] appended {len(records)} lines -> {OUT_JSONL}")
    summary = records[-1]
    return 0 if summary.get("all_healthy") else 2


if __name__ == "__main__":
    sys.exit(main())
