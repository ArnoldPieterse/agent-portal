#!/usr/bin/env python
"""
Goal #4 (Researcher, cycle-6) - Eviction-Awareness Rule unit test.

Encodes the documented Q4-evicts-Q8 asymmetry into a runnable check against
hot_load.restore_order(). Acceptance: for "Q8 was resident before a Q4 reload",
the restore order yields ZERO binding loss AND every residency change is logged
(never silent).

hot_load.py is __main__-guarded -> importing it is side-effect free (no live loads).
Run:  python memory/researcher/test_eviction_restore.py      # plain, exit 0 on pass
      pytest memory/researcher/test_eviction_restore.py       # same cases as test_ funcs
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import hot_load  # noqa: E402   (safe: __main__-guarded)


# --- Case 1 (acceptance): Q8 resident, we want dual residency after a Q4 reload.
# Loading quinn-q4 evicts atlas-q8 (documented asymmetry); restore_order must RELOAD
# atlas-q8 afterwards so the final set == target (zero loss) and log every change.
def test_dual_residency_preserved():
    order, log, zero_loss = hot_load.restore_order(
        "white", {"atlas-q8"}, {"quinn-q4", "atlas-q8"})
    assert zero_loss is True, f"binding loss: final != target; log={log}"
    assert ("LOAD", "quinn-q4") in order
    assert ("RELOAD", "atlas-q8") in order, "evicted wanted model was not restored"
    # RELOAD must come AFTER the LOAD that evicted it (restore-after-evict ordering).
    assert order.index(("LOAD", "quinn-q4")) < order.index(("RELOAD", "atlas-q8")), \
        "RELOAD of evicted model must follow the LOAD that caused the eviction"
    # residency change is logged, never silent
    assert any("EVICTED atlas-q8" in ln for ln in log), f"eviction not logged: {log}"
    assert any("RESTORED atlas-q8" in ln for ln in log), f"restore not logged: {log}"
    return order, log


# --- Case 2: a NON-target resident is dropped (UNLOADED + logged) and never
# pointlessly re-loaded when we only want the Q4. NOTE: restore_order pre-unloads all
# non-target residents in step 1, so the mid-load 'EVICTION ACCEPTED' branch is
# unreachable for this input (the model is gone before the LOAD runs). We assert the
# observable contract: no RELOAD of a non-target model + zero loss.
def test_non_target_resident_dropped_not_reloaded():
    order, log, zero_loss = hot_load.restore_order(
        "white", {"atlas-q8"}, {"quinn-q4"})
    assert zero_loss is True
    assert ("LOAD", "quinn-q4") in order
    assert ("RELOAD", "atlas-q8") not in order, "must NOT restore a non-target model"
    assert any("UNLOADED atlas-q8" in ln or "EVICTION ACCEPTED for atlas-q8" in ln
               for ln in log), f"drop not logged: {log}"


# --- Case 3: resident models we no longer want are UNLOADED (and logged) so the
# final set is exactly the target.
def test_unwanted_resident_unloaded_and_logged():
    order, log, zero_loss = hot_load.restore_order(
        "white", {"quinn-q4", "atlas-q8"}, {"quinn-q4"})
    assert zero_loss is True
    assert ("UNLOAD", "atlas-q8") in order
    assert any("UNLOADED atlas-q8" in ln for ln in log), f"not logged: {log}"


# --- Case 4 (sanity): host with no documented eviction edges never triggers a repair.
def test_host_without_edges_no_repair():
    order, log, zero_loss = hot_load.restore_order(
        "black", {"some-q8"}, {"some-q4", "some-q8"})
    assert zero_loss is True
    assert ("RELOAD", "some-q8") not in order


if __name__ == "__main__":
    failures = 0
    for fn in (test_dual_residency_preserved, test_non_target_resident_dropped_not_reloaded,
               test_unwanted_resident_unloaded_and_logged, test_host_without_edges_no_repair):
        try:
            out = fn()
            print(f"PASS {fn.__name__}  order={out[0] if isinstance(out, tuple) else ''}")
        except AssertionError as e:
            failures += 1
            print(f"FAIL {fn.__name__}: {e}")
    # echo the acceptance case's full log for the evidence record
    try:
        _, log = test_dual_residency_preserved()
        print("--- acceptance-case residency log (zero-loss, fully logged) ---")
        for ln in log:
            print("   ", ln)
    except Exception as e:  # noqa: BLE001
        failures += 1
        print(f"FAIL echo: {e}")
    sys.exit(1 if failures else 0)
