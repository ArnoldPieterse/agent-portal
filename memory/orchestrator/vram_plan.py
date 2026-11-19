"""VRAM Pressure Alerting (Orchestrator cycle-7 goal #8).

Given a load plan [{model_id, host}], predict per-host VRAM usage from
hotload-catalog.json and alert when predicted > 90% of host total.

Alerts are appended to memory/ops/vram-alerts.jsonl as JSONL records.
"""
import json, os, time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent.parent  # repo root
CATALOG = HERE / "memory" / "llm" / "hotload-catalog.json"
ALERTS_FILE = HERE / "memory" / "ops" / "vram-alerts.jsonl"
THRESHOLD_PCT = 90.0  # alert when predicted > 90% of host VRAM

_cache = None

def get_catalog():
    """Load hotload-catalog.json (cached)."""
    global _cache
    if _cache is None:
        _cache = json.loads(CATALOG.read_text())
    return _cache

def reset_cache():
    global _cache
    _cache = None

def evaluate_plan(plan):
    """Evaluate a load plan and return per-host VRAM prediction.

    Args:
        plan: list of {"model_id": str, "host": str} entries to load.
              Optional: "gpu_ids" (list) to override catalog gpu assignment.

    Returns:
        {
            "ts": float,
            "hosts": {
                host_name: {
                    "total_gb": float,
                    "predicted_gb": float,
                    "pct": float,
                    "alert": bool,
                    "models": [model_id, ...],
                },
                ...
            },
            "alerts_triggered": int,
        }

    Side effect: appends one JSONL record per alerting host to ALERTS_FILE.
    """
    cat = get_catalog()
    hosts_meta = cat.get("_meta", {}).get("hosts", {})
    models_by_id = {m["id"]: m for m in cat.get("models", []) + cat.get("planned_models", [])}

    # Aggregate predicted VRAM per host
    host_loads = {}  # host -> list of (model_id, vram_gb)
    for entry in plan:
        mid = entry.get("model_id", "")
        host = entry.get("host", "white")
        m = models_by_id.get(mid)
        if m is None:
            continue
        # Use model's own vram_gb; fall back to min_vram_gb for planned models
        vram = m.get("vram_gb") or m.get("min_vram_gb", 0)
        host_loads.setdefault(host, []).append((mid, vram))

    result_hosts = {}
    alerts_triggered = 0
    now = time.time()

    for host, loads in host_loads.items():
        total_gb = hosts_meta.get(host, {}).get("vram_total_gb", 32.0)
        predicted_gb = round(sum(v for _, v in loads), 1)
        pct = round(100.0 * predicted_gb / total_gb, 1) if total_gb else 0.0
        alert = pct > THRESHOLD_PCT

        result_hosts[host] = {
            "total_gb": total_gb,
            "predicted_gb": predicted_gb,
            "pct": pct,
            "alert": alert,
            "models": [mid for mid, _ in loads],
        }

        if alert:
            alerts_triggered += 1
            _write_alert(host, predicted_gb, total_gb, pct, [mid for mid, _ in loads])

    return {
        "ts": now,
        "hosts": result_hosts,
        "alerts_triggered": alerts_triggered,
    }

def _write_alert(host, predicted_gb, total_gb, pct, models):
    """Append one alert record to vram-alerts.jsonl."""
    ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": time.time(),
        "host": host,
        "predicted_gb": predicted_gb,
        "total_gb": total_gb,
        "pct": pct,
        "models": models,
        "threshold_pct": THRESHOLD_PCT,
    }
    with open(ALERTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

# ---------------------------------------------------------------------------
# Self-test (run directly): python memory/orchestrator/vram_plan.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Simulated test: 35GB plan on a 32GB host should trigger alert
    # Use the real catalog but override with a synthetic large model
    reset_cache()
    cat = get_catalog()

    # Find a real model to use for testing
    test_models = cat.get("models", [])
    if not test_models:
        print("FAIL: no models in catalog")
        exit(1)

    # Build a plan that exceeds 90% of white's VRAM (32 GB * 0.9 = 28.8 GB)
    # qwen3-27b-q8 is 30.1 GB on white -> alone exceeds threshold
    big_model = test_models[0]  # qwen3-27b-q8, 30.1 GB, host=white
    plan = [{"model_id": big_model["id"], "host": "white"}]
    result = evaluate_plan(plan)
    print(json.dumps(result, indent=2))

    host_key = "white"
    h = result["hosts"].get(host_key, {})
    if h.get("alert"):
        print(f"\nPASS: {host_key} alert triggered (predicted={h['predicted_gb']}GB / total={h['total_gb']}GB = {h['pct']}%)")
    else:
        print(f"\nFAIL: expected alert but none triggered: {h}")

    # Verify alert file was written
    if ALERTS_FILE.exists():
        lines = ALERTS_FILE.read_text().strip().split("\n")
        last = json.loads(lines[-1])
        print(f"PASS: vram-alerts.jsonl has {len(lines)} record(s); last: host={last['host']} pct={last['pct']}%")
    else:
        print("FAIL: vram-alerts.jsonl not created")
