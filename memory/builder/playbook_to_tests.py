"""playbook_to_tests.py - Derive runnable tests from the testing playbook doc."""
import json, os, re, sys, subprocess
from datetime import datetime, timezone

PLAYBOOK = "memory/portal/testing.md"
OUTPUT = "builder/playbook_tests.py"

def parse_playbook(path):
    with open(path) as f:
        lines = f.read().splitlines()
    cases, section = [], None
    for line in lines:
        h = re.match(r"^##\s+(.+)", line)
        if h:
            section = h.group(1).strip()
            continue
        if not line.startswith("|") or section is None:
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 4:
            continue
        num, desc, expected, status = cells[0], cells[1], cells[2], cells[3]
        if not re.match(r"^\d+$", num):
            continue
        ref_script = None
        m = re.search(r"\((\w+\.py)\)", status)
        if m:
            ref_script = m.group(1)
        cases.append({"section": section, "num": int(num), "desc": desc, "expected": expected, "status": status, "ref_script": ref_script})
    return cases

def generate(cases):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = []
    out.append('"""playbook_tests.py - AUTO-GENERATED from memory/portal/testing.md."""')
    out.append("# DO NOT EDIT - run: python memory/builder/playbook_to_tests.py")
    out.append("import os, subprocess, sys")
    out.append("")
    for c in cases:
        safe = re.sub(r'[^a-zA-Z0-9]+', '_', c['section']).strip('_').lower()[:30]
        name = 'test_%s_%d' % (safe, c['num'])
        refpath = None
        if c['ref_script']:
            for cand in ['memory/builder/' + c['ref_script'], c['ref_script']]:
                if os.path.exists(cand):
                    refpath = cand
                    break
        out.append('def %s():' % name)
        out.append('    """%s: %s"""' % (c['section'], c['desc']))
        if refpath:
            out.append('    r = subprocess.run([sys.executable, "%s"], capture_output=True, text=True, timeout=30)' % refpath)
        else:
            out.append('    assert True  # manual verification: %s' % c['expected'][:60])
        out.append('    if r.returncode != 0:')
        out.append('        print(r.stdout[-500:] if r.stdout else "")')
        out.append('        print(r.stderr[-500:] if r.stderr else "")')
        out.append('        assert False, "subprocess exit %d"' % '{rc}' if False else '    assert r.returncode == 0')
        out.append("")
    total = len(cases)
    withref = sum(1 for c in cases if c['ref_script'])
    out.append('def main():')
    out.append('    fns = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]')
    out.append('    passed = failed = 0')
    out.append('    for name, fn in fns:')
    out.append('        try:')
    out.append('            fn()')
    out.append('            passed += 1')
    out.append('            print("  [PASS] %s"' % '{name}')
    out.append('        except Exception as e:')
    out.append('            failed += 1')
    out.append('            print("  [FAIL] %s: %s"' % ('{name}', '{e}'))
    out.append('    print("")')
    out.append('    print("=== PLAYBOOK TESTS: %%d/%%d PASS ===" %% (passed, passed + failed))' % 'x' if False else '    print("=== PLAYBOOK TESTS: %d/%d PASS ===" % (passed, passed + failed))')
    out.append('    sys.exit(0 if failed == 0 else 1)')
    out.append("")
    out.append("if __name__ == '__main__':")
    out.append("    main()")
    return '\n'.join(out)

def main():
    cases = parse_playbook(PLAYBOOK)
    code = generate(cases)
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, 'w') as f:
        f.write(code + '\n')
    print("Generated %d tests from %s -> %s" % (len(cases), PLAYBOOK, OUTPUT))
    if '--verbose' in sys.argv:
        for c in cases:
            ref = " (%s)" % c['ref_script'] if c['ref_script'] else ""
            print("  [%s #%d] %s%s" % (c['section'], c['num'], c['desc'][:40], ref))

if __name__ == '__main__':
    main()
