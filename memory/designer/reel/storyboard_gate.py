"""storyboard_gate.py - Reel's self-critique gate (autonomy gap #2)
Validates a storyboard markdown file before stage-2 handoff to Lumen.
Checks: (a) hook <=1s, (b) shot count == beat count, (c) every caption has [ref:...] token.
Usage: python memory/designer/reel/storyboard_gate.py <storyboard.md>
Exit: 0=PASS, 1=FAIL
"""
import re, sys, pathlib

def load(path):
    return pathlib.Path(path).read_text(encoding='utf-8')

def check_hook(text):
    """Shot 1 duration must be <=1s (hook in first second)."""
    # Look for the first shot's duration pattern: "0.5s", "1s", "1.0s" etc.
    m = re.search(r'(?:shot\s*1|beat\s*1)[^\n]*?(\d+(?:\.\d+)?)\s*s', text, re.I)
    if not m:
        return False, "No duration found for shot 1"
    dur = float(m.group(1))
    if dur > 1.0:
        return False, f"Hook shot 1 is {dur}s (must be <=1s)"
    return True, f"Hook OK ({dur}s)"

def check_shot_beat_count(text):
    """Shot count must equal beat count."""
    shots = re.findall(r'^\s*(?:shot|beat)\s*\d+', text, re.I | re.M)
    # Count unique shot numbers
    shot_nums = set()
    for s in shots:
        m = re.search(r'(\d+)', s)
        if m:
            shot_nums.add(int(m.group(1)))
    # Also look for a "beats:" or "N beats" declaration
    beat_decl = re.search(r'(\d+)\s*beats?', text, re.I)
    if beat_decl:
        declared = int(beat_decl.group(1))
        actual = len(shot_nums)
        if actual != declared:
            return False, f"Declared {declared} beats but found {actual} shot lines"
    # If no declaration, at least 1 shot required
    if not shot_nums:
        return False, "No shots found in storyboard"
    return True, f"{len(shot_nums)} shots present"

def check_citations(text):
    """Every caption line must contain a [ref:...] token."""
    captions = re.findall(r'caption[^\n]*', text, re.I)
    if not captions:
        # No captions section - pass (silent clips allowed)
        return True, "No captions (silent clip OK)"
    missing = []
    for cap in captions:
        if '[ref:' not in cap.lower():
            # Extract the caption text for reporting
            txt = cap.strip()[:60]
            missing.append(txt)
    if missing:
        return False, f"{len(missing)} caption(s) missing [ref:...] token: {missing[:3]}"
    return True, f"All {len(captions)} captions cited"

def main():
    if len(sys.argv) < 2:
        print("Usage: python storyboard_gate.py <storyboard.md>")
        sys.exit(1)
    
    path = sys.argv[1]
    if not pathlib.Path(path).exists():
        print(f"FAIL: file not found: {path}")
        sys.exit(1)
    
    text = load(path)
    results = [
        check_hook(text),
        check_shot_beat_count(text),
        check_citations(text),
    ]
    
    all_pass = True
    for i, (ok, msg) in enumerate(results, 1):
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] Check {i}: {msg}")
        if not ok:
            all_pass = False
    
    verdict = "PASS" if all_pass else "FAIL"
    print(f"\n{verdict}: {path}")
    sys.exit(0 if all_pass else 1)

if __name__ == '__main__':
    main()
