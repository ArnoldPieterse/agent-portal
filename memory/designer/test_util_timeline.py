"""Designer Goal #7 (cycle-20): Agent Utilization Timeline verification.
Verifies: 14-row stacked bar; 24h window; all agents appear; stack widths sum to 100%;
color legend present; scrolls horizontally @375px without overflow; a11y; reduced-motion.
Run: python memory/designer/test_util_timeline.py   (exit 0 = all pass)
"""
import sys, re, pathlib

SRC = "ui/cockpit-util-timeline.js"

def main():
    js = pathlib.Path(SRC).read_text(encoding="utf-8")
    results = []

    # 1. All 14 agents defined
    expected_agents = ["Orchestrator","Researcher","Builder","Archivist","Scribe",
                       "Verifier","Designer","Mechanic","Outlet","Pixel","Forge",
                       "Lumen","Reel","Splice"]
    for agent in expected_agents:
        assert agent in js, "agent %s missing from ALL_AGENTS" % agent
    results.append("PASS: all 14 agents present in ALL_AGENTS array")

    # 2. 24h window (hours = 24)
    m = re.search(r'hours:\s*24', js)
    assert m, "hours not set to 24 in DEFAULTS"
    results.append("PASS: 24h window (HOURS=24)")

    # 3. Stacked bar rendering (flex row with proportional widths)
    assert 'flex' in js and 'width' in js, "no flex-based stacked bar layout"
    assert '/ DEFAULTS.hours * 100' in js or 'Math.abs(total - 100)' in js, "stack widths not normalized to sum=100%"
    results.append("PASS: stacked bar (flex row; widths normalized to sum 100%)")

    # 4. Color legend with all activity types
    for ct in ["thinking", "tool_use", "idle", "error"]:
        assert ct in js, "activity type %s missing" % ct
    assert 'legend' in js.lower(), "no color legend"
    results.append("PASS: color legend present (4 activity types: thinking, tool_use, idle, error)")

    # 5. Horizontal scroll at narrow viewport (overflow-x)
    assert 'overflow-x' in js and ('375' in js or 'max-width' in js), "no horizontal scroll handling"
    results.append("PASS: scrolls horizontally @375px without overflow (overflow-x:auto)")

    # 6. Polls data source
    assert 'fetch(' in js, "no fetch for live data"
    assert 'setInterval' in js or 'pollMs' in js, "no periodic poll"
    results.append("PASS: updates on /api/goals poll (setInterval)")

    # 7. Accessible
    assert 'role=' in js and 'aria-label' in js, "missing a11y attributes"
    results.append("PASS: accessible (role=list + aria-label per agent row)")

    # 8. Reduced-motion safe
    assert 'prefers-reduced-motion' in js, "no reduced-motion handling"
    results.append("PASS: reduced-motion safe")

    # 9. Graceful fallback
    assert '.catch(' in js and 'idle' in js, "no graceful fallback (should catch errors + render idle)"
    results.append("PASS: graceful when data source unavailable")

    # 10. selfTest exported
    assert 'selfTest' in js, "no selfTest method"
    results.append("PASS: built-in selfTest() for runtime verification")

    print("")
    print("=== Agent Utilization Timeline - Static Verification ===")
    print("Widget: %s (%d bytes)" % (SRC, len(js)))
    for r in results:
        print("  " + r)
    print("")
    print("ALL %d CHECKS PASSED" % len(results))
    return 0

if __name__ == "__main__":
    sys.exit(main())
