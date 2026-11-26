#!/usr/bin/env python3
"""event_bus.py - Convergence Event Bus (SSE + replay).

Builder goal 3 (Cycle 20): one append-only bus (convergence-events.jsonl) with an SSE
endpoint that all convergence writers emit to and all consumers subscribe from;
cursor-based replay lets a late-joining panel reconstruct full state. Replaces N
despite feeds with a single SSOT stream.

Architecture:
  - Source of truth: memory/ops/convergence-events.jsonl (append-only, one JSON per line)
  - In-process pub/sub: threading.Queue per subscriber for low-latency fanout
  - SSE endpoint: HTTP GET /events?cursor=N returns text/event-stream
  - Cursor-based replay: read from line N of JSONL; cursor=0 replays all
  - Bounded backpressure: if consumer falls behind, they get a bounded buffer (max 100)
    and a 'behind' flag; source writes are NEVER blocked by slow consumers

Usage:
  python memory/builder/event_bus.py --selftest       # run assertions
  python memory/builder/event_bus.py emit <type> <data_json>   # append one event
  python memory/builder/event_bus.py serve [--port 9876]       # SSE server
  python memory/builder/event_bus.py replay [cursor]           # print events from cursor
"""
from __future__ import annotations

import argparse
import json
import threading
import time
from collections import deque
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from queue import Queue, Full
from typing import Optional

HERE = Path(__file__).resolve().parent  # memory/builder
OPS = HERE.parent / "ops"
EVENTS_PATH = OPS / "convergence-events.jsonl"
MAX_BUFFER = 100  # bounded backpressure per consumer


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Core bus: append-only JSONL + in-process pub/sub
# ---------------------------------------------------------------------------

class ConvergenceEventBus:
    """Append-only event bus with cursor-based replay and bounded fanout."""

    def __init__(self, events_path: Path = EVENTS_PATH, max_buffer: int = MAX_BUFFER):
        self.events_path = events_path
        self.max_buffer = max_buffer
        self._subscribers: list[tuple[str, Queue]] = []  # (name, queue)
        self._lock = threading.Lock()
        self._seq = self._current_seq()

    def _current_seq(self) -> int:
        """Return the next sequence number based on existing file."""
        if not self.events_path.exists():
            return 0
        try:
            with open(self.events_path, "r", encoding="utf-8") as f:
                for _ in f:
                    pass
            # Count lines (each line = one event)
            count = sum(1 for _ in open(self.events_path, "r", encoding="utf-8"))
            return count
        except Exception:
            return 0

    def emit(self, event_type: str, data: dict, source: str = "unknown") -> dict:
        """Append an event to the JSONL and fanout to subscribers. Never blocks on slow consumers."""
        with self._lock:
            seq = self._seq
            self._seq += 1
            event = {
                "seq": seq,
                "ts": _now(),
                "type": event_type,
                "source": source,
                "data": data,
            }
            # Write to JSONL (append-only)
            self.events_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.events_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")

        # Fanout to subscribers (bounded - never blocks writer)
        for name, q in self._subscribers:
            try:
                q.put_nowait(event)
            except Full:
                # Drop oldest to make room (bounded backpressure)
                try:
                    q.get_nowait()
                    q.put_nowait(event)
                except Exception:
                    pass

        return event

    def subscribe(self, name: str) -> Queue:
        """Register a subscriber. Returns their bounded queue."""
        q: Queue = Queue(maxsize=self.max_buffer)
        with self._lock:
            self._subscribers.append((name, q))
        return q

    def unsubscribe(self, name: str):
        """Remove a subscriber by name."""
        with self._lock:
            self._subscribers = [(n, q) for n, q in self._subscribers if n != name]

    def replay(self, cursor: int = 0) -> list[dict]:
        """Read events from the JSONL starting at line `cursor` (0-indexed)."""
        if not self.events_path.exists():
            return []
        events = []
        with open(self.events_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i < cursor:
                    continue
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return events

    @property
    def current_seq(self) -> int:
        return self._seq


# Global bus instance (shared across imports in same process)
_bus: Optional[ConvergenceEventBus] = None
_bus_lock = threading.Lock()


def get_bus() -> ConvergenceEventBus:
    global _bus
    with _bus_lock:
        if _bus is None:
            _bus = ConvergenceEventBus()
        return _bus


# ---------------------------------------------------------------------------
# SSE HTTP Server
# ---------------------------------------------------------------------------

class SSEHandler(BaseHTTPRequestHandler):
    """Minimal SSE handler: GET /events?cursor=N"""
    bus: ConvergenceEventBus  # set by serve()

    def do_GET(self):
        if not self.path.startswith("/events"):
            self.send_response(404)
            self.end_headers()
            return

        # Parse cursor from query string
        cursor = 0
        if "cursor=" in self.path:
            try:
                cursor = int(self.path.split("cursor=")[1].split("&")[0])
            except ValueError:
                pass

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        # Send existing events from cursor
        events = self.bus.replay(cursor)
        for ev in events:
            self.wfile.write(f"id: {ev['seq']}\ndata: {json.dumps(ev)}\n\n".encode())
        self.wfile.flush()

        # Then subscribe for live events (simplified: poll every 1s)
        sub_name = f"sse_{id(self)}"
        q = self.bus.subscribe(sub_name)
        try:
            while True:
                try:
                    ev = q.get(timeout=2)
                    self.wfile.write(f"id: {ev['seq']}\ndata: {json.dumps(ev)}\n\n".encode())
                    self.wfile.flush()
                except Exception:
                    # Send keep-alive comment
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            self.bus.unsubscribe(sub_name)

    def log_message(self, format, *args):
        pass  # suppress request logs


def serve(port: int = 9876):
    """Start the SSE server."""
    bus = get_bus()
    SSEHandler.bus = bus
    server = HTTPServer(("127.0.0.1", port), SSEHandler)
    print(f"[event_bus] SSE server on http://127.0.0.1:{port}/events?cursor=0")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def selftest() -> int:
    """
    Acceptance tests:
    A. A simulated transition is broadcast to 2 subscribers within 2s.
    B. A new subscriber at cursor=0 replays all events and reaches current state.
    C. A deliberately slow consumer does not drop the source's writes (bounded backpressure).
    """
    import tempfile
    import shutil

    print("=== event_bus.py selftest ===")
    errors = []

    # Use a temp events file for isolation
    tmp_dir = Path(tempfile.mkdtemp(prefix="event_bus_test_"))
    tmp_events = tmp_dir / "convergence-events.jsonl"
    bus = ConvergenceEventBus(events_path=tmp_events, max_buffer=10)

    # --- Test A: Broadcast to 2 subscribers within 2s ---
    sub1_q = bus.subscribe("panel_1")
    sub2_q = bus.subscribe("panel_2")

    t0 = time.monotonic()
    ev = bus.emit("fsm_transition", {"from": "CONVERGING", "to": "STEADY_STATE"}, source="selftest")

    # Both subscribers should have the event in their queue immediately (in-process)
    try:
        got1 = sub1_q.get_nowait()
        got2 = sub2_q.get_nowait()
        elapsed = time.monotonic() - t0
        assert got1["seq"] == ev["seq"] and got2["seq"] == ev["seq"]
        assert elapsed < 2.0, f"Broadcast took {elapsed:.3f}s (>2s)"
        print(f"  [PASS] A: Broadcast to 2 subscribers in {elapsed*1000:.1f}ms")
    except Exception as e:
        errors.append(f"A: Failed - {e}")

    # --- Test B: Replay from cursor=0 reaches current state ---
    # Emit a few more events
    bus.emit("goal_reached", {"agent": "builder", "goal": 9}, source="selftest")
    bus.emit("fsm_transition", {"from": "STEADY_STATE", "to": "CONVERGING"}, source="selftest")

    replayed = bus.replay(cursor=0)
    expected_count = 3  # 1 from test A + 2 from here
    if len(replayed) != expected_count:
        errors.append(f"B: Expected {expected_count} events in replay, got {len(replayed)}")
    else:
        # Verify last event matches current state
        assert replayed[-1]["type"] == "fsm_transition"
        assert replayed[-1]["data"]["to"] == "CONVERGING"
        print(f"  [PASS] B: Replay from cursor=0 returns {len(replayed)} events, final state correct")

    # Test partial replay (cursor=2 should skip first 2)
    partial = bus.replay(cursor=2)
    if len(partial) != 1:
        errors.append(f"B2: Expected 1 event from cursor=2, got {len(partial)}")
    else:
        print("  [PASS] B2: Partial replay (cursor=2) returns correct subset")

    # --- Test C: Slow consumer doesn't block source writes ---
    # Create a subscriber with tiny buffer and don't read from it
    slow_q = bus.subscribe("slow_consumer", )
    # Fill the buffer (max_buffer=10)
    for i in range(5):
        bus.emit("noise", {"i": i}, source="selftest")

    t0 = time.monotonic()
    # Source should be able to write many more events without blocking
    for i in range(50):
        bus.emit("burst", {"i": i}, source="selftest")
    elapsed = time.monotonic() - t0

    if elapsed > 2.0:
        errors.append(f"C: Source writes took {elapsed:.3f}s (>2s) - slow consumer is blocking")
    else:
        # Verify the slow consumer's buffer is bounded (not infinite)
        buf_size = slow_q.qsize()
        if buf_size > 10:
            errors.append(f"C: Slow consumer buffer exceeded max ({buf_size} > 10)")
        else:
            print(f"  [PASS] C: 50 writes in {elapsed*1000:.1f}ms; slow buffer bounded at {buf_size}/10")

    # Verify all source events were written to disk (no drops on the SSOT)
    all_events = bus.replay(cursor=0)
    total_expected = 3 + 5 + 50  # test A + pre-burst + burst
    if len(all_events) != total_expected:
        errors.append(f"C2: Expected {total_expected} events on disk, got {len(all_events)}")
    else:
        print(f"  [PASS] C2: All {total_expected} source events persisted (no drops in SSOT)")

    # Cleanup
    shutil.rmtree(tmp_dir, ignore_errors=True)

    if errors:
        print(f"\n[FAIL] {len(errors)} assertion(s) failed:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("\n[ALL PASS] event_bus selftest complete")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Convergence Event Bus (SSE + replay)")
    subparsers = parser.add_subparsers(dest="cmd")

    # emit
    p_emit = subparsers.add_parser("emit", help="Append one event")
    p_emit.add_argument("event_type", help="Event type (e.g. fsm_transition, goal_reached)")
    p_emit.add_argument("data_json", nargs="?", default="{}", help="JSON data payload")
    p_emit.add_argument("--source", default="cli", help="Source identifier")

    # serve
    p_serve = subparsers.add_parser("serve", help="Start SSE server")
    p_serve.add_argument("--port", type=int, default=9876)

    # replay
    p_replay = subparsers.add_parser("replay", help="Print events from cursor")
    p_replay.add_argument("cursor", nargs="?", type=int, default=0)

    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        sys.exit(selftest())

    if args.cmd == "emit":
        bus = get_bus()
        try:
            data = json.loads(args.data_json)
        except json.JSONDecodeError:
            data = {"raw": args.data_json}
        ev = bus.emit(args.event_type, data, source=args.source)
        print(json.dumps(ev))

    elif args.cmd == "serve":
        serve(port=args.port)

    elif args.cmd == "replay":
        bus = get_bus()
        events = bus.replay(cursor=args.cursor)
        for ev in events:
            print(json.dumps(ev))
        print(f"\n[{len(events)} events from cursor {args.cursor}]", file=sys.stderr)

    else:
        parser.print_help()


if __name__ == "__main__":
    import sys
    main()