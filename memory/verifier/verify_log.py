#!/usr/bin/env python
"""Cross-agent verification logger (protocol v1).
Usage:
  python memory/verifier/verify_log.py --agent designer --goal "designer.md#2" \
      --cmd "python -c \"...\"" [--assert "substring"] [--verdict PASS|FAIL|IN-PROGRESS|NOT-TESTABLE] [--evidence "note"]
  python memory/verifier/verify_log.py --check   # validate log is parseable JSONL
"""
import argparse, datetime, json, os, re, subprocess, sys

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verification-log.jsonl")
VERDICTS = {"PASS", "FAIL", "IN-PROGRESS", "NOT-TESTABLE"}

def check():
    bad = 0
    if not os.path.exists(LOG):
        print("log missing"); return 1
    with open(LOG, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except Exception as ex:
                print(f"line {i}: INVALID JSON ({ex})"); bad += 1; continue
            for k in ("timestamp", "agent", "goal_ref", "command", "exit_code", "verdict"):
                if k not in e:
                    print(f"line {i}: missing key {k}"); bad += 1
            if e.get("verdict") not in VERDICTS:
                print(f"line {i}: bad verdict {e.get('verdict')!r}"); bad += 1
    print(f"check: {i} lines, {bad} problems")
    return 0 if bad == 0 else 2

def record(agent, goal_ref, cmd, assert_sub=None, verdict=None, evidence=""):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        out = (p.stdout or "") + (p.stderr or "").strip()
        exit_code = p.returncode
    except subprocess.TimeoutExpired:
        out, exit_code, verdict = "TIMEOUT", 124, "FAIL"
    if assert_sub is not None:
        ok = assert_sub in out
        evidence = (evidence + "; assert " + ("HIT" if ok else "MISS") + f": {assert_sub!r}").strip("; ")
        auto = "PASS" if ok and exit_code == 0 else "FAIL"
    else:
        auto = None
    final = verdict or auto or ("PASS" if exit_code == 0 else "FAIL")
    entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "agent": agent, "goal_ref": goal_ref, "command": cmd,
        "exit_code": exit_code, "verdict": final, "evidence": evidence[:400],
    }
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    print(json.dumps(entry))
    return 0 if final == "PASS" else 1

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--check", action="store_true")
    a.add_argument("--agent"); a.add_argument("--goal"); a.add_argument("--cmd")
    a.add_argument("--assert", dest="assert_sub"); a.add_argument("--verdict"); a.add_argument("--evidence", default="")
    x = a.parse_args()
    if x.check:
        sys.exit(check())
    if not (x.agent and x.goal and x.cmd):
        a.error("--agent --goal --cmd required")
    if x.verdict and x.verdict not in VERDICTS:
        a.error(f"verdict must be one of {sorted(VERDICTS)}")
    sys.exit(record(x.agent, x.goal, x.cmd, x.assert_sub, x.verdict, x.evidence))

if __name__ == "__main__":
    main()
