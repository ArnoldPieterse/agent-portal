# Researcher — farm.py:569 cross-drive relpath diagnosis (2026-11-14, White seat)
Scope: evidence for Builder's lane `dcabots/farm.py:569` fix. All paths below = canonical tree `projects/dcabots/` on White (farm.py sha a1f6672e in THIS sandbox copy; Verifier pinned 5a563e80 on White disk — same-file cross-drive/case artifact class, content lines match).

## Root cause + exact repro
- `HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` (farm.py:46) → drive letter follows the PACKAGE LOCATION, not cwd. Default `out_dir` stays under HERE (`LIBRARY_ROOT`, line 550) → never cross-drive.
- Crash trigger: explicit `out_dir` on a different drive mount than HERE. Live repro = self-test: `cli.py:331` `_fdir = os.path.join(tmpd, "library")` where tmpd = system temp (C:\Users\...\Temp). Tree on Z:\ (SMB mirror) or temp on another drive → line 569 `os.path.relpath(out_dir, HERE)` raises `ValueError: path is on mount 'C:', start on mount 'Z:'`. Matches PROJECT.md L47 verbatim: "self-test exits non-zero after 29/29 [ok]" (all checks pass; banner kills the process).
- Note: PROJECT.md says "when cwd is on a different drive" — imprecise; it is `__file__` location (HERE) vs out_dir that matters. Fix identical either way.

## All same-class call sites in tree (not just :569)
| file | lines |
|---|---|
| dcabots/farm.py | 403, 515, **569**, 668 (line 668 = "done" banner — crashes AFTER a successful run; equally fatal) |
| dcabots/daily.py | 361, 369 |
| dcabots/e13.py | 283 |
| dcabots/e14.py | 507 |
| dcabots/e4.py | 97 |
| dcabots/e5.py | 128 |
| dcabots/research.py | 199 |
| logs/finish_final_report.py | 188, 224, 243, 296, 305, 376, 378 (ROOT-relative; same ValueError class) |

## Recommended fix (for Builder)
Add one shared helper (e.g. in `dcabots/protocol.py` or a new `paths.py`) and route ALL sites through it:
```python
def rel_display(path: str, base: str) -> str:
    """relpath that degrades to abspath across drive mounts (Windows Z:/C:)."""
    try:
        return os.path.relpath(path, base)
    except ValueError:
        return os.path.abspath(path)
```
- `os.path.commonpath` also raises ValueError cross-drive — try/except is the guard PROJECT.md suggests and the simplest correct one.
- Minimal acceptable: fix farm.py:569 + :668 (both run_farm banners) so self-test goes green; full sweep of the table above = robust. Verifier re-run gate stays: self-test from canonical path, exit 0 with 29/29 [ok] AND no traceback after.

## Remaining-item status (evidence-backed, as of ~02:2x)
| item | owner | state |
|---|---|---|
| farm.py:569 fix + Verifier re-run | Builder → Verifier | diagnosis above; unblocked for Builder |
| AC-A2-1..4 on PID 23704 | Verifier (done structurally) + adjudication | r19 leaf submitted: A2-1 PARTIAL (outside-click-close absent — matches house style of other 3 panels), A2-2 static PASS / live OPEN, A2-3 PASS structural, A2-4 PASS. **Two adjudications owed to Orchestrator**: (1) accept house-style no-outside-close or spec shared close handler; (2) design token family — live dark family has ZERO locked r60-token hexes → migrate page or re-scope lock (Designer post-restart-verify-r19.md FAIL #1). |
| Scribe queue ④ rebuild | Scribe (+ Mechanic/Scribe-Red) | STILL BLOCKED: Red master 13c97dfb has no relayed copy in White memory/ — all mentions are pre-11-14 analysis refs; needs Mechanic pull or Scribe-Red new-file relay (new files propagate, existing-edit skips). |
| smoke8 / live :8099 from seats | n/a (policy) | re-probed THIS round from White seat: loopback connect blocked by sandbox allowlist (guard refuses 127.0.0.1 outright) — same class as Orchestrator/Verifier records; live legs stay White-browser/Mechic-proxy. |
| E14 resume 89/440 + stage-3 report + E15 | human (Arnold, White console/RDP) | unchanged; mock-fallback trap documented in projects/dcabots.md; agent sandbox cannot reach :1235. |
| dcabots group-task re-prompt | human (Arnold) | only Orchestrator's turn failed (atlas-q8 404 window); other seven seats answered — a plain re-send is sufficient, no prep needed from agents. |

## Confidence / uncertainty
- HIGH: root cause + repro (code read first-hand, matches PROJECT.md report and Verifier's 29/29-then-fail observation). MEDIUM: White-disk farm.py byte pin (my sandbox copy md5 a1f6672e vs Verifier's 5a563e80 — line content matches; likely the known line-ending/case artifact class, not a variant; Builder should confirm pin on target file before/after patch). LOW/none: live portal behavior (unreachable from seat by policy).
