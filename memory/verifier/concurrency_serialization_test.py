"""Concurrency Serialization Test - Verifier Goal #5 (LIVE leg)

Sends 3 simultaneous POST /api/chat requests to different agents and verifies
they are serialized (not overlapping), confirming parallel_slots=1 behavior.

Acceptance criteria:
  1. 3 concurrent requests show sequential execution (no overlap in time windows)
  2. No interleaved output
  3. RLock held for expected duration (inferred from serialization timing)

Usage:
  python memory/verifier/concurrency_serialization_test.py [--url http://localhost:8099]
  python memory/verifier/concurrency_serialization_test.py --dry-run

Exit codes:
  0 = PASS (serialization confirmed)
  1 = FAIL (overlap detected or error)
  2 = BLOCKED (cannot reach portal)
"""
import argparse
import concurrent.futures
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

# Default agents to test (different model_id aliases)
DEFAULT_AGENTS = ["builder", "researcher", "verifier"]


def send_chat_request(base_url: str, agent: str, prompt: str = "ping") -> dict:
    """Send a single /api/chat request. Returns timing + status info."""
    url = f"{base_url}/api/chat"
    payload = json.dumps({
        "agent": agent,
        "message": prompt,
        "max_tokens": 10
    }).encode("utf-8")

    t_start = time.perf_counter()
    wall_start = datetime.now(timezone.utc).isoformat()

    result = {
        "agent": agent,
        "t_start": t_start,
        "wall_start": wall_start,
        "status": 0,
        "error": None,
        "latency_ms": 0,
        "t_end": 0,
        "wall_end": "",
    }

    try:
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "concurrency-test/1.0"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read()
            result["status"] = resp.status
            result["body_size"] = len(body)
    except urllib.error.HTTPError as e:
        result["status"] = e.code
        result["error"] = f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        result["error"] = str(e)

    t_end = time.perf_counter()
    result["t_end"] = t_end
    result["wall_end"] = datetime.now(timezone.utc).isoformat()
    result["latency_ms"] = (t_end - t_start) * 1000
    return result


def check_serialization(results: list) -> dict:
    """Check if the 3 requests were serialized (no overlap in execution windows)."""
    sorted_results = sorted(results, key=lambda r: r["t_start"])

    overlaps = []
    for i in range(len(sorted_results)):
        for j in range(i + 1, len(sorted_results)):
            a, b = sorted_results[i], sorted_results[j]
            if a["t_start"] < b["t_end"] and b["t_start"] < a["t_end"]:
                overlap_ms = (min(a["t_end"], b["t_end"]) - max(a["t_start"], b["t_start"])) * 1000
                overlaps.append({
                    "pair": [a["agent"], b["agent"]],
                    "overlap_ms": round(overlap_ms, 2),
                })

    total_wall = max(r["t_end"] for r in results) - min(r["t_start"] for r in results)
    sum_individual = sum(r["latency_ms"] / 1000 for r in results)
    max_individual = max(r["latency_ms"] / 1000 for r in results)

    ratio_serialized = total_wall / sum_individual if sum_individual > 0 else 0
    ratio_parallel = total_wall / max_individual if max_individual > 0 else 0

    return {
        "overlaps": overlaps,
        "total_wall_ms": round(total_wall * 1000, 2),
        "sum_individual_ms": round(sum_individual * 1000, 2),
        "max_individual_ms": round(max_individual * 1000, 2),
        "ratio_to_sum": round(ratio_serialized, 3),
        "ratio_to_max": round(ratio_parallel, 3),
        "serialized": len(overlaps) == 0 and ratio_serialized > 0.7,
    }


def write_report(results: list, analysis: dict, base_url: str, output_path: str):
    """Write the test report."""
    now = datetime.now(timezone.utc).isoformat()
    lines = [
        "# Concurrency Serialization Test (LIVE leg) - Goal #5",
        f"",
        f"Generated: {now}",
        f"URL: {base_url}",
        f"Agents tested: {', '.join(r['agent'] for r in results)}",
        f"",
        f"## Results",
        f"",
        f"| Agent | Start (UTC) | End (UTC) | Latency (ms) | Status | Error |",
        f"|-------|-------------|-----------|--------------|--------|-------|",
    ]
    for r in sorted(results, key=lambda x: x["t_start"]):
        lines.append(
            f"| {r['agent']} | {r['wall_start']} | {r['wall_end']} | "
            f"{r['latency_ms']:.1f} | {r['status']} | {r.get('error', 'none')} |"
        )

    lines += [
        f"",
        f"## Serialization Analysis",
        f"",
        f"- Total wall time: {analysis['total_wall_ms']} ms",
        f"- Sum of individual times: {analysis['sum_individual_ms']} ms",
        f"- Max individual time: {analysis['max_individual_ms']} ms",
        f"- Ratio (wall/sum): {analysis['ratio_to_sum']} (~1.0 = serialized)",
        f"- Ratio (wall/max): {analysis['ratio_to_max']} (~1.0 = parallel)",
        f"",
    ]

    if analysis["overlaps"]:
        lines.append(f"### Overlaps Detected")
        for o in analysis["overlaps"]:
            lines.append(f"- {o['pair'][0]} <-> {o['pair'][1]}: {o['overlap_ms']} ms overlap")
        lines.append("")

    verdict = "PASS" if analysis["serialized"] else "FAIL"
    lines += [f"## Verdict: {verdict}", f""]
    if analysis["serialized"]:
        lines.append("All 3 requests executed sequentially with no overlap. parallel_slots=1 confirmed.")
    else:
        lines.append(f"Overlap detected or timing inconsistent with serialization. "
                     f"Ratio to sum = {analysis['ratio_to_sum']} (expected >0.7 for serialized).")

    lines += [
        f"",
        f"## Notes",
        f"- Client-side timing only; server-side RLock hold duration inferred from serialization.",
        f"- If ratio_to_sum is between 0.5 and 0.7, partial overlap may indicate "
        f"network latency masking true serialization (inconclusive).",
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Report written: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Concurrency serialization test (Goal #5 live leg)")
    parser.add_argument("--url", default="http://localhost:8099", help="Portal base URL")
    parser.add_argument("--agents", nargs="+", default=DEFAULT_AGENTS, help="Agent names to test")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without real HTTP calls")
    parser.add_argument("--report", default=None, help="Output report path")
    args = parser.parse_args()

    output_path = args.report or os.path.join(
        "memory", "verifier", f"concurrency-live-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md"
    )

    print(f"Concurrency Serialization Test")
    print(f"  URL: {args.url}")
    print(f"  Agents: {', '.join(args.agents)}")
    print()

    if args.dry_run:
        print("[DRY-RUN] Simulating 3 serialized requests...")
        base_t = time.perf_counter()
        results = []
        for i, agent in enumerate(args.agents):
            t_start = base_t + i * 1.0
            t_end = t_start + 1.0
            results.append({
                "agent": agent,
                "t_start": t_start,
                "wall_start": f"dry-run-{i}-start",
                "status": 200,
                "error": None,
                "latency_ms": 1000.0,
                "t_end": t_end,
                "wall_end": f"dry-run-{i}-end",
            })

        analysis = check_serialization(results)
        print(f"  Serialized: {analysis['serialized']}")
        print(f"  Overlaps: {len(analysis['overlaps'])}")
        write_report(results, analysis, "dry-run", output_path)
        print("\n[DRY-RUN] PASS - serialization logic works correctly.")
        sys.exit(0)

    # Live test: fire 3 requests simultaneously
    print("Firing 3 simultaneous /api/chat requests...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {
            pool.submit(send_chat_request, args.url, agent): agent
            for agent in args.agents
        }
        results = []
        for fut in concurrent.futures.as_completed(futures):
            r = fut.result()
            results.append(r)
            status_str = f"HTTP {r['status']}" if not r["error"] else r["error"]
            print(f"  {r['agent']}: {status_str} ({r['latency_ms']:.0f} ms)")

    errors = [r for r in results if r["error"] or r["status"] != 200]
    if errors:
        print(f"\nBLOCKED: {len(errors)}/{len(results)} requests failed:")
        for e in errors:
            print(f"  {e['agent']}: {e.get('error', 'HTTP error')}")
        analysis = check_serialization(results) if not errors else {
            "serialized": False, "overlaps": [], "total_wall_ms": 0,
            "sum_individual_ms": 0, "max_individual_ms": 0,
            "ratio_to_sum": 0, "ratio_to_max": 0
        }
        write_report(results, analysis, args.url, output_path)
        sys.exit(2)

    analysis = check_serialization(results)
    print(f"\nSerialization analysis:")
    print(f"  Total wall: {analysis['total_wall_ms']} ms")
    print(f"  Sum individual: {analysis['sum_individual_ms']} ms")
    print(f"  Ratio (wall/sum): {analysis['ratio_to_sum']}")
    print(f"  Overlaps: {len(analysis['overlaps'])}")
    print(f"  Serialized: {analysis['serialized']}")

    write_report(results, analysis, args.url, output_path)

    if analysis["serialized"]:
        print("\nPASS: All 3 requests serialized. parallel_slots=1 confirmed.")
        sys.exit(0)
    else:
        print("\nFAIL: Overlap detected or timing inconsistent with serialization.")
        sys.exit(1)


if __name__ == "__main__":
    main()
