"""regression_alert.py — Backend detection engine for Designer Goal #2 (Regression Alert Banner).

Tracks fleet autonomy score, detects drops >5pts from rolling baseline,
manages 10-min cooldown, and emits structured alert events.

Usage:
    from regression_alert import RegressionAlertEngine
    eng = RegressionAlertEngine(state_file="memory/builder/regression_alert_state.json")
    eng.record_score(92.3)          # feed new score (e.g. from /api/health poll)
    event = eng.check()             # returns dict or None

Event schema (when triggered):
    {
        "type": "regression_alert",
        "severity": "critical" | "warning",
        "score_before": float,
        "score_after": float,
        "delta": float,            # negative = drop
        "triggered_at": ISO-8601,
        "cooldown_until": ISO-8601,
    }
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path

DROP_THRESHOLD = 5.0       # pts — triggers alert
COOLDOWN_SECONDS = 600     # 10 min
AUTO_DISMISS_SECONDS = 30  # 30s (frontend uses this; backend just records)
BASELINE_WINDOW = 5        # last N scores for rolling baseline


class RegressionAlertEngine:
    def __init__(self, state_file: str = "memory/builder/regression_alert_state.json"):
        self.state_file = Path(state_file)
        self.state = self._load()

    def _default_state(self):
        return {
            "history": [],          # list of {"score": float, "ts": ISO}
            "last_trigger_ts": None,
            "cooldown_until": None,
            "total_alerts": 0,
        }

    def _load(self):
        if self.state_file.exists():
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        return self._default_state()

    def _save(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self.state, indent=2), encoding="utf-8")

    def record_score(self, score: float):
        """Feed a new autonomy score (0-100)."""
        now = datetime.now(timezone.utc).isoformat()
        self.state["history"].append({"score": score, "ts": now})
        # Keep last 100 entries max
        if len(self.state["history"]) > 100:
            self.state["history"] = self.state["history"][-100:]
        self._save()

    def _baseline(self) -> float:
        """Rolling mean of last BASELINE_WINDOW scores (excluding current)."""
        entries = self.state["history"][:-1]  # exclude most recent
        if len(entries) < 2:
            return entries[0]["score"] if entries else 50.0
        window = entries[-BASELINE_WINDOW:]
        return sum(e["score"] for e in window) / len(window)

    def check(self) -> dict | None:
        """Check if a regression alert should fire. Returns event dict or None."""
        if len(self.state["history"]) < 2:
            return None

        current = self.state["history"][-1]["score"]
        baseline = self._baseline()
        delta = current - baseline  # negative = drop

        if delta >= -DROP_THRESHOLD:
            return None  # no regression

        # Cooldown check
        now_ts = time.time()
        if self.state["cooldown_until"]:
            cooldown_end = datetime.fromisoformat(self.state["cooldown_until"]).timestamp()
            if now_ts < cooldown_end:
                return None  # still in cooldown

        # Trigger alert
        now_iso = datetime.now(timezone.utc).isoformat()
        cooldown_end_iso = datetime.fromtimestamp(now_ts + COOLDOWN_SECONDS, tz=timezone.utc).isoformat()

        self.state["last_trigger_ts"] = now_iso
        self.state["cooldown_until"] = cooldown_end_iso
        self.state["total_alerts"] += 1
        self._save()

        severity = "critical" if delta <= -10 else "warning"
        return {
            "type": "regression_alert",
            "severity": severity,
            "score_before": round(baseline, 2),
            "score_after": round(current, 2),
            "delta": round(delta, 2),
            "triggered_at": now_iso,
            "cooldown_until": cooldown_end_iso,
        }

    def status(self) -> dict:
        """Current engine status for UI polling."""
        in_cooldown = False
        if self.state["cooldown_until"]:
            cooldown_end = datetime.fromisoformat(self.state["cooldown_until"]).timestamp()
            in_cooldown = time.time() < cooldown_end
        return {
            "last_score": self.state["history"][-1]["score"] if self.state["history"] else None,
            "baseline": round(self._baseline(), 2) if len(self.state["history"]) >= 2 else None,
            "in_cooldown": in_cooldown,
            "cooldown_until": self.state["cooldown_until"],
            "total_alerts": self.state["total_alerts"],
        }


# --- Self-test ---
if __name__ == "__main__":
    import tempfile, os

    tf = tempfile.mktemp(suffix=".json")
    eng = RegressionAlertEngine(state_file=tf)

    # Feed stable scores
    for s in [92.0, 93.0, 91.5, 92.5, 92.0]:
        eng.record_score(s)

    # No alert on small change
    eng.record_score(91.0)  # delta ~ -1.0 from baseline
    assert eng.check() is None, "FAIL: false positive on 1pt drop"
    print("PASS: no alert on 1pt drop")

    # Now simulate a 6pt drop
    eng2 = RegressionAlertEngine(state_file=tf)
    eng2.record_score(85.5)  # baseline ~92.2, delta ~ -6.7
    event = eng2.check()
    assert event is not None, "FAIL: no alert on 6pt drop"
    assert event["severity"] == "warning", f"FAIL: expected warning, got {event['severity']}"
    assert event["delta"] < -5.0
    print(f"PASS: 6pt drop triggers warning (delta={event['delta']})")

    # Cooldown: immediate re-check should return None
    eng3 = RegressionAlertEngine(state_file=tf)
    eng3.record_score(84.0)  # another big drop but in cooldown
    assert eng3.check() is None, "FAIL: cooldown not enforced"
    print("PASS: cooldown prevents re-trigger within 10min")

    # Critical severity on >10pt drop (fresh engine)
    tf2 = tempfile.mktemp(suffix=".json")
    eng4 = RegressionAlertEngine(state_file=tf2)
    for s in [95.0, 95.0, 95.0, 95.0]:
        eng4.record_score(s)
    eng4.record_score(83.0)  # delta = -12
    ev = eng4.check()
    assert ev is not None and ev["severity"] == "critical"
    print(f"PASS: 12pt drop triggers critical (delta={ev['delta']})")

    # Status endpoint
    st = eng4.status()
    assert st["last_score"] == 83.0
    assert st["in_cooldown"] is True
    assert st["total_alerts"] == 1
    print(f"PASS: status() correct (score={st['last_score']}, cooldown={st['in_cooldown']})")

    # Cleanup
    os.unlink(tf)
    os.unlink(tf2)
    print("\nALL TESTS PASS — regression_alert.py ready for UI wiring")
