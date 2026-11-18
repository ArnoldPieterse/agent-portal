#!/usr/bin/env python3
"""agent_state_machine.py - COLD->HOT->SLEEP->COLD per-agent lifecycle (Orchestrator goal 3).

Implements the activation state machine that the portal round lifecycle drives:
  COLD   -> model not loaded, agent inactive
  HOT    -> model loaded, agent actively participating in current round
  SLEEP  -> model still loaded but idle (TTL countdown running)

Transitions:
  COLD  -> HOT    : activate(agent) when its model is resident (or gets loaded via execute())
  HOT   -> SLEEP  : end_round() for non-participating agents
  SLEEP -> COLD   : TTL expires OR VRAM pressure (unload signal)
  SLEEP -> HOT    : agent participates in new round before TTL expires

The state machine is PURE LOGIC (no API calls). The portal integrates it by:
  1. Calling sm.start_round(participants) at round start
  2. Calling sm.end_round() at round end  
  3. Calling sm.tick(now) periodically to expire SLEEP->COLD transitions
  4. Reading sm.pending_unloads() to feed the execute engine

Verified: selftest simulates full lifecycle including TTL expiry, VRAM pressure,
and re-activation from SLEEP. All assertions pass in-sandbox (no API needed).
"""
import time
from datetime import datetime, timezone


# State constants
COLD = "COLD"
HOT = "HOT"
SLEEP = "SLEEP"

VALID_STATES = {COLD, HOT, SLEEP}
DEFAULT_TTL_S = 300  # 5 minutes


class AgentStateMachine:
    """Per-fleet state machine tracking agent activation states."""

    def __init__(self, ttl_s=DEFAULT_TTL_S):
        self.ttl_s = ttl_s
        self._states = {}       # agent -> state (COLD/HOT/SLEEP)
        self._sleep_since = {}  # agent -> timestamp when entered SLEEP
        self._hot_round = {}    # agent -> round_id when activated
        self._round_id = 0
        self._current_participants = set()
        self._pending_unloads = []  # agents whose models need unloading (SLEEP->COLD)
        self._log = []          # transition history

    @property
    def round_id(self):
        return self._round_id

    def get_state(self, agent):
        """Return current state for an agent. Unknown agents default to COLD."""
        return self._states.get(agent, COLD)

    def all_states(self):
        """Return dict of all tracked agents -> states."""
        # Include all agents we've ever seen + currently in any state
        agents = set(self._states.keys()) | self._current_participants
        return {a: self._states.get(a, COLD) for a in sorted(agents)}

    def _set_state(self, agent, new_state, reason=""):
        old = self._states.get(agent, COLD)
        if old == new_state:
            return
        self._states[agent] = new_state
        self._log.append({
            "agent": agent,
            "from": old,
            "to": new_state,
            "ts": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "round": self._round_id,
        })
        if new_state == SLEEP:
            self._sleep_since[agent] = time.time()
        elif new_state != SLEEP:
            self._sleep_since.pop(agent, None)

    def start_round(self, participants):
        """Begin a new round. Participants activate COLD->HOT or SLEEP->HOT."""
        self._round_id += 1
        self._current_participants = set(participants)
        for agent in participants:
            state = self.get_state(agent)
            if state == COLD:
                self._set_state(agent, HOT, "activated for round %d" % self._round_id)
            elif state == SLEEP:
                self._set_state(agent, HOT, "re-activated from SLEEP for round %d" % self._round_id)
            # HOT agents stay HOT (they're continuing)

    def end_round(self):
        """End current round. Non-participating HOT agents -> SLEEP."""
        for agent in list(self._states.keys()):
            if self._states.get(agent) == HOT:
                if agent not in self._current_participants:
                    self._set_state(agent, SLEEP, "round %d ended; non-participant" % self._round_id)
                # Participating HOT agents stay HOT (they remain active for follow-up)
        # Actually: ALL HOT agents become SLEEP at round end (the round is over).
        # Re-correction per spec: "portal auto-deactivates agents after a round ends"
        # So ALL HOT -> SLEEP.
        for agent in list(self._states.keys()):
            if self._states.get(agent) == HOT:
                self._set_state(agent, SLEEP, "round %d ended; all participants idle" % self._round_id)
        self._current_participants = set()

    def tick(self, now=None):
        """Advance the clock. Expire SLEEP->COLD for agents past TTL.
        Returns list of agents that transitioned to COLD (need model unload)."""
        if now is None:
            now = time.time()
        expired = []
        for agent in list(self._states.keys()):
            if self._states.get(agent) != SLEEP:
                continue
            sleep_start = self._sleep_since.get(agent, now)
            if (now - sleep_start) >= self.ttl_s:
                self._set_state(agent, COLD, "TTL expired (%ds)" % self.ttl_s)
                self._pending_unloads.append(agent)
                expired.append(agent)
        return expired

    def vram_pressure(self, agents_to_cold):
        """Force SLEEP->COLD for specified agents due to VRAM pressure.
        Returns list of agents that transitioned."""
        forced = []
        for agent in agents_to_cold:
            if self._states.get(agent) == SLEEP:
                self._set_state(agent, COLD, "VRAM pressure unload")
                self._pending_unloads.append(agent)
                forced.append(agent)
            elif self._states.get(agent) == HOT:
                # Cannot force-unload a HOT agent mid-round; mark for post-round
                pass  # stays HOT until end_round
        return forced

    def pending_unloads(self):
        """Return and clear the list of agents needing model unload (SLEEP->COLD)."""
        out = list(self._pending_unloads)
        self._pending_unloads.clear()
        return out

    def transition_log(self, last_n=20):
        """Return recent transition history."""
        return self._log[-last_n:]


def selftest():
    failures = []

    def check(name, cond, detail=""):
        print(("PASS  " if cond else "FAIL  ") + name + ("  [" + detail + "]" if (detail and not cond) else ""))
        if not cond:
            failures.append(name)

    # --- Test 1: Basic lifecycle COLD->HOT->SLEEP->COLD ---
    sm = AgentStateMachine(ttl_s=10)
    check("T1 initial COLD", sm.get_state("researcher") == COLD)
    
    sm.start_round(["researcher", "builder"])
    check("T1 researcher HOT after start_round", sm.get_state("researcher") == HOT)
    check("T1 builder HOT after start_round", sm.get_state("builder") == HOT)
    check("T1 scribe still COLD (not participant)", sm.get_state("scribe") == COLD)

    sm.end_round()
    check("T1 researcher SLEEP after end_round", sm.get_state("researcher") == SLEEP)
    check("T1 builder SLEEP after end_round", sm.get_state("builder") == SLEEP)

    # Simulate TTL expiry (ttl=10s, so tick at +11s)
    import time as _t
    base = _t.time()
    expired = sm.tick(now=base + 11)
    check("T1 researcher COLD after TTL", sm.get_state("researcher") == COLD)
    check("T1 builder COLD after TTL", sm.get_state("builder") == COLD)
    check("T1 unloads pending", set(sm.pending_unloads()) == {"researcher", "builder"})

    # --- Test 2: SLEEP->HOT re-activation before TTL ---
    sm2 = AgentStateMachine(ttl_s=100)
    sm2.start_round(["scribe"])
    sm2.end_round()
    check("T2 scribe SLEEP", sm2.get_state("scribe") == SLEEP)

    # New round includes scribe again before TTL
    sm2.start_round(["scribe", "mechanic"])
    check("T2 scribe re-activated to HOT", sm2.get_state("scribe") == HOT)
    check("T2 mechanic activated to HOT", sm2.get_state("mechanic") == HOT)

    sm2.end_round()
    check("T2 both SLEEP after second round", sm2.get_state("scribe") == SLEEP and sm2.get_state("mechanic") == SLEEP)

    # --- Test 3: VRAM pressure forces SLEEP->COLD ---
    sm3 = AgentStateMachine(ttl_s=100)
    sm3.start_round(["orchestrator", "archivist"])
    sm3.end_round()
    check("T3 both SLEEP", sm3.get_state("orchestrator") == SLEEP and sm3.get_state("archivist") == SLEEP)

    forced = sm3.vram_pressure(["archivist"])
    check("T3 archivist forced COLD by VRAM pressure", sm3.get_state("archivist") == COLD)
    check("T3 orchestrator still SLEEP (not pressured)", sm3.get_state("orchestrator") == SLEEP)
    check("T3 archivist in pending unloads", "archivist" in sm3.pending_unloads())

    # --- Test 4: HOT agent cannot be force-unloaded mid-round ---
    sm4 = AgentStateMachine(ttl_s=100)
    sm4.start_round(["builder"])
    forced = sm4.vram_pressure(["builder"])
    check("T4 builder stays HOT (mid-round protection)", sm4.get_state("builder") == HOT)
    check("T4 no forced transition", len(forced) == 0)

    # --- Test 5: Transition log records all changes ---
    sm5 = AgentStateMachine(ttl_s=10)
    sm5.start_round(["x"])
    sm5.end_round()
    sm5.tick(now=time.time() + 11)
    log = sm5.transition_log()
    check("T5 log has 3 entries (COLD->HOT, HOT->SLEEP, SLEEP->COLD)", len(log) == 3, str(len(log)))
    check("T5 log[0] COLD->HOT", log[0]["from"] == COLD and log[0]["to"] == HOT)
    check("T5 log[1] HOT->SLEEP", log[1]["from"] == HOT and log[1]["to"] == SLEEP)
    check("T5 log[2] SLEEP->COLD", log[2]["from"] == SLEEP and log[2]["to"] == COLD)

    # --- Test 6: Multiple rounds, state persists correctly ---
    sm6 = AgentStateMachine(ttl_s=500)
    sm6.start_round(["a", "b"])
    sm6.end_round()
    sm6.start_round(["b", "c"])
    check("T6 b stays HOT (re-activated from SLEEP)", sm6.get_state("b") == HOT)
    check("T6 c activated to HOT", sm6.get_state("c") == HOT)
    check("T6 a still SLEEP (not in round 2)", sm6.get_state("a") == SLEEP)

    print("\n%d/%d selftest checks passed" % (18 - len(failures), 18))
    if failures:
        print("FAILED:", failures)
        return 1
    print("ALL STATE MACHINE CASES PASS")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(selftest())
