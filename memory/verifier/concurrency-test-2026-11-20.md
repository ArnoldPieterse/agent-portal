# Concurrency Verification (cycle-8 goal #5) - STATIC leg

Generated: 2026-11-20 23:49:13
Source: agent_portal.py (4763 lines)

## Invariant under test
Docstring (agent_portal.py L2528): "Concurrency is safe: ... no lock is ever held across a generation."
We structurally verify that NO `with <lock>:` block contains a model-generation call.

## Lock definitions found
- `_lock` -> threading.RLock  (L639)
- `_journal_lock` -> threading.Lock  (L2350)
- `_umq_lock` -> threading.Lock  (L1547)
- `_history_lock` -> threading.Lock  (L2349)
- `_act_lock` -> threading.Lock  (L659)
- `_fleet_lock` -> threading.Lock  (L856)
- `_group_run_lock` -> threading.Lock  (L2348)
- `_autoloop_lock` -> threading.Lock  (L3033)

## Lock-hold blocks scanned: 25
- L673 `with _act_lock:` -> body holds NO generation call  [OK]
- L917 `with _fleet_lock:` -> body holds NO generation call  [OK]
- L922 `with _fleet_lock:` -> body holds NO generation call  [OK]
- L947 `with _fleet_lock:` -> body holds NO generation call  [OK]
- L1320 `with _lock:` -> body holds NO generation call  [OK]
- L1340 `with _lock:` -> body holds NO generation call  [OK]
- L1346 `with _lock:` -> body holds NO generation call  [OK]
- L1574 `with _umq_lock:` -> body holds NO generation call  [OK]
- L1589 `with _umq_lock:` -> body holds NO generation call  [OK]
- L1605 `with _umq_lock:` -> body holds NO generation call  [OK]
- L1628 `with _umq_lock:` -> body holds NO generation call  [OK]
- L1695 `with _lock:` -> body holds NO generation call  [OK]
- L1737 `with _lock:` -> body holds NO generation call  [OK]
- L1766 `with _lock:` -> body holds NO generation call  [OK]
- L1779 `with _lock:` -> body holds NO generation call  [OK]
- L2004 `with _lock:` -> body holds NO generation call  [OK]
- L2017 `with _lock:` -> body holds NO generation call  [OK]
- L2392 `with _history_lock:` -> body holds NO generation call  [OK]
- L2400 `with _journal_lock:` -> body holds NO generation call  [OK]
- L2806 `with _group_run_lock:` -> body holds NO generation call  [OK]
- L3062 `with _autoloop_lock:` -> body holds NO generation call  [OK]
- L3071 `with _autoloop_lock:` -> body holds NO generation call  [OK]
- L3144 `with _autoloop_lock:` -> body holds NO generation call  [OK]
- L3179 `with _autoloop_lock:` -> body holds NO generation call  [OK]
- L3332 `with _autoloop_lock:` -> body holds NO generation call  [OK]

## Violations: 0 - every lock-hold is a short critical section

## Parallel execution topology
- L9: from concurrent.futures import ThreadPoolExecutor, as_completed
- L931: with ThreadPoolExecutor(max_workers=max(1, len(order))) as ex:
- L2555: from concurrent.futures import ThreadPoolExecutor
- L2556: with ThreadPoolExecutor(max_workers=max(1, len(names))) as pool:
- Design: one worker thread per agent; DIFFERENT Studio hosts truly overlap;
  the local pair is serialized by White's Studio internally (parallel_slots=1).

## parallel_slots references
- L2525: internally (parallel_slots=1) and simply start a beat apart - harmless. Bubbles

## Live leg (NOT run here - wall-blocked)
3 simultaneous /api/chat -> confirm serialization in logs. Requires :8099 egress;
sandbox seat returns WinError 10013 (see memory/ops/blockers.md, Verifier #4).
Deferred to a non-sandbox White seat - do NOT re-probe from here.

## STATIC RESULT: PASS
- 0 locks held across a generation: YES
- invariant holds by construction: YES
