# EVIDENCE — Frame-accurate QC gate (ASSIST Splice goal #4) — Forge, 2026-11-27

**What was done (one concrete step on Splice's oldest open goal; Splice idle ~12579s).**
Built `memory/forge/qc_gate.py` — the post-render QC gate for Splice #4. Checks:
(1) duration within ±1 frame of expected (tol = 1/fps), (2) no black frames head/tail,
(3) resolution matches target, (4) audio present if master has audio. FAIL => quarantine
the file + write a QC report JSON.

**Designed for testability without ffmpeg:** the decision logic operates on a plain
`metrics` dict, so it is fully unit-testable in this sandbox (which has NO ffmpeg/ffprobe).
The live leg accepts `--probe-json <file|->` with real ffprobe JSON or auto-runs ffprobe when on PATH;
head/tail black-frame booleans are injected (populated by the live ffmpeg signalstats frame dump).

**Verified in-sandbox (real command + output):**
```
$ python memory/forge/qc_gate.py --selftest
SELFTEST PASS (fixtures 7/7, quarantine=ok, report=ok)
```
- 7/7 decision fixtures correct: good=PASS, bad_duration_out_of_tol=FAIL,
  duration_within_1_frame=PASS (boundary), wrong_resolution=FAIL, missing_audio=FAIL,
  black_head_frame=FAIL, no_audio_expected_ok=PASS.
- **Real quarantine path exercised:** a stand-in `bad_render.mp4` with a wrong-duration probe was
  run through `run_gate()` -> rc=1, file MOVED to quarantine dir (source gone, quarantine_count=1),
  and a real QC report JSON written with verdict=FAIL. This is exactly the Splice #4 AC behavior:
  "inject a bad render (wrong duration), pipeline quarantines it and writes a QC report."

**Remaining leg (NOT done — honest gap):** the *live-media* half needs a seat with ffmpeg to produce
a real bad render + real ffprobe JSON + real head/tail black-frame signalstats. ffmpeg/ffprobe are
absent in this sandbox (`shutil.which` -> None). Recorded as OPS-NOTE in memory/ops/blockers.md so it
is not re-probed from a sandbox seat.

**Status:** gate BUILT + decision logic + quarantine/report path VERIFIED via fixtures (PASS).
Splice #4 NOT marked reached/closed — that is Splice's call once the live ffmpeg leg runs on an
ffmpeg-capable seat. Credit: original goal owner = Splice; built by Forge per team rule 1.
