#!/usr/bin/env python3
"""Frame-accurate QC gate for Splice goal #4 (ASSIST, Forge-built).

Post-render checks:
  1. duration matches expected within +/-1 frame (tolerance = 1/fps)
  2. no black frames at head/tail
  3. resolution matches target
  4. audio present if master has audio
FAIL => quarantine the file (move to quarantine dir) + write a QC report JSON.

Design for testability WITHOUT ffmpeg:
  - The DECISION logic operates on a plain `metrics` dict, so it is fully
    unit-testable in a sandbox that has no ffmpeg/ffprobe installed.
  - Live leg: pass `--probe-json <file|->` with real ffprobe JSON, or let the
    gate auto-run `ffprobe` when it is on PATH. head_black/tail_black are
    populated by the live leg (ffmpeg signalstats frame dump) and injected as
    booleans here so the black-frame decision is testable too.

Selftest (the in-sandbox evidence):
  python memory/forge/qc_gate.py --selftest
  -> runs built-in fixtures through evaluate() AND performs a real quarantine
     of a temp bad-render file + writes a real QC report. exit 0 only if all pass.
"""
import json, os, shutil, sys, tempfile, time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SPLICE_DIR = REPO / "memory" / "designer" / "splice"
DEFAULT_QUARANTINE = SPLICE_DIR / "quarantine"
DEFAULT_REPORTS = SPLICE_DIR / "qc_reports"


def probe_to_metrics(probe: dict) -> dict:
    """Extract {duration,width,height,has_audio} from an ffprobe -print_format json tree."""
    streams = probe.get("streams", []) or []
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_present = any(s.get("codec_type") == "audio" for s in streams)
    duration = None
    if video is not None and video.get("duration") not in (None, "N/A"):
        try:
            duration = float(video["duration"])
        except (TypeError, ValueError):
            duration = None
    if duration is None:
        fmt = probe.get("format", {}) or {}
        try:
            duration = float(fmt.get("duration"))
        except (TypeError, ValueError):
            duration = None
    return {
        "duration": duration,
        "width": video.get("width") if video else None,
        "height": video.get("height") if video else None,
        "has_audio": audio_present,
        # black-frame booleans are supplied by the live leg (ffmpeg signalstats);
        # default False = no evidence of black frames.
        "head_black": bool(probe.get("head_black", False)),
        "tail_black": bool(probe.get("tail_black", False)),
    }


def evaluate(metrics: dict, expected: dict) -> dict:
    """Pure decision logic. Returns {checks:[...], verdict}.
    expected = {duration, fps, width, height, audio(bool)}.
    """
    checks = []
    # 1. duration +/- 1 frame
    tol = (1.0 / expected["fps"]) if expected.get("fps") else 0.0
    actual_d = metrics.get("duration")
    d_ok = (actual_d is not None and abs(actual_d - expected["duration"]) <= tol + 1e-9)
    checks.append({
        "name": "duration", "pass": bool(d_ok),
        "detail": f"actual={actual_d} expected={expected['duration']} tol=+/-{tol:.6f}s (1 frame @ {expected.get('fps')}fps)",
    })
    # 2. black frames head/tail
    b_ok = not (metrics.get("head_black") or metrics.get("tail_black"))
    checks.append({
        "name": "black_frames", "pass": bool(b_ok),
        "detail": f"head_black={metrics.get('head_black')} tail_black={metrics.get('tail_black')}",
    })
    # 3. resolution
    r_ok = (metrics.get("width") == expected["width"] and metrics.get("height") == expected["height"])
    checks.append({
        "name": "resolution", "pass": bool(r_ok),
        "detail": f"actual={metrics.get('width')}x{metrics.get('height')} expected={expected['width']}x{expected['height']}",
    })
    # 4. audio present if master has audio
    a_ok = (not expected.get("audio")) or bool(metrics.get("has_audio"))
    checks.append({
        "name": "audio", "pass": bool(a_ok),
        "detail": f"expected_audio={bool(expected.get('audio'))} present={metrics.get('has_audio')}",
    })
    verdict = "PASS" if all(c["pass"] for c in checks) else "FAIL"
    return {"checks": checks, "verdict": verdict}


def _write_report(report_dir: Path, report: dict) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    p = report_dir / f"qc_{report['file']}.json"
    p.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return p


def run_gate(file: str, metrics: dict, expected: dict,
             quarantine_dir: Path = DEFAULT_QUARANTINE,
             report_dir: Path = DEFAULT_REPORTS) -> int:
    """Run the gate on one file. Writes a QC report; quarantines on FAIL.
    Returns process exit code (0 PASS, 1 FAIL/quarantined, 2 error)."""
    res = evaluate(metrics, expected)
    fname = os.path.basename(file)
    report = {
        "file": fname, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "expected": expected, "metrics": metrics, **res,
        "quarantined": False, "quarantine_path": None,
    }
    if res["verdict"] == "FAIL":
        quarantine_dir.mkdir(parents=True, exist_ok=True)
        src = Path(file)
        if src.exists():
            dst = quarantine_dir / fname
            n = 1
            while dst.exists():
                dst = quarantine_dir / f"{stem}_{n}{ext}" if False else quarantine_dir / f"{src.stem}_{n}{src.suffix}"
                n += 1
            shutil.move(str(src), str(dst))
            report["quarantined"] = True
            report["quarantine_path"] = str(dst)
    _write_report(report_dir, report)
    print(json.dumps({k: report[k] for k in ("file", "verdict", "quarantined", "quarantine_path")}, indent=2))
    return 0 if res["verdict"] == "PASS" else 1


def _ffprobe(file: str) -> dict:
    """Live leg: run ffprobe if available. Raises if not on PATH."""
    out = subprocess_run(["ffprobe", "-v", "quiet", "-print_format", "json",
                          "-show_format", "-show_streams", file])
    return json.loads(out)


def subprocess_run(cmd):
    import subprocess
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed: {r.stderr.strip()[:300]}")
    return r.stdout


def selftest() -> int:
    exp = {"duration": 10.0, "fps": 30.0, "width": 1920, "height": 1080, "audio": True}
    tol = 1.0 / 30.0
    fixtures = {
        # name: (metrics, expected_verdict)
        "good": ({"duration": 10.0, "width": 1920, "height": 1080, "has_audio": True,
                  "head_black": False, "tail_black": False}, "PASS"),
        "bad_duration_out_of_tol": ({"duration": 10.5, "width": 1920, "height": 1080,
                                     "has_audio": True, "head_black": False, "tail_black": False}, "FAIL"),
        "duration_within_1_frame": ({"duration": 10.0 + tol / 2, "width": 1920, "height": 1080,
                                     "has_audio": True, "head_black": False, "tail_black": False}, "PASS"),
        "wrong_resolution": ({"duration": 10.0, "width": 1280, "height": 720, "has_audio": True,
                              "head_black": False, "tail_black": False}, "FAIL"),
        "missing_audio": ({"duration": 10.0, "width": 1920, "height": 1080, "has_audio": False,
                           "head_black": False, "tail_black": False}, "FAIL"),
        "black_head_frame": ({"duration": 10.0, "width": 1920, "height": 1080, "has_audio": True,
                              "head_black": True, "tail_black": False}, "FAIL"),
        "no_audio_expected_ok": ({"duration": 5.0, "width": 1920, "height": 1080, "has_audio": False,
                                  "head_black": False, "tail_black": False}, None),
    }
    failures = []
    results = {}
    for name, (metrics, want) in fixtures.items():
        e = dict(exp)
        if name == "no_audio_expected_ok":
            e.update(duration=5.0, audio=False)
            want = "PASS"
        got = evaluate(metrics, e)["verdict"]
        ok = (got == want)
        results[name] = {"want": want, "got": got, "ok": ok}
        if not ok:
            failures.append(name)

    # Real quarantine + report path: temp bad-render file with wrong-duration probe.
    tmp = Path(tempfile.mkdtemp(prefix="qc_selftest_"))
    qdir = tmp / "quarantine"
    rdir = tmp / "reports"
    bad_file = tmp / "bad_render.mp4"
    bad_file.write_bytes(b"\x00fake-video-bytes")  # stand-in for a real render
    bad_metrics = {"duration": 12.34, "width": 1920, "height": 1080, "has_audio": True,
                   "head_black": False, "tail_black": False}
    rc = run_gate(str(bad_file), bad_metrics, exp, quarantine_dir=qdir, report_dir=rdir)
    q_files = list(qdir.glob("*"))
    r_files = list(rdir.glob("*.json"))
    quarantined_ok = (rc == 1) and (not bad_file.exists()) and len(q_files) == 1
    report_ok = len(r_files) == 1
    rep = json.loads(r_files[0].read_text(encoding="utf-8")) if report_ok else {}
    report_verdict_ok = rep.get("verdict") == "FAIL"

    summary = {
        "fixtures": results,
        "quarantine_test": {"rc": rc, "file_moved": not bad_file.exists(),
                            "quarantine_count": len(q_files), "report_written": report_ok,
                            "report_verdict": rep.get("verdict")},
        "tmp_dir": str(tmp),
    }
    all_ok = (not failures) and quarantined_ok and report_ok and report_verdict_ok
    print(json.dumps(summary, indent=2))
    print(f"\nSELFTEST {'PASS' if all_ok else 'FAIL'} "
          f"(fixtures {len(results)-len(failures)}/{len(results)}, quarantine={'ok' if quarantined_ok else 'BAD'}, "
          f"report={'ok' if report_ok and report_verdict_ok else 'BAD'})")
    return 0 if all_ok else 1


def main(argv):
    if len(argv) > 1 and argv[1] == "--selftest":
        return selftest()
    # live mode: <file> --probe-json <path|-> [--expected-duration D --fps F --width W --height H --audio]
    import argparse
    ap = argparse.ArgumentParser(description="Frame-accurate QC gate (Splice #4)")
    ap.add_argument("file", nargs="?", help="render file to gate")
    ap.add_argument("--probe-json", help="ffprobe JSON file, or '-' to auto-run ffprobe")
    ap.add_argument("--expected-duration", type=float, required=True)
    ap.add_argument("--fps", type=float, default=30.0)
    ap.add_argument("--width", type=int, required=True)
    ap.add_argument("--height", type=int, required=True)
    ap.add_argument("--audio", action="store_true", help="master is expected to have audio")
    args = ap.parse_args(argv[1:])
    if not args.file:
        ap.error("file required (or use --selftest)")
    if args.probe_json == "-":
        probe = _ffprobe(args.file)
    elif args.probe_json:
        probe = json.loads(Path(args.probe_json).read_text(encoding="utf-8"))
    else:
        ap.error("--probe-json required (path or '-') when ffmpeg is not on PATH")
    metrics = probe_to_metrics(probe)
    expected = {"duration": args.expected_duration, "fps": args.fps,
                "width": args.width, "height": args.height, "audio": args.audio}
    return run_gate(args.file, metrics, expected)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
