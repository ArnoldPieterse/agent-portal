"""Verify recovery-matrix.md meets acceptance criteria:
- All 4 hosts (White, Black, Red, Blue) present
- Each host has >=5 numbered steps
- Escalation section present
"""
import re, sys, os

MATRIX = os.path.join(os.path.dirname(__file__), "..", "goals", "mechanic.md")
MATRIX_FILE = os.path.join(os.path.dirname(__file__), "recovery-matrix.md")

def main():
    if not os.path.exists(MATRIX_FILE):
        print("FAIL: recovery-matrix.md not found")
        sys.exit(1)
    
    with open(MATRIX_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    hosts = ["White", "Black", "Red", "Blue"]
    results = []
    
    for host in hosts:
        # Find the section for this host
        pattern = rf"## {host} \(.*?\)\n(.*?)(?=^## |\Z)"
        m = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if not m:
            results.append(f"  {host}: MISSING SECTION")
            continue
        section = m.group(1)
        # Count numbered steps
        steps = re.findall(r"^\d+\. ", section, re.MULTILINE)
        status = "PASS" if len(steps) >= 5 else f"FAIL ({len(steps)} steps)"
        results.append(f"  {host}: {status} ({len(steps)} steps)")
    
    # Check escalation section
    has_escalation = "## Escalation" in content
    results.append(f"  Escalation: {'PASS' if has_escalation else 'FAIL'}")
    
    print("Recovery Matrix Verification:")
    for r in results:
        print(r)
    
    all_pass = all("PASS" in r for r in results)
    print(f"\nOverall: {'PASS' if all_pass else 'FAIL'}")
    sys.exit(0 if all_pass else 1)

if __name__ == "__main__":
    main()
