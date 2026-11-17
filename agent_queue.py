# RUN QUEUE (2026-11-17) - starnet-style durable pending-run queue + backpressure telemetry.
#
# Semantics ported from androoAGI/starnet (sidecar_loopjob*.js, shared/events.js):
#   * FIFO, capped (QUEUE_CAP default 5, min 1, max 12 - starnet's own bounds)
#   * workitem.placed: enqueue returns position + depth; the caller is told WHERE it sits
#   * queue.status: {depth, maxCapacity, deferred, items[]} for the backpressure HUD
#   * 'at-capacity' deferral is EXPLICIT (deferred counter) - starnet's NS-0 fix:
#     the old silent concurrency-cap deferral is never repeated here
#   * durable journal with atomic tmp+replace (same idiom as run_state.json), so a
#     restart does not drop queued work; recover() reports what survived on boot
#
# This module is deliberately dependency-free and thread-safe; agent_portal.py owns
# the pump (starting the next run) so queue state never decides scheduling by itself.

import json, os, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
QUEUE_FILE = os.path.join(HERE, "run_queue.json")

QUEUE_CAP_DEFAULT = 5    # pending runs allowed before 'at-capacity' deferral
QUEUE_CAP_MIN = 1        # 1 = strictly blocking (one queued behind the live run)
QUEUE_CAP_MAX = 12

_lock = threading.Lock()


def cap():
    """Effective queue capacity (bounded to starnet's min/max)."""
    c = int(QUEUE_CAP_DEFAULT)
    return max(QUEUE_CAP_MIN, min(QUEUE_CAP_MAX, c))


def _load():
    try:
        with open(QUEUE_FILE, encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict) and isinstance(d.get("items"), list):
            return d
    except Exception:
        pass
    return {"items": [], "deferred": 0}


def _save(d):
    tmp = QUEUE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f)
    os.replace(tmp, QUEUE_FILE)   # atomic: a crash never leaves a torn journal


def enqueue(text, extra=None):
    """workitem.placed. Returns (workitem, None) or (None, 'at-capacity').
    workitem = {id, position, depth, maxCapacity} - the caller's queue receipt."""
    with _lock:
        d = _load()
        if len(d["items"]) >= cap():
            d["deferred"] = int(d.get("deferred", 0)) + 1   # EXPLICIT at-capacity deferral
            _save(d)
            return None, "at-capacity"
        wid = "q-%x-%s" % (int(time.time() * 1000), os.urandom(3).hex())
        d["items"].append({"id": wid, "text": text or "", "extra": extra or {},
                           "placed_at": time.strftime("%Y-%m-%d %H:%M:%S")})
        _save(d)
        return {"id": wid, "position": len(d["items"]), "depth": len(d["items"]),
                "maxCapacity": cap()}, None


def pop_next():
    """Dequeue the oldest pending run (workitem.delivered). Returns item or None."""
    with _lock:
        d = _load()
        if not d["items"]:
            return None
        it = d["items"].pop(0)
        _save(d)
        return it


def status():
    """queue.status for the backpressure HUD (merged into GET /api/run-state)."""
    with _lock:
        d = _load()
        items = d["items"]
        return {
            "queue_depth": len(items),
            "queue_maxCapacity": cap(),
            "queue_deferred": int(d.get("deferred", 0)),
            # starnet emits nextAdvanceAt; for us the advance happens as soon as the
            # live run ends, so report that fact instead of a guessed timestamp.
            "queue_nextAdvanceAt": None,
            "queue_items": [{"id": it["id"], "position": i + 1, "placed_at": it.get("placed_at"),
                             "preview": (it.get("text") or "")[:80]}
                            for i, it in enumerate(items)],
        }


def recover():
    """Boot-time (starnet recover() idiom): the journal IS the queue, so pending runs
    already survived the restart. Just report them; the portal's pump advances them."""
    with _lock:
        d = _load()
        n = len(d["items"])
    if n:
        print("[run-queue] recovered %d pending run(s) from journal" % n, flush=True)
    return n
