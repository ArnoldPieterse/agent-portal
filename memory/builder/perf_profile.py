#!/usr/bin/env python3
"""Static performance profiler for portal JS files.

Usage: python memory/builder/perf_profile.py [file]
  Defaults to ui/core.js if no file given.

Outputs a ranked list of functions by estimated DOM/network cost,
flagging optimization targets (score > 10).
"""
import pathlib, re, sys, json

WEIGHTS = {
    'createElement': 3,   # node allocation
    'innerHTML_set': 5,   # full parse tree rebuild - most expensive
    'appendChild': 2,     # DOM mutation + potential reflow
    'textContent_set': 1, # cheap text update
    'append': 2,          # shorthand for appendChild
    'querySelector': 1,   # lookup cost
    'style_set': 1,       # style mutation
}
NET_WEIGHT = 10  # network call blocks paint

DOM_PATTERNS = {
    'createElement': r'document\.createElement\s*\(',
    'innerHTML_set': r'\.innerHTML\s*=',
    'appendChild': r'\.appendChild\s*\(',
    'textContent_set': r'\.textContent\s*=',
    'append': r'\.append\s*\(',
    'querySelector': r'\$\(|querySelector',
    'style_set': r'\.style\.\w+\s*=',
}
NET_PATTERNS = {
    'api_call': r'apiClient\.|api\(\s*[\'\" ]',
    'fetch': r'\bfetch\s*\(',
}

def find_functions(lines):
    """Find top-level function definitions with line ranges."""
    func_pat = re.compile(r'^(?:async\s+)?function\s+(\w+)\s*\(')
    funcs = []
    for i, line in enumerate(lines):
        m = func_pat.match(line.strip())
        if not m:
            continue
        depth = 0
        started = False
        for j in range(i, len(lines)):
            for ch in lines[j]:
                if ch == '{': depth += 1; started = True
                elif ch == '}': depth -= 1
            if started and depth == 0:
                funcs.append({'name': m.group(1), 'start': i+1, 'end': j+1})
                break
        else:
            funcs.append({'name': m.group(1), 'start': i+1, 'end': len(lines)})
    return funcs

def profile_file(filepath):
    content = pathlib.Path(filepath).read_text()
    lines = content.split('\n')
    results = []
    
    for f in find_functions(lines):
        body = '\n'.join(lines[f['start']-1:f['end']])
        ops = {}
        score = 0
        for name, pat in DOM_PATTERNS.items():
            count = len(re.findall(pat, body))
            if count:
                ops[name] = count
                score += count * WEIGHTS[name]
        net_count = 0
        for name, pat in NET_PATTERNS.items():
            count = len(re.findall(pat, body))
            if count:
                ops[f'net:{name}'] = count
                net_count += count
        score += net_count * NET_WEIGHT
        
        results.append({
            'name': f['name'], 'lines': f['end'] - f['start'] + 1,
            'score': score, 'ops': ops, 'has_network': net_count > 0
        })
    
    results.sort(key=lambda x: -x['score'])
    return results

def main():
    filepath = sys.argv[1] if len(sys.argv) > 1 else 'ui/core.js'
    results = profile_file(filepath)
    
    print(f"Performance profile: {filepath}")
    print(f"{'Function':<24} {'Lines':>5} {'Score':>6}  Operations")
    print("-" * 85)
    for r in results[:20]:
        ops_str = ' '.join(f"{k}={v}" for k, v in r['ops'].items())
        print(f"{r['name']:<24} {r['lines']:>5} {r['score']:>6}  {ops_str}")
    
    targets = [r for r in results if r['score'] > 10]
    if targets:
        print(f"\n--- OPTIMIZATION TARGETS ({len(targets)} functions with score > 10) ---")
        for t in targets:
            issues = []
            if t['ops'].get('innerHTML_set', 0) > 1:
                issues.append("multiple innerHTML rebuilds (full re-parse each)")
            if t['ops'].get('createElement', 0) > 5:
                issues.append(f"heavy createElement x{t['ops']['createElement']}")
            if t['has_network']:
                issues.append("network in render path (blocks paint)")
            if not issues:
                issues.append("high op count - consider memoization or incremental update")
            print(f"  {t['name']} (score={t['score']}): {'; '.join(issues)}")
    
    # JSON output for programmatic use
    if '--json' in sys.argv:
        print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()
