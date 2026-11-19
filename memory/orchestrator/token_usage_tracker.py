"""
token_usage_tracker.py - Orchestrator cycle-7 goal 2 (Fleet Capacity Dashboard v2)
Per-agent LLM token usage tracking + 7-day trend aggregation.

Data format (JSONL in memory/orchestrator/token_usage.jsonl):
  {"ts": "2026-11-20T01:00:00+00:00", "agent": "researcher", "model": "qwen3-27b-q8",
   "input_tokens": 1200, "output_tokens": 450}

Usage:
  from memory.orchestrator.token_usage_tracker import append_usage, get_7day_trend
  append_usage("researcher", "qwen3-27b-q8", 1200, 450)
  trend = get_7day_trend()  # -> {agent: [{date, input_tokens, output_tokens, total}, ...]}
"""
import json, os, time
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
USAGE_FILE = os.path.join(HERE, "token_usage.jsonl")


def append_usage(agent: str, model: str, input_tokens: int, output_tokens: int) -> None:
    """Append one usage record. Safe to call from portal request handler."""
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": agent,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }
    with open(USAGE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def get_7day_trend() -> dict:
    """Return per-agent 7-day token usage trend.

    Returns: {agent_name: [{date, input_tokens, output_tokens, total}, ...]}
    Each agent gets exactly 7 entries (oldest first), zero-filled for missing days.
    """
    records = []
    if os.path.exists(USAGE_FILE):
        with open(USAGE_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    now = datetime.now(timezone.utc)
    days = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    day_set = set(days)

    buckets = {}
    for rec in records:
        try:
            ts = rec["ts"][:10]
        except (KeyError, TypeError):
            continue
        if ts not in day_set:
            continue
        agent = rec.get("agent", "unknown")
        key = (agent, ts)
        if key not in buckets:
            buckets[key] = {"input_tokens": 0, "output_tokens": 0}
        buckets[key]["input_tokens"] += rec.get("input_tokens", 0)
        buckets[key]["output_tokens"] += rec.get("output_tokens", 0)

    agents = set(k[0] for k in buckets) or {"unknown"}
    result = {}
    for agent in sorted(agents):
        series = []
        for d in days:
            b = buckets.get((agent, d), {"input_tokens": 0, "output_tokens": 0})
            it, ot = b["input_tokens"], b["output_tokens"]
            series.append({
                "date": d,
                "input_tokens": it,
                "output_tokens": ot,
                "total": it + ot,
            })
        result[agent] = series
    return result


def _aggregate(records: list) -> dict:
    """Core aggregation logic (exposed for unit testing)."""
    now = datetime.now(timezone.utc)
    days = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    day_set = set(days)

    buckets = {}
    for rec in records:
        try:
            ts = rec["ts"][:10]
        except (KeyError, TypeError):
            continue
        if ts not in day_set:
            continue
        agent = rec.get("agent", "unknown")
        key = (agent, ts)
        if key not in buckets:
            buckets[key] = {"input_tokens": 0, "output_tokens": 0}
        buckets[key]["input_tokens"] += rec.get("input_tokens", 0)
        buckets[key]["output_tokens"] += rec.get("output_tokens", 0)

    agents = set(k[0] for k in buckets) or {"unknown"}
    result = {}
    for agent in sorted(agents):
        series = []
        for d in days:
            b = buckets.get((agent, d), {"input_tokens": 0, "output_tokens": 0})
            it, ot = b["input_tokens"], b["output_tokens"]
            series.append({"date": d, "input_tokens": it, "output_tokens": ot, "total": it + ot})
        result[agent] = series
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        tmp = os.path.join(HERE, "_test_usage.jsonl")
        old = USAGE_FILE
        USAGE_FILE = tmp
        append_usage("researcher", "qwen3-27b-q8", 1000, 500)
        append_usage("builder", "qwen3-27b-q4", 800, 300)
        result = get_7day_trend()
        assert "researcher" in result and len(result["researcher"]) == 7
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        r_today = [e for e in result["researcher"] if e["date"] == today][0]
        assert r_today["input_tokens"] == 1000 and r_today["output_tokens"] == 500
        b_today = [e for e in result["builder"] if e["date"] == today][0]
        assert b_today["total"] == 1100
        USAGE_FILE = old
        os.remove(tmp)
        print("SELFTEST PASS: get_7day_trend returns 7-day series per agent, values correct")
    else:
        trend = get_7day_trend()
        print(json.dumps(trend, indent=2))
