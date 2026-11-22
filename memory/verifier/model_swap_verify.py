#!/usr/bin/env python3
"""
model_swap_verify.py - Model Swap Verification Battery (Verifier goal #7)

After any model swap, runs a test battery:
  (a) agent responds to ping <10s
  (b) response quality check (not garbled)
  (c) tool calls work (if agent has tools)
  (d) context window is correct size

Acceptance criteria:
  * On correctly swapped model: all 4 checks pass
  * On failed swap (wrong model loaded): at least one check fails
  * Battery runs <60s total

Usage:
  python memory/verifier/model_swap_verify.py --self-test
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Simulated agent interface (pluggable for live testing)
# ---------------------------------------------------------------------------

class AgentSimulator:
    """Simulates agent responses post-swap. Can be configured good or bad."""

    def __init__(self, swap_success=True, tools=["python", "terminal"], context_window=128000):
        self.swap_success = swap_success
        self.tools = tools
        self.context_window = context_window

    def ping(self):
        """Simulate a ping request. Returns (response_text, latency_seconds)."""
        if not self.swap_success:
            # Failed swap: very slow or no response
            return None, 15.0  # timeout simulation
        return "pong", 0.3

    def respond(self, prompt):
        """Simulate a chat completion. Returns response text."""
        if not self.swap_success:
            return "\ufffd\ufffd\ufffd\x00\x01binary_garbage_\ufffd\x02"
        # Good model: coherent English response
        return f"I understand your request: {prompt}. Here is my analysis based on the available data. The key finding is that the system is operating within expected parameters and no anomalies were detected in the current observation window."

    def tool_call(self, tool_name, args):
        """Simulate a tool call. Returns (success: bool, result_text)."""
        if not self.swap_success:
            return False, "ERROR: tool registry empty - no tools loaded for this model"
        if tool_name not in self.tools:
            return False, f"Unknown tool: {tool_name}"
        # Simulate successful tool execution
        if tool_name == "python":
            return True, "print('hello') -> hello\n"
        elif tool_name == "terminal":
            return True, "dir /b -> file1.txt, file2.txt\n"
        return True, f"{tool_name} executed successfully"

    def get_context_window(self):
        """Return the actual context window size of the loaded model."""
        if not self.swap_success:
            return 4096  # wrong model with tiny context
        return self.context_window


# ---------------------------------------------------------------------------
# Battery checks
# ---------------------------------------------------------------------------

def check_ping(agent):
    """(a) Agent responds to ping in <10s."""
    t0 = time.time()
    response, latency = agent.ping()
    elapsed = time.time() - t0

    if response is None:
        return {
            "check": "ping_response",
            "passed": False,
            "detail": f"No response received (latency={latency:.1f}s > 10s timeout)"
        }
    passed = latency < 10.0
    return {
        "check": "ping_response",
        "passed": passed,
        "detail": f"Response '{response}' in {latency:.2f}s (threshold: 10s)",
        "latency_s": round(latency, 3)
    }


def check_quality(agent):
    """(b) Response is not garbled (coherent text, no null bytes / replacement chars)."""
    prompt = "What is the capital of France? Answer in one sentence."
    response = agent.respond(prompt)

    # Quality heuristics:
    has_null_bytes = b"\x00" in response.encode("utf-8", errors="replace")
    replacement_chars = response.count("\ufffd")
    has_words = len(re.findall(r"[a-zA-Z]{3,}", response)) >= 5
    non_printable_ratio = sum(1 for c in response if ord(c) < 32 and c not in "\n\t\r") / max(len(response), 1)

    passed = (not has_null_bytes) and (replacement_chars == 0) and has_words and (non_printable_ratio < 0.05)
    return {
        "check": "response_quality",
        "passed": passed,
        "detail": (
            f"null_bytes={has_null_bytes}, replacement_chars={replacement_chars}, "
            f"word_count={len(re.findall(r'[a-zA-Z]{3,}', response))}, "
            f"non_printable_ratio={non_printable_ratio:.3f}"
        ),
        "response_preview": response[:120]
    }


def check_tools(agent):
    """(c) Tool calls work if agent has tools defined."""
    if not agent.tools:
        return {
            "check": "tool_calls",
            "passed": True,
            "detail": "No tools defined - check N/A (pass by default)"
        }

    results = []
    all_passed = True
    for tool in agent.tools[:3]:  # test up to 3 tools
        success, result_text = agent.tool_call(tool, {})
        if not success:
            all_passed = False
        results.append({"tool": tool, "success": success, "result_preview": result_text[:80]})

    return {
        "check": "tool_calls",
        "passed": all_passed,
        "detail": f"{sum(1 for r in results if r['success'])}/{len(results)} tools responded correctly",
        "tools_tested": results
    }


def check_context(agent):
    """(d) Context window is the expected size (not a degraded/wrong model)."""
    actual = agent.get_context_window()
    expected = agent.context_window  # what we expect based on the target model spec

    # Allow 10% tolerance for rounding differences
    passed = abs(actual - expected) / max(expected, 1) < 0.10
    return {
        "check": "context_window",
        "passed": passed,
        "detail": f"Actual={actual}, expected={expected} (tolerance 10%)",
        "actual": actual,
        "expected": expected
    }


# ---------------------------------------------------------------------------
# Battery runner
# ---------------------------------------------------------------------------

def run_battery(agent):
    """Run all 4 checks. Returns report dict."""
    t0 = time.time()

    results = [
        check_ping(agent),
        check_quality(agent),
        check_tools(agent),
        check_context(agent),
    ]

    elapsed = time.time() - t0
    all_passed = all(r["passed"] for r in results)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "elapsed_s": round(elapsed, 3),
        "all_passed": all_passed,
        "checks_passed": sum(1 for r in results if r["passed"]),
        "checks_total": len(results),
        "checks": results
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def self_test():
    print("=" * 64)
    print("model_swap_verify.py - SELF-TEST")
    print("=" * 64)

    all_results = []

    # T1: Correct swap -> all 4 checks pass
    print("\n[T1] Correct model swap (all should pass)...")
    good_agent = AgentSimulator(swap_success=True, tools=["python", "terminal"], context_window=128000)
    r1 = run_battery(good_agent)
    t1_pass = r1["all_passed"] and r1["checks_passed"] == 4
    print(f"    {'PASS' if t1_pass else 'FAIL'} - {r1['checks_passed']}/4 checks, elapsed={r1['elapsed_s']}s")
    for c in r1["checks"]:
        mark = "+" if c["passed"] else "x"
        print(f"      [{mark}] {c['check']}: {c['detail']}")
    all_results.append(("T1_correct_swap_all_pass", t1_pass))

    # T2: Failed swap -> at least one check fails
    print("\n[T2] Failed model swap (at least 1 should fail)...")
    bad_agent = AgentSimulator(swap_success=False, tools=["python"], context_window=131072)
    r2 = run_battery(bad_agent)
    t2_pass = (not r2["all_passed"]) and r2["checks_passed"] < 4
    failed_checks = [c["check"] for c in r2["checks"] if not c["passed"]]
    print(f"    {'PASS' if t2_pass else 'FAIL'} - {r2['checks_passed']}/4 passed, failed: {failed_checks}")
    for c in r2["checks"]:
        mark = "+" if c["passed"] else "x"
        print(f"      [{mark}] {c['check']}: {c['detail']}")
    all_results.append(("T2_failed_swap_detection", t2_pass))

    # T3: Battery runs <60s
    print("\n[T3] Timing (<60s)...")
    t3_pass = r1["elapsed_s"] < 60 and r2["elapsed_s"] < 60
    print(f"    {'PASS' if t3_pass else 'FAIL'} - good={r1['elapsed_s']}s, bad={r2['elapsed_s']}s")
    all_results.append(("T3_timing_under_60s", t3_pass))

    # T4: Report structure is machine-readable JSON
    print("\n[T4] Report structure...")
    required = ["timestamp", "elapsed_s", "all_passed", "checks_passed", "checks_total", "checks"]
    t4_pass = all(f in r1 for f in required) and all(f in r2 for f in required)
    # Verify each check has 'check', 'passed', 'detail'
    check_fields_ok = all(all(k in c for k in ["check", "passed", "detail"]) for c in r1["checks"] + r2["checks"])
    t4_pass = t4_pass and check_fields_ok
    print(f"    {'PASS' if t4_pass else 'FAIL'}")
    all_results.append(("T4_report_structure", t4_pass))

    # Summary
    passed = sum(1 for _, p in all_results if p)
    total = len(all_results)
    print("\n" + "=" * 64)
    print(f"SUMMARY: {passed}/{total} self-tests passed")

    # Write report
    full_report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "self_test_results": [name for name, p in all_results if p],
        "failed_tests": [name for name, p in all_results if not p],
        "t1_good_swap": r1,
        "t2_bad_swap": r2,
        "all_pass": passed == total
    }
    out_path = "memory/verifier/model_swap_verify_report.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(full_report, f, indent=2)
    print(f"Report: {out_path}")

    all_pass = passed == total
    print(f"\nSELF-TEST {'PASSED' if all_pass else 'FAILED'} - {passed}/{total} tests green")
    return 0 if all_pass else 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Model Swap Verification Battery")
    parser.add_argument("--self-test", action="store_true", help="Run self-test with simulated agents")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(self_test())
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
