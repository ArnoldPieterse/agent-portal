#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""fleet_trust_score.py - Researcher Goal 9 (cycle-11): Fleet Trust Score.

Combines the three autonomy signals into a 0-100 trust score:
  loop-closure rate   (loop-closure-report.md)      weight 0.4
  mean decision conf. (decision-confidence-report.json) weight 0.3
  calibration         (calibration-report.md, Brier) weight 0.3
Appends exactly one row per run to trust-history.jsonl, and only when the
input reports changed since the last row (idempotent on same input).

Usage:
  python fleet_trust_score.py            # compute + maybe append
  python fleet_trust_score.py selftest   # high vs low state differ by >=20
"""
import hashlib, json, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
HIST = os.path.join(HERE, "trust-history.jsonl")


def _read(p):
    try:
        return open(os.path.join(HERE, p), encoding="utf-8", errors="replace").read()
    except OSError:
        return ""


def read_signals():
    sig = {}
    m = re.search(r"closure rate:\s*([0-9.]+)%", _read("loop-closure-report.md"))
    sig["closure_rate"] = float(m.group(1)) / 100.0 if m else None
    try:
        d = json.loads(_read("decision-confidence-report.json"))
        sig["mean_confidence"] = d.get("mean_confidence", d.get("mean"))
    except (ValueError, AttributeError):
        sig["mean_confidence"] = None
    m = re.search(r"Brier:\s*([0-9.]+)", _read("calibration-report.md"))
    sig["brier"] = float(m.group(1)) if m else None
    return sig


def trust_score(sig):
    """Weights documented in module docstring; missing signal -> that weight
    redistributed proportionally (never invents a value)."""
    parts = []
    if sig.get("closure_rate") is not None:
        parts.append((0.4, max(0.0, min(1.0, sig["closure_rate"]))))
    if sig.get("mean_confidence") is not None:
        parts.append((0.3, max(0.0, min(1.0, sig["mean_confidence"]))))
    if sig.get("brier") is not None:
        # lower Brier = better calibrated; map 0->1.0, 0.25->0.0
        parts.append((0.3, max(0.0, min(1.0, (0.25 - sig["brier"]) / 0.25))))
    if not parts:
        return None
    wsum = sum(w for w, _ in parts)
    return round(100.0 * sum(w * v for w, v in parts) / wsum, 1)


def compute():
    sig = read_signals()
    score = trust_score(sig)
    inputs_hash = hashlib.sha256(json.dumps(sig, sort_keys=True).encode()).hexdigest()[:12]
    row = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "signals": sig,
           "trust_score": score, "inputs_hash": inputs_hash}
    appended = False
    if os.path.exists(HIST):
        last = ""
        for line in open(HIST, encoding="utf-8", errors="replace"):
            if line.strip():
                last = line.strip()
        try:
            if json.loads(last).get("inputs_hash") == inputs_hash:
                appended = False  # idempotent: same inputs, skip append
            else:
                open(HIST, "a", encoding="utf-8").write(json.dumps(row) + "\n")
                appended = True
        except ValueError:
            open(HIST, "a", encoding="utf-8").write(json.dumps(row) + "\n")
            appended = True
    else:
        open(HIST, "w", encoding="utf-8").write(json.dumps(row) + "\n")
        appended = True
    return row, appended


def selftest():
    # high-trust state vs low-trust state must differ by >=20 points
    hi = trust_score({"closure_rate": 0.95, "mean_confidence": 0.8, "brier": 0.05})
    lo = trust_score({"closure_rate": 0.40, "mean_confidence": 0.15, "brier": 0.24})
    assert hi is not None and lo is not None
    assert hi - lo >= 20, "high-low gap %.1f (<20)" % (hi - lo)
    # determinism
    assert trust_score({"closure_rate": 0.95, "mean_confidence": 0.8, "brier": 0.05}) == hi
    # missing signal: redistributes, still in range
    mid = trust_score({"closure_rate": 0.7, "mean_confidence": None, "brier": None})
    assert mid is not None and 0 <= mid <= 100
    # live compute + idempotency: two runs, second must NOT append
    row1, a1 = compute()
    row2, a2 = compute()
    assert row1["inputs_hash"] == row2["inputs_hash"]
    assert not a2, "second run appended despite identical inputs"
    print("high=%.1f low=%.1f gap=%.1f | live score=%s (append1=%s append2=%s)"
          % (hi, lo, hi - lo, row1["trust_score"], a1, a2))
    print("SELFTEST PASS")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        selftest()
    else:
        row, appended = compute()
        print(json.dumps(row, indent=1), "\nappended:", appended)

