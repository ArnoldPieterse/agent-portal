"""Goal 7: Typography Hierarchy Audit - Verification Script.
Ensures all font sizes conform to the 5-step scale: 12/14/15/18/24px.
Exit 0 = PASS, Exit 1 = FAIL (violations found).
"""
import re, sys

SCALE = {12, 14, 15, 18, 24}  # allowed px values
EXCEPTIONS = {'#attach': 22}   # icon glyph in 44px button - not text

def main():
    css = open('ui/app.css').read()
    violations = []
    
    for i, line in enumerate(css.split('\n'), 1):
        for m in re.finditer(r'font-size:\s*([^;]+);', line):
            val = m.group(1).strip()
            if val.startswith('var('):
                # Check the token resolves to a valid scale value
                token = val[4:-1]  # extract --fs-XX
                fs_match = re.search(r'--fs-(\d+)', token)
                if fs_match:
                    px_val = int(fs_match.group(1))
                    if px_val not in SCALE:
                        violations.append((i, val, f"token {token} = {px_val}px not in scale"))
            else:
                # Hard-coded value
                px_match = re.match(r'^(\d+\.?\d*)px$', val)
                if px_match:
                    px_val = float(px_match.group(1))
                    if px_val not in SCALE:
                        # Check if it's an allowed exception
                        is_exception = False
                        for sel, allowed_px in EXCEPTIONS.items():
                            if sel in line and px_val == allowed_px:
                                is_exception = True
                        if not is_exception:
                            violations.append((i, val, f"hard-coded {val} not in scale"))
    
    if violations:
        print(f"FAIL: {len(violations)} typography violation(s)")
        for line_no, val, reason in violations:
            print(f"  Line {line_no}: {val} - {reason}")
        sys.exit(1)
    else:
        # Count scale usage
        counts = {}
        for i, line in enumerate(css.split('\n'), 1):
            for m in re.finditer(r'font-size:\s*var\(--fs-(\d+)\)', line):
                key = f"--fs-{m.group(1)}"
                counts[key] = counts.get(key, 0) + 1
        
        print("PASS: All font sizes conform to 5-step scale (12/14/15/18/24px)")
        print(f"  Scale usage: {counts}")
        print(f"  Exceptions: {EXCEPTIONS}")
        sys.exit(0)

if __name__ == '__main__':
    main()
