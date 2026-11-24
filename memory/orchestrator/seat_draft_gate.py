"""seat_draft_gate.py - Seat Draft Goal Quality Gate.

Validates goals drafted on behalf of unreachable seats (Archivist, Scribe):
  (a) goal is executable by the seat's role tools
  (b) verification criteria don't require >24h continuous online time
  (c) has a designated backup agent

Usage:
    python memory/orchestrator/seat_draft_gate.py --selftest
    python memory/orchestrator/seat_draft_gate.py --check <goal_text> --agent <seat>
"""
import pathlib, json, re, sys
from datetime import datetime

MEM = pathlib.Path("memory")
OUTPUT = MEM / "orchestrator" / "draft-gate-results.json"

# Role tool capabilities per seat (what each seat CAN do with its tools)
ROLE_CAPABILITIES = {
    "archivist": ["read_files", "write_files", "search", "index", "cite", "summarize", "cross_reference"],
    "scribe": ["read_files", "write_files", "synthesize", "compress", "format", "summarize"],
    "orchestrator": ["read_files", "write_files", "dispatch", "schedule", "model_routing", "hr"],
    "researcher": ["web_search", "read_files", "write_files", "cross_check", "evidence"],
    "builder": ["terminal", "python", "edit_file", "create_files", "test"],
    "verifier": ["terminal", "python", "test_batteries", "audit", "rollback_test"],
    "designer": ["render_html", "css", "ui_craft", "critique", "build_interfaces"],
    "mechanic": ["terminal", "probe", "recovery", "load_test", "vram_monitor"],
}

# Tools that require the seat to be "online" (i.e., need model inference)
ONLINE_TOOLS = {"web_search", "render_html", "synthesize", "cross_check", "evidence"}

def check_executable_by_role(goal_text: str, agent: str) -> tuple:
    """(a) Check goal is executable by the seat's role tools."""
    caps = ROLE_CAPABILITIES.get(agent, [])
    if not caps:
        return False, f"Unknown agent '{agent}' - no capabilities defined"
    
    # Detect required tools from goal text
    required_tools = set()
    text_lower = goal_text.lower()
    
    tool_indicators = {
        "web_search": ["search the web", "find online", "look up", "research.*source"],
        "render_html": ["render", "html", "canvas", "ui", "widget", "dashboard"],
        "terminal": ["terminal", "command", "script", "run.*python", "bash"],
        "python": ["python", "script", "compute", "algorithm", "formula"],
        "edit_file": ["edit", "modify", "update.*file", "change.*code"],
        "create_files": ["create", "write.*file", "new.*file", "build"],
        "read_files": ["read", "scan", "parse", "check.*file"],
        "write_files": ["write", "output", "save", "log to"],
        "search": ["grep", "find", "locate", "index"],
        "test": ["test", "verify", "assert", "selftest"],
    }
    
    for tool, patterns in tool_indicators.items():
        for pat in patterns:
            if re.search(pat, text_lower):
                required_tools.add(tool)
                break
    
    # Tool equivalences: create_files ~ write_files, test ~ verify
    TOOL_EQUIV = {
        "create_files": ["write_files", "create_files"],
        "test": ["test", "verify", "assert"],
        "edit_file": ["edit_file", "write_files"],
    }
    
    # Check all required tools are in capabilities (with some flexibility)
    missing = []
    for tool in required_tools:
        equivs = TOOL_EQUIV.get(tool, [tool])
        if not any(eq in caps or any(eq in c or c in eq for c in caps) for eq in equivs):
            missing.append(tool)
    
    if missing:
        return False, f"Requires tools not in {agent} capabilities: {missing}"
    return True, "All required tools within role capabilities"

def check_duration(goal_text: str) -> tuple:
    """(b) Verification criteria don't require >24h continuous online time."""
    # Look for indicators of long-running tasks
    duration_risks = []
    
    patterns_24h = [
        r"(wait|monitor).{0,20}(>\s*)?24",
        r"continuous.{0,20}24",
        r"overnight",
        r"multi.day",
        r"several.days",
        r"week.long",
    ]
    
    for pat in patterns_24h:
        if re.search(pat, goal_text, re.IGNORECASE):
            duration_risks.append(pat)
    
    # Check for "wait for X to complete" type patterns without timeout
    wait_patterns = re.findall(r"(?:wait|monitor|poll).{0,50}(?:complete|finish|done)", goal_text, re.IGNORECASE)
    if wait_patterns:
        # If there's a wait but no explicit timeout/batch mechanism, flag it
        if not re.search(r"(timeout|batch|chunk|incremental|per.cycle|per.pass)", goal_text, re.IGNORECASE):
            duration_risks.append("unbounded_wait")
    
    if duration_risks:
        return False, f"Potential >24h requirement: {duration_risks}"
    return True, "No >24h continuous online requirement detected"

def check_backup_agent(goal_text: str) -> tuple:
    """(c) Has a designated backup agent."""
    # Look for explicit backup designation
    backup_patterns = [
        r"backup[:\s]+(\w+)",
        r"fallback[:\s]+(\w+)",
        r"if.*unavailable.*(?:use|assign|delegate).*?(\w+)",
        r"designated.by[:\s]+(\w+)",
    ]
    
    for pat in backup_patterns:
        m = re.search(pat, goal_text, re.IGNORECASE)
        if m:
            return True, f"Backup agent designated: {m.group(1)}"
    
    # Also check if the goal text mentions another agent as secondary
    agents = list(ROLE_CAPABILITIES.keys())
    mentioned = [a for a in agents if a in goal_text.lower()]
    if len(mentioned) >= 2:
        return True, f"Multiple agents referenced (implicit backup): {mentioned}"
    
    return False, "No designated backup agent found in goal text"

def validate_draft(goal_text: str, agent: str) -> dict:
    """Run all three checks and return combined result."""
    a_pass, a_msg = check_executable_by_role(goal_text, agent)
    b_pass, b_msg = check_duration(goal_text)
    c_pass, c_msg = check_backup_agent(goal_text)
    
    overall = a_pass and b_pass and c_pass
    return {
        "agent": agent,
        "goal_preview": goal_text[:100],
        "checks": {
            "executable_by_role": {"pass": a_pass, "detail": a_msg},
            "duration_ok": {"pass": b_pass, "detail": b_msg},
            "backup_agent": {"pass": c_pass, "detail": c_msg},
        },
        "overall": overall,
    }

def selftest():
    """5 test drafts: mix of pass/fail."""
    print("=== seat_draft_gate.py SELFTEST ===")
    
    tests = [
        # Test 1: PASS - valid archivist goal with backup
        {
            "text": "Create convergence-kb.md defining steady-state criteria. Read and index existing files. Output to memory/archivist/. Backup: Scribe.",
            "agent": "archivist",
            "expected": True,
        },
        # Test 2: FAIL - requires web_search (not in archivist caps)
        {
            "text": "Search the web for latest LLM benchmarks and compile into a report. Save to memory/archivist/benchmarks.md.",
            "agent": "archivist",
            "expected": False,
        },
        # Test 3: FAIL - requires >24h monitoring without batch mechanism
        {
            "text": "Monitor the fleet continuously for several days and log every state change. Wait for all cycles to complete before writing summary.",
            "agent": "scribe",
            "expected": False,
        },
        # Test 4: PASS - valid scribe goal with fallback
        {
            "text": "Synthesize the last 3 cycle retrospectives into a single decision log. Compress to <2KB. Fallback: Archivist.",
            "agent": "scribe",
            "expected": True,
        },
        # Test 5: FAIL - no backup agent designated
        {
            "text": "Read all pointer maps and verify cross-references resolve. Write report to memory/archivist/xref-report.md.",
            "agent": "archivist",
            "expected": False,
        },
    ]
    
    passed = 0
    for i, t in enumerate(tests, 1):
        result = validate_draft(t["text"], t["agent"])
        ok = result["overall"] == t["expected"]
        status = "PASS" if ok else "FAIL"
        print(f"  Test {i} [{t['agent']}] expected={t['expected']} got={result['overall']}: {status}")
        if not ok:
            print(f"    Checks: {json.dumps(result['checks'], indent=2)[:300]}")
        else:
            passed += 1
    
    print(f"\n  Result: {passed}/5 correct")
    
    all_pass = passed == 5
    print(f"  SELFTEST: {'PASS' if all_pass else 'FAIL'}")
    
    # Write results
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps([validate_draft(t["text"], t["agent"]) for t in tests], indent=2), encoding="utf-8")
    
    return all_pass

def main():
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    
    if "--check" in sys.argv and "--agent" in sys.argv:
        idx_text = sys.argv.index("--check")
        idx_agent = sys.argv.index("--agent")
        text = sys.argv[idx_text + 1]
        agent = sys.argv[idx_agent + 1]
        result = validate_draft(text, agent)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["overall"] else 1)

if __name__ == "__main__":
    main()
