#!/usr/bin/env python3
"""Evolution FULL-LIFECYCLE validator - Verifier goal #10 (cycle 3 deep-dive).

Extends the cycle-2 3-state validator (CANDIDATE/LIVING/DEAD) to the full
cycle-3 lifecycle contract:

    propose -> test -> select -> merge -> archive

States (lifecycle):
    PROPOSED      - change proposed, genome recorded, pre-written tests attached
    TEST_PASSED   - pre-written tests executed and green
    TEST_FAILED   - pre-written tests executed and red
    SELECTED      - a tested-passed candidate chosen for promotion
    MERGED        - selected change applied to the target (island)
    ARCHIVED      - terminal: merged + sealed, no further mutation
    REJECTED      - terminal (DEAD): rejected/rolled back at any pre-archive stage

Legal transitions:
    propose : (none)         -> PROPOSED
    test    : PROPOSED       -> TEST_PASSED | TEST_FAILED
    select  : TEST_PASSED    -> SELECTED
    merge   : SELECTED       -> MERGED
    archive : MERGED         -> ARCHIVED
    reject  : {PROPOSED,TEST_PASSED,TEST_FAILED,SELECTED,MERGED} -> REJECTED

Illegal (MUST be rejected, state must remain unchanged):
    - select on PROPOSED / TEST_FAILED / REJECTED / MERGED / ARCHIVED
    - merge  on PROPOSED / TEST_PASSED / TEST_FAILED / SELECTED?->no legal /
             REJECTED / ARCHIVED
    - archive on PROPOSED / TEST_PASSED / SELECTED / REJECTED (skips stages)
    - test   on TEST_PASSED / MERGED / ARCHIVED (re-test after terminal/merge)
    - reject on ARCHIVED (already sealed)

Two execution modes:
  * model  - validates the reference state machine (this file). Always runnable;
             proves the lifecycle CONTRACT + transition matrix is sound.
  * engine - if a real evolution.py CLI is present in CWD (adapter seam), drives
             it via subprocess and asserts the same rejections. Reports which mode
             actually ran so evidence is never over-claimed.

Usage: python memory/verifier/evolution_lifecycle_validator.py [--engine]
Exit 0 iff every illegal transition was rejected AND state stayed clean.
"""
import argparse, json, os, subprocess, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_JSON = os.path.join(HERE, "evolution-lifecycle-validator-2026-11-17.json")
OUT_MD = os.path.join(HERE, "evolution-lifecycle-validator-2026-11-17.md")

# ---- reference state machine -------------------------------------------------
TERMINAL = {"ARCHIVED", "REJECTED"}
LEGAL = {
    ("PROPOSED",     "test"):  {"TEST_PASSED", "TEST_FAILED"},
    ("TEST_PASSED",  "select"):{"SELECTED"},
    ("SELECTED",     "merge"): {"MERGED"},
    ("MERGED",       "archive"):{"ARCHIVED"},
}
# reject is legal from any non-terminal state
REJECT_OK = {"PROPOSED", "TEST_PASSED", "TEST_FAILED", "SELECTED", "MERGED"}

class RefEngine:
    """Reference model of the full lifecycle. Clean-state on illegal ops."""
    def __init__(self):
        self.entities = {}   # id -> state
        self.next_id = 1
    def propose(self, spec="s"):
        eid = f"CHG-{self.next_id:04d}"; self.next_id += 1
        self.entities[eid] = "PROPOSED"
        return eid
    def _check(self, eid):
        if eid not in self.entities:
            raise ValueError(f"{eid} not found")
        return self.entities[eid]
    def test(self, eid, result="TEST_PASSED"):
        st = self._check(eid)
        if st != "PROPOSED":
            raise ValueError(f"test illegal: {eid} is {st}, not PROPOSED")
        if result not in ("TEST_PASSED", "TEST_FAILED"):
            raise ValueError("bad test result")
        self.entities[eid] = result
    def select(self, eid):
        st = self._check(eid)
        if st != "TEST_PASSED":
            raise ValueError(f"select illegal: {eid} is {st}, not TEST_PASSED")
        self.entities[eid] = "SELECTED"
    def merge(self, eid):
        st = self._check(eid)
        if st != "SELECTED":
            raise ValueError(f"merge illegal: {eid} is {st}, not SELECTED")
        self.entities[eid] = "MERGED"
    def archive(self, eid):
        st = self._check(eid)
        if st != "MERGED":
            raise ValueError(f"archive illegal: {eid} is {st}, not MERGED")
        self.entities[eid] = "ARCHIVED"
    def reject(self, eid):
        st = self._check(eid)
        if st not in REJECT_OK:
            raise ValueError(f"reject illegal: {eid} is {st} (terminal)")
        self.entities[eid] = "REJECTED"
    def state(self, eid):
        return self._check(eid)

# ---- test plan ---------------------------------------------------------------
# Each case: build a fixture entity to a given state, then attempt `op` which is
# ILLEGAL; assert it raises AND that the entity's state is unchanged (clean).
ILLEGAL_CASES = [
    # name, setup_fn(eng)->eid, op, expected_error_fragment
    ("L1_select_on_proposed",       lambda e: _mk(e, "PROPOSED"),     "select",  "not TEST_PASSED"),
    ("L2_select_on_test_failed",    lambda e: _mk(e, "TEST_FAILED"),  "select",  "not TEST_PASSED"),
    ("L3_merge_on_proposed",        lambda e: _mk(e, "PROPOSED"),     "merge",   "not SELECTED"),
    ("L4_merge_on_test_passed",     lambda e: _mk(e, "TEST_PASSED"),  "merge",   "not SELECTED"),
    ("L5_archive_on_selected",      lambda e: _mk(e, "SELECTED"),     "archive", "not MERGED"),
    ("L6_archive_on_proposed",      lambda e: _mk(e, "PROPOSED"),     "archive", "not MERGED"),
    ("L7_test_on_merged",           lambda e: _mk(e, "MERGED"),       "test",    "not PROPOSED"),
    ("L8_reject_on_archived",       lambda e: _mk(e, "ARCHIVED"),     "reject",  "terminal"),
    ("L9_select_on_rejected",       lambda e: _mk(e, "REJECTED"),     "select",  "not TEST_PASSED"),
    ("L10_merge_on_archived",       lambda e: _mk(e, "ARCHIVED"),     "merge",   "not SELECTED"),
]
LEGAL_CASES = [
    # full happy path, one entity, must not raise and must land in ARCHIVED
    ("H1_full_lifecycle", ["test","select","merge","archive"]),
    ("H2_reject_from_selected", ["test","select","reject"]),
]

def _mk(e, target):
    eid = e.propose()
    steps = {"PROPOSED": [], "TEST_PASSED": ["test"],
             "TEST_FAILED": ["test_fail"],
             "SELECTED": ["test","select"],
             "MERGED": ["test","select","merge"],
             "ARCHIVED": ["test","select","merge","archive"],
             "REJECTED": ["reject"]}
    for s in steps[target]:
        if s == "test":      e.test(eid, "TEST_PASSED")
        elif s == "test_fail": e.test(eid, "TEST_FAILED")
        elif s == "select":  e.select(eid)
        elif s == "merge":   e.merge(eid)
        elif s == "archive": e.archive(eid)
        elif s == "reject":  e.reject(eid)
    return eid

OPS = {"test": lambda e,i: e.test(i), "select": lambda e,i: e.select(i),
       "merge": lambda e,i: e.merge(i), "archive": lambda e,i: e.archive(i),
       "reject": lambda e,i: e.reject(i)}

# ---- engine adapter (seam) ---------------------------------------------------
def engine_available():
    return os.path.exists("evolution.py") and os.path.exists(os.path.join("evolution","population.json"))

def run_model():
    results = []
    # illegal cases
    for name, setup, op, frag in ILLEGAL_CASES:
        e = RefEngine()
        eid = setup(e)
        before = e.state(eid)
        try:
            OPS[op](e, eid)
            raised, msg = False, "(no error raised)"
        except ValueError as ex:
            raised, msg = True, str(ex)
        after = e.state(eid)
        rejected = raised and (frag in msg.lower() or frag in msg)
        clean = (before == after)
        ok = rejected and clean
        results.append({"test": name, "op": op, "state_before": before,
                        "expected_reject_frag": frag, "raised": raised,
                        "error": msg, "state_after": after, "clean_state": clean,
                        "illegal_rejected": rejected, "pass": ok})
    # legal happy paths
    for name, ops in LEGAL_CASES:
        e = RefEngine(); eid = e.propose()
        try:
            for o in ops:
                if o == "test": e.test(eid, "TEST_PASSED")
                else: OPS[o](e, eid)
            final = e.state(eid); ok = True; err = None
        except ValueError as ex:
            final = e.state(eid); ok = False; err = str(ex)
        expected_final = "ARCHIVED" if name == "H1_full_lifecycle" else "REJECTED"
        results.append({"test": name, "ops": ops, "final_state": final,
                        "expected_final": expected_final, "error": err,
                        "pass": ok and final == expected_final})
    return results

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--engine", action="store_true")
    args = ap.parse_args()
    mode = "engine" if (args.engine and engine_available()) else "model"
    if mode == "engine":
        print("[lifecycle_validator] WARNING: live-engine adapter not yet wired; "
              "falling back to model mode.")
        mode = "model"
    results = run_model()
    total = len(results)
    passed = sum(1 for r in results if r["pass"])
    all_pass = passed == total
    n_illegal = len(ILLEGAL_CASES)
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "engine_available_in_cwd": engine_available(),
        "lifecycle": "propose -> test -> select -> merge -> archive",
        "states": ["PROPOSED","TEST_PASSED","TEST_FAILED","SELECTED","MERGED","ARCHIVED","REJECTED"],
        "illegal_attempts": n_illegal,
        "total_tests": total, "passed": passed, "failed": total-passed, "all_pass": all_pass,
        "results": results,
    }
    with open(OUT_JSON, "w") as f: json.dump(report, f, indent=2)
    # markdown evidence
    lines = ["# Evolution full-lifecycle validator — cycle 3 (goal #10)",
             f"\n- timestamp: {report['timestamp']}",
             f"- mode: **{mode}** (engine in CWD: {engine_available()})",
             f"- lifecycle: `{report['lifecycle']}`",
             f"- illegal attempts: **{n_illegal}** | tests {passed}/{total} pass | all_pass={all_pass}",
             "\n## Illegal transitions (must reject + keep state clean)",
             "| case | op | before -> after | rejected | clean | error |", 
             "|---|---|---|---|---|---|"]
    for r in results:
        if "op" in r and r["op"]:
            lines.append(f"| {r['test']} | {r['op']} | {r['state_before']} -> {r['state_after']} "
                         f"| {'yes' if r['illegal_rejected'] else 'NO'} | {'yes' if r['clean_state'] else 'NO'} "
                         f"| {r['error']} |")
    lines += ["\n## Legal happy paths", "| case | ops | final | expected | pass |",
              "|---|---|---|---|---|"]
    for r in results:
        if "ops" in r:
            lines.append(f"| {r['test']} | {'->'.join(r['ops'])} | {r['final_state']} "
                         f"| {r['expected_final']} | {'yes' if r['pass'] else 'NO'} |")
    with open(OUT_MD, "w") as f: f.write("\n".join(lines) + "\n")
    print(f"[lifecycle_validator] mode={mode} illegal_attempts={n_illegal} "
          f"{passed}/{total} pass all_pass={all_pass}")
    if not all_pass:
        print("FAILURES:", [r['test'] for r in results if not r['pass']])
    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())
