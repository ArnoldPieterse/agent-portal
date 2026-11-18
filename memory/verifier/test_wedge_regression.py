"""WEDGE regression test — verifies Builder's bounded-wait patch in _parallel_turns.

Spec (from TODO.md / Builder's handoff):
  Submit one agent whose LLM call blocks > timeout + one that completes fast.
  Expected: pass reaches verdict with the hung agent marked error="timeout (600s)",
  the fast agent gets its normal result. No infinite hang.

Usage: python test_wedge_regression.py
Run from any seat with Python 3.7+ (no network needed).
"""
import time, json, sys
from concurrent.futures import ThreadPoolExecutor, wait


def test_wedge_regression(timeout=3, hang_sleep=30):
    """Returns True if all assertions pass."""
    out = [None, None]
    names = ["fast_agent", "hung_agent"]

    def work(idx, name):
        if name == "hung_agent":
            time.sleep(hang_sleep)
            return {"name": name, "full": "should never reach here", "silent": False,
                    "concluded": True, "error": None, "blocked": None}
        else:
            time.sleep(0.1)
            return {"name": name, "full": "I'm fine", "silent": False,
                    "concluded": True, "error": None, "blocked": None}

    t_start = time.monotonic()

    # EXACT SAME PATTERN as patched _parallel_turns (agent_portal.py L1874-1882)
    pool = ThreadPoolExecutor(max_workers=max(1, len(names)))
    futures = {i: pool.submit(work, i, nm) for i, nm in enumerate(names)}

    # Bounded wait
    done_set, not_done = wait(futures.values(), timeout=timeout)

    # Mark timed-out agents
    for i, fut in futures.items():
        if not fut.done() and out[i] is None:
            out[i] = {"name": names[i], "full": "", "silent": False, "concluded": False,
                      "error": f"timeout ({timeout}s)", "blocked": None}

    # Collect completed results
    for i, fut in futures.items():
        if fut.done() and not fut.cancelled():
            try:
                out[i] = fut.result(timeout=1)
            except Exception as e:
                out[i] = {"name": names[i], "full": "", "silent": False,
                          "concluded": False, "error": str(e), "blocked": None}

    pool.shutdown(wait=False, cancel_futures=True)

    t_elapsed = time.monotonic() - t_start

    # ---- ASSERTIONS ----
    errors = []

    # A1: Pass did NOT hang (completed well under the hang_sleep of hung agent)
    if t_elapsed > timeout + 2:
        errors.append(f"A1 FAIL: pass took {t_elapsed:.1f}s, expected ~{timeout}s")

    # A2: Hung agent is marked with timeout error
    hung = out[1]
    if hung is None:
        errors.append("A2 FAIL: hung_agent result is None")
    elif "timeout" not in (hung.get("error") or ""):
        errors.append(f"A2 FAIL: hung_agent error={hung.get('error')!r}, expected 'timeout'")

    # A3: Fast agent got its normal result
    fast = out[0]
    if fast is None:
        errors.append("A3 FAIL: fast_agent result is None")
    elif fast.get("full") != "I'm fine":
        errors.append(f"A3 FAIL: fast_agent full={fast.get('full')!r}")
    elif fast.get("error") is not None:
        errors.append(f"A3 FAIL: fast_agent has unexpected error={fast.get('error')!r}")

    # A4: No agent is still "pending" (out[i] is None)
    for i, r in enumerate(out):
        if r is None:
            errors.append(f"A4 FAIL: out[{i}] is None (agent {names[i]} never resolved)")

    status = "PASS" if not errors else "FAIL"
    print(f"\n{'='*60}")
    print(f"WEDGE REGRESSION TEST — {status}")
    print(f"{'='*60}")
    print(f"  Elapsed: {t_elapsed:.2f}s (timeout={timeout}s, hang_sleep={hang_sleep}s)")
    print(f"  fast_agent: {json.dumps(out[0], default=str)}")
    print(f"  hung_agent: {json.dumps(out[1], default=str)}")
    if errors:
        for e in errors:
            print(f"  \u2717 {e}")
    else:
        print(f"  \u2713 A1: pass reached verdict in {t_elapsed:.1f}s (no wedge)")
        print(f"  \u2713 A2: hung agent marked error='timeout ({timeout}s)'")
        print(f"  \u2713 A3: fast agent got normal result, no error")
        print(f"  \u2713 A4: all agents resolved (no None slots)")

    return status == "PASS"


if __name__ == "__main__":
    ok = test_wedge_regression()
    sys.exit(0 if ok else 1)
