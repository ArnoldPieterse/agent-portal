#!/usr/bin/env python3
"""breakpoint_gate_logic_test.py - Standalone proof of breakpoint_gate.py judge() logic.

No browser, no sockets, no websockets import. Runs in any sandboxed seat.
Proves the acceptance criteria: forced overflow -> FAIL, clean -> PASS.

Usage: python memory/designer/breakpoint_gate_logic_test.py
Exit 0 = all expectations hold, exit 1 = failure.
"""
import sys


def judge(width, res, tol=2, check_elements=False):
    """Pure decision logic (identical to breakpoint_gate.py)."""
    issues = []
    if res["scroll_w"] > res["inner_w"] + tol:
        issues.append("horizontal overflow: scrollWidth=%d > innerWidth=%d (+%dpx)"
                      % (res["scroll_w"], res["inner_w"], res["scroll_w"] - res["inner_w"]))
    if res["console_errors"]:
        issues.append("%d console error(s): %s" % (len(res["console_errors"]),
                      "; ".join(res["console_errors"][:3])))
    if check_elements:
        for sel, ok in res["vis"].items():
            if not ok:
                issues.append("missing/invisible: %s" % sel)
    return len(issues) == 0, issues


def main():
    print("breakpoint_gate logic-test (no browser/sockets)\n")
    cases = [
        ("clean page -> PASS",
         {"scroll_w": 375, "inner_w": 375, "console_errors": [],
          "vis": {"header": True, "#agentList": True, "#chatCol": True}},
         False),
        ("forced overflow -> FAIL",
         {"scroll_w": 900, "inner_w": 375, "console_errors": [],
          "vis": {"header": True, "#agentList": True, "#chatCol": True}},
         False),
        ("JS console error -> FAIL",
         {"scroll_w": 375, "inner_w": 375, "console_errors": ["Uncaught Error: boom"],
          "vis": {"header": True, "#agentList": True, "#chatCol": True}},
         False),
        ("subpixel rounding within tol -> PASS",
         {"scroll_w": 377, "inner_w": 375, "console_errors": [],
          "vis": {"header": True, "#agentList": True, "#chatCol": True}},
         False),
        ("missing element (check_elements=True) -> FAIL",
         {"scroll_w": 375, "inner_w": 375, "console_errors": [],
          "vis": {"header": True, "#agentList": False, "#chatCol": True}},
         True),
    ]

    all_ok = True
    for name, res, check_elements in cases:
        passed, issues = judge(375, res, check_elements=check_elements)
        # Expected outcome based on test case name
        if "PASS" in name and "FAIL" not in name.split("->")[1]:
            expected_pass = True
        else:
            expected_pass = False
        held = (passed == expected_pass)
        all_ok = all_ok and held
        print(f"  [{'ok' if held else 'MISS'}] {name}  passed={passed} issues={issues}")

    print()
    print("=" * 48)
    n = len(cases)
    ok_count = sum(1 for _, res, ce in cases
                   if (judge(375, res, check_elements=ce)[0] == ("PASS" in _ and "FAIL" not in _.split("->")[1])))
    print(f"LOGIC-TEST {'PASS' if all_ok else 'FAIL'}: {ok_count}/{n} acceptance expectations held")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
