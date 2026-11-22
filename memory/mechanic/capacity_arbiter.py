"""Host Capacity Arbitration - Mechanic Goal #8 (Cycle 10).

When multiple agents request the same host's GPU simultaneously, arbitrate:
priority by (a) current task criticality, (b) time already waited, (c) predicted duration.
Queue lower-priority requests; notify requesting agent of estimated wait.

Usage:
    python memory/mechanic/capacity_arbiter.py --selftest   # run self-test battery
    python memory/mechanic/capacity_arbiter.py              # process pending requests (one pass)
"""

import json
import os
import sys
import time
import heapq
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# --- Configuration ---
ARBITRATION_LOG = Path("memory/ops/arbitration-log.jsonl")
REQUESTS_FILE = Path("memory/mechanic/gpu-requests.jsonl")

# Priority weights for scoring
W_CRITICALITY = 10.0   # weight for task criticality (higher = more urgent)
W_WAIT_TIME = 5.0      # weight for time already waited (seconds, normalized)
W_DURATION = 1.0       # weight for predicted duration (shorter = higher priority)


@dataclass
class GpuRequest:
    """A GPU resource request from an agent."""
    request_id: str
    agent_name: str
    host: str
    model: str
    criticality: int          # 1=low, 2=medium, 3=high, 4=critical
    requested_at: float       # unix timestamp
    predicted_duration_s: float  # estimated time needed
    status: str = "pending"   # pending | granted | queued | denied
    granted_at: Optional[float] = None
    wait_notification: Optional[str] = None


class CapacityArbiter:
    """Arbitrates GPU requests for a single host."""
    
    def __init__(self, host: str, max_concurrent: int = 1):
        self.host = host
        self.max_concurrent = max_concurrent
        self.active_requests: list = []  # currently granted
        self.queue: list = []            # waiting requests (priority queue)
        self.history: list = []          # completed/denied
    
    def _score(self, req: GpuRequest, now: float = None) -> float:
        """Calculate priority score. Higher score = higher priority."""
        if now is None:
            now = time.time()
        
        # (a) Criticality: 1-4, higher is more urgent
        crit_score = req.criticality * W_CRITICALITY
        
        # (b) Wait time: seconds waited, normalized to avoid dominating
        wait_s = max(0, now - req.requested_at)
        wait_score = min(wait_s / 60.0, 10.0) * W_WAIT_TIME  # cap at 10min contribution
        
        # (c) Predicted duration: shorter tasks get slight preference
        # Invert so shorter duration = higher score
        dur_score = max(0, (300.0 - req.predicted_duration_s) / 300.0) * W_DURATION
        
        return crit_score + wait_score + dur_score
    
    def submit(self, req: GpuRequest, now: float = None):
        """Submit a new request for arbitration."""
        if now is None:
            now = time.time()
        
        # Check if we can grant immediately
        if len(self.active_requests) < self.max_concurrent:
            req.status = "granted"
            req.granted_at = now
            self.active_requests.append(req)
            self._log_decision(req, action="grant", reason=f"capacity available ({len(self.active_requests)}/{self.max_concurrent})")
        else:
            # Queue it
            req.status = "queued"
            self.queue.append(req)
            
            # Calculate estimated wait for notification
            est_wait = self._estimate_wait(req, now)
            req.wait_notification = f"Estimated wait: {est_wait:.0f}s ({len(self.queue)} ahead in queue)"
            self._log_decision(req, action="queue", reason=f"host at capacity ({self.max_concurrent}/{self.max_concurrent}), est_wait={est_wait:.0f}s")
    
    def _estimate_wait(self, req: GpuRequest, now: float = None) -> float:
        """Estimate how long a request will wait in the queue."""
        if now is None:
            now = time.time()
        
        # Sum remaining durations of active requests + queued requests with higher priority
        total_wait = 0.0
        
        # Active requests' remaining time (approximate: use predicted duration)
        for active in self.active_requests:
            elapsed = now - active.granted_at if active.granted_at else 0
            remaining = max(0, active.predicted_duration_s - elapsed)
            total_wait += remaining
        
        # Queued requests with higher priority
        my_score = self._score(req, now)
        for queued in sorted(self.queue, key=lambda q: self._score(q, now), reverse=True):
            if queued.request_id == req.request_id:
                break
            if self._score(queued, now) > my_score:
                total_wait += queued.predicted_duration_s
        
        return total_wait
    
    def release(self, request_id: str, now: float = None):
        """Release a completed request and potentially promote from queue."""
        if now is None:
            now = time.time()
        
        # Find and remove the active request
        for i, req in enumerate(self.active_requests):
            if req.request_id == request_id:
                self.active_requests.pop(i)
                req.status = "completed"
                self.history.append(req)
                break
        
        # Promote from queue if capacity available
        self._promote(now)
    
    def _promote(self, now: float = None):
        """Promote highest-priority queued request if slot available."""
        if now is None:
            now = time.time()
        
        while len(self.active_requests) < self.max_concurrent and self.queue:
            # Find highest priority in queue
            best_idx = 0
            best_score = -1
            for i, req in enumerate(self.queue):
                score = self._score(req, now)
                if score > best_score:
                    best_score = score
                    best_idx = i
            
            promoted = self.queue.pop(best_idx)
            promoted.status = "granted"
            promoted.granted_at = now
            self.active_requests.append(promoted)
            self._log_decision(promoted, action="promote", reason=f"slot freed, promoted from queue (score={best_score:.1f})")
    
    def get_queue_status(self, agent_name: str = None) -> dict:
        """Get current queue status, optionally filtered by agent."""
        now = time.time()
        queued = []
        for req in self.queue:
            if agent_name and req.agent_name != agent_name:
                continue
            queued.append({
                "request_id": req.request_id,
                "agent": req.agent_name,
                "model": req.model,
                "criticality": req.criticality,
                "waited_s": round(now - req.requested_at, 1),
                "estimated_wait_s": round(self._estimate_wait(req, now), 1)
            })
        
        return {
            "host": self.host,
            "active_count": len(self.active_requests),
            "max_concurrent": self.max_concurrent,
            "queued_count": len(self.queue),
            "queue": sorted(queued, key=lambda x: x["waited_s"], reverse=True)
        }
    
    def _log_decision(self, req: GpuRequest, action: str, reason: str):
        """Log arbitration decision to JSONL."""
        ARBITRATION_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "host": self.host,
            "request_id": req.request_id,
            "agent": req.agent_name,
            "model": req.model,
            "action": action,
            "criticality": req.criticality,
            "reason": reason
        }
        with open(ARBITRATION_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")


def process_requests_file():
    """Process pending requests from the requests file (one pass)."""
    if not REQUESTS_FILE.exists():
        print("No pending requests file found.")
        return {"processed": 0}
    
    # Group by host
    hosts = {}
    with open(REQUESTS_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            host = data.get("host", "white")
            if host not in hosts:
                hosts[host] = CapacityArbiter(host=host, max_concurrent=data.get("max_concurrent", 1))
            
            req = GpuRequest(
                request_id=data["request_id"],
                agent_name=data["agent_name"],
                host=host,
                model=data.get("model", "unknown"),
                criticality=data.get("criticality", 2),
                requested_at=data.get("requested_at", time.time()),
                predicted_duration_s=data.get("predicted_duration_s", 60.0)
            )
            hosts[host].submit(req)
    
    # Report
    results = {}
    for host, arb in hosts.items():
        results[host] = arb.get_queue_status()
    
    print(json.dumps(results, indent=2))
    return {"processed": sum(len(a.queue) + len(a.active_requests) for a in hosts.values())}


# --- SELF-TEST ---
def selftest():
    """Run self-test battery. Returns (passed, total)."""
    results = []

    def check(name, condition):
        results.append((name, bool(condition)))
        status = "PASS" if condition else "FAIL"
        print(f"  [{status}] {name}")

    print("=== Capacity Arbiter Self-Test ===")
    
    now = time.time()

    # Test 1: Single request gets immediate grant
    arb = CapacityArbiter(host="test", max_concurrent=1)
    req1 = GpuRequest(
        request_id="r1", agent_name="agent_a", host="test",
        model="llama-7b", criticality=2, requested_at=now, predicted_duration_s=60
    )
    arb.submit(req1, now=now)
    check("single request granted immediately", req1.status == "granted")
    check("granted_at set", req1.granted_at is not None)

    # Test 2: Second request gets queued when host at capacity
    req2 = GpuRequest(
        request_id="r2", agent_name="agent_b", host="test",
        model="llama-13b", criticality=2, requested_at=now + 5, predicted_duration_s=120
    )
    arb.submit(req2, now=now + 5)
    check("second request queued", req2.status == "queued")
    check("wait notification set", req2.wait_notification is not None)
    check("wait notification has estimate", "Estimated wait" in req2.wait_notification)

    # Test 3: Higher criticality gets priority on promotion
    arb2 = CapacityArbiter(host="test2", max_concurrent=1)
    r_a = GpuRequest(request_id="ra", agent_name="low_crit", host="test2",
                     model="m1", criticality=1, requested_at=now, predicted_duration_s=60)
    r_b = GpuRequest(request_id="rb", agent_name="high_crit", host="test2",
                     model="m2", criticality=4, requested_at=now + 1, predicted_duration_s=30)
    arb2.submit(r_a, now=now)       # gets granted (only request)
    arb2.submit(r_b, now=now + 1)   # gets queued
    
    # Add a third lower-criticality request
    r_c = GpuRequest(request_id="rc", agent_name="med_crit", host="test2",
                     model="m3", criticality=2, requested_at=now + 2, predicted_duration_s=45)
    arb2.submit(r_c, now=now + 2)   # also queued
    
    check("high_crit queued (host at capacity)", r_b.status == "queued")
    check("med_crit queued", r_c.status == "queued")
    
    # Release first request - highest priority should be promoted
    arb2.release("ra", now=now + 10)
    check("after release, one active", len(arb2.active_requests) == 1)
    check("high_crit promoted (criticality=4)", arb2.active_requests[0].request_id == "rb")

    # Test 4: Wait time affects priority when criticality is equal
    arb3 = CapacityArbiter(host="test3", max_concurrent=1)
    r_x = GpuRequest(request_id="rx", agent_name="first", host="test3",
                     model="m", criticality=2, requested_at=now, predicted_duration_s=60)
    arb3.submit(r_x, now=now)  # granted
    
    # Two requests with same criticality but different wait times
    r_y = GpuRequest(request_id="ry", agent_name="waited_longer", host="test3",
                     model="m", criticality=2, requested_at=now + 10, predicted_duration_s=60)
    r_z = GpuRequest(request_id="rz", agent_name="waited_shorter", host="test3",
                     model="m", criticality=2, requested_at=now + 50, predicted_duration_s=60)
    arb3.submit(r_y, now=now + 10)  # queued, has been waiting 40s by now+50
    arb3.submit(r_z, now=now + 50)  # queued, just arrived
    
    # Release - the one that waited longer should be promoted
    arb3.release("rx", now=now + 60)
    check("longer-waiting request promoted first", arb3.active_requests[0].request_id == "ry")

    # Test 5: Shorter predicted duration gets slight preference (tiebreaker)
    arb4 = CapacityArbiter(host="test4", max_concurrent=1)
    r_p = GpuRequest(request_id="rp", agent_name="p", host="test4",
                     model="m", criticality=2, requested_at=now, predicted_duration_s=60)
    arb4.submit(r_p, now=now)
    
    # Same criticality, same request time, different duration
    r_q = GpuRequest(request_id="rq", agent_name="q_short", host="test4",
                     model="m", criticality=2, requested_at=now + 5, predicted_duration_s=10)
    r_r = GpuRequest(request_id="rr", agent_name="r_long", host="test4",
                     model="m", criticality=2, requested_at=now + 5, predicted_duration_s=300)
    arb4.submit(r_q, now=now + 5)
    arb4.submit(r_r, now=now + 5)
    
    # Both queued - scores should favor shorter duration
    score_q = arb4._score(r_q, now=now + 5)
    score_r = arb4._score(r_r, now=now + 5)
    check("shorter duration gets higher score", score_q > score_r)

    # Test 6: No request lost - all eventually served
    arb5 = CapacityArbiter(host="test5", max_concurrent=1)
    requests_5 = []
    for i in range(5):
        req = GpuRequest(
            request_id=f"r5_{i}", agent_name=f"agent_{i}", host="test5",
            model="m", criticality=2 + (i % 3), requested_at=now + i*10,
            predicted_duration_s=30
        )
        arb5.submit(req, now=now + i*10)
        requests_5.append(req)
    
    # Release all one by one - verify all get served
    served = set()
    current_active = list(arb5.active_requests)
    for req in current_active:
        served.add(req.request_id)
        arb5.release(req.request_id, now=now + 100)
    
    # After first release, one should be promoted
    if arb5.active_requests:
        next_req = arb5.active_requests[0]
        served.add(next_req.request_id)
        arb5.release(next_req.request_id, now=now + 200)
    
    # Continue until all served or queue empty
    while arb5.active_requests:
        req = arb5.active_requests[0]
        served.add(req.request_id)
        arb5.release(req.request_id, now=time.time() + 1000)
    
    check("no request lost (all eventually served)", len(served) == 5)

    # Test 7: Queue status report
    status = arb.get_queue_status()
    check("queue status has host", status["host"] == "test")
    check("queue status has active_count", "active_count" in status)
    check("queue status has queued_count", "queued_count" in status)
    check("queue status has queue list", isinstance(status["queue"], list))

    # Test 8: Filtered queue status by agent
    filtered = arb.get_queue_status(agent_name="agent_b")
    check("filtered status only shows agent_b", all(q["agent"] == "agent_b" for q in filtered["queue"]))

    # Test 9: Arbitration log written
    check("arbitration-log.jsonl exists", ARBITRATION_LOG.exists())
    if ARBITRATION_LOG.exists():
        lines = ARBITRATION_LOG.read_text().strip().split("\n")
        check(f"arbitration log has entries ({len(lines)})", len(lines) >= 3)
        entry = json.loads(lines[0])
        check("log entry has required fields", all(k in entry for k in ("timestamp", "host", "request_id", "agent", "action")))

    # Test 10: Log actions are valid
    if ARBITRATION_LOG.exists():
        lines = ARBITRATION_LOG.read_text().strip().split("\n")
        actions = set()
        for line in lines:
            e = json.loads(line)
            actions.add(e["action"])
        check("log contains grant action", "grant" in actions)
        check("log contains queue action", "queue" in actions)

    # Test 11: Score calculation is deterministic
    arb6 = CapacityArbiter(host="det", max_concurrent=1)
    req_det = GpuRequest(request_id="det1", agent_name="a", host="det",
                         model="m", criticality=3, requested_at=now, predicted_duration_s=50)
    s1 = arb6._score(req_det, now=now + 100)
    s2 = arb6._score(req_det, now=now + 100)
    check("score is deterministic", s1 == s2)

    # Test 12: Score increases with wait time
    s_early = arb6._score(req_det, now=now + 10)
    s_late = arb6._score(req_det, now=now + 300)
    check("score increases with wait time", s_late > s_early)

    # Test 13: Multiple concurrent slots work
    arb7 = CapacityArbiter(host="multi", max_concurrent=2)
    r_m1 = GpuRequest(request_id="m1", agent_name="a", host="multi",
                      model="m", criticality=2, requested_at=now, predicted_duration_s=30)
    r_m2 = GpuRequest(request_id="m2", agent_name="b", host="multi",
                      model="m", criticality=2, requested_at=now+1, predicted_duration_s=30)
    r_m3 = GpuRequest(request_id="m3", agent_name="c", host="multi",
                      model="m", criticality=2, requested_at=now+2, predicted_duration_s=30)
    arb7.submit(r_m1, now=now)
    arb7.submit(r_m2, now=now+1)
    arb7.submit(r_m3, now=now+2)
    check("2 concurrent: first 2 granted", r_m1.status == "granted" and r_m2.status == "granted")
    check("2 concurrent: 3rd queued", r_m3.status == "queued")

    # Test 14: Release promotes from queue in multi-slot
    arb7.release("m1", now=now+60)
    check("after release in multi, 3rd promoted", r_m3.status == "granted")

    # Test 15: Empty queue status
    arb_empty = CapacityArbiter(host="empty", max_concurrent=1)
    st = arb_empty.get_queue_status()
    check("empty arbiter: 0 active, 0 queued", st["active_count"] == 0 and st["queued_count"] == 0)

    # Test 16: Wait notification format
    if req2.wait_notification:
        check("wait notification has seconds", "s" in req2.wait_notification)
        check("wait notification mentions position", "ahead" in req2.wait_notification or "wait" in req2.wait_notification.lower())

    # Test 17: Criticality ordering (4 > 3 > 2 > 1)
    arb8 = CapacityArbiter(host="crit_test", max_concurrent=1)
    r_crit1 = GpuRequest(request_id="c1", agent_name="a", host="crit_test",
                         model="m", criticality=1, requested_at=now, predicted_duration_s=60)
    arb8.submit(r_crit1, now=now)  # granted
    
    r_crit4 = GpuRequest(request_id="c4", agent_name="b", host="crit_test",
                         model="m", criticality=4, requested_at=now+1, predicted_duration_s=60)
    r_crit2 = GpuRequest(request_id="c2", agent_name="c", host="crit_test",
                         model="m", criticality=2, requested_at=now+1, predicted_duration_s=60)
    arb8.submit(r_crit4, now=now+1)  # queued
    arb8.submit(r_crit2, now=now+1)  # queued
    
    arb8.release("c1", now=now+5)
    check("criticality 4 promoted before 2", arb8.active_requests[0].request_id == "c4")

    # Test 18: GpuRequest dataclass fields
    check("GpuRequest has all required fields", 
          hasattr(req1, 'request_id') and hasattr(req1, 'agent_name') and 
          hasattr(req1, 'host') and hasattr(req1, 'model') and 
          hasattr(req1, 'criticality') and hasattr(req1, 'status'))

    # Test 19: History tracks completed requests
    check("history records completed", len(arb2.history) >= 1)

    # Test 20: End-to-end: submit -> queue -> release -> promote -> complete
    arb_e2e = CapacityArbiter(host="e2e", max_concurrent=1)
    e1 = GpuRequest(request_id="e1", agent_name="a", host="e2e", model="m", criticality=3, requested_at=now, predicted_duration_s=30)
    e2 = GpuRequest(request_id="e2", agent_name="b", host="e2e", model="m", criticality=2, requested_at=now+5, predicted_duration_s=45)
    
    arb_e2e.submit(e1, now=now)
    check("e2e: first granted", e1.status == "granted")
    arb_e2e.submit(e2, now=now+5)
    check("e2e: second queued", e2.status == "queued")
    arb_e2e.release("e1", now=now+35)
    check("e2e: second promoted after release", e2.status == "granted")
    arb_e2e.release("e2", now=now+80)
    check("e2e: all complete, empty queue", len(arb_e2e.queue) == 0 and len(arb_e2e.active_requests) == 0)

    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"\n=== RESULT: {passed}/{total} PASS ===")
    return passed, total


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        p, t = selftest()
        sys.exit(0 if p == t else 1)
    else:
        process_requests_file()
