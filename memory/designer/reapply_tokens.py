"""Re-apply design token layer to ui/app.css after mirror revert.
Run: python memory/designer/reapply_tokens.py
Last verified: 2026-11-17 (36 tokens, all checks pass)
"""
import re

css = open('ui/app.css').read()

# Check if already applied (quick heuristic: look for --radius-sm in :root)
if '--radius-sm' in css[:500]:
    print("Tokens already present - no action needed.")
    exit(0)

# Add new tokens to :root
root_match = re.search(r':root\s*{([^}]+)}', css)
old_content = root_match.group(1)
new_tokens = """
  --radius-sm:6px;--radius-md:8px;--radius-lg:12px;
  --shadow-md:0 4px 12px rgba(0,0,0,.4);
  --dur-fast:.15s;--dur-med:.2s;--dur-pulse:1.3s;--dur-spin:.9s;
  --on-accent:#fff;--flink:#6db1ff;--link-hover:#9ccaff;
  --bg-hover:#2a3342;--dim-alt:#8b949e;
"""
new_root = old_content.rstrip() + new_tokens
css = css[:root_match.start()] + ':root{' + new_root + '}' + css[root_match.end():]

# Replace in body
body_start = css.index('}') + 1
body = css[body_start:]

replacements = [
    (r'(color:)\s*#fff\b', r'\1var(--on-accent)'),
    (r'(background:)\s*#2a3342\b', r'\1var(--bg-hover)'),
    (r'(color:)\s*#6db1ff\b', r'\1var(--flink)'),
    (r'(color:)\s*#9ccaff\b', r'\1var(--link-hover)'),
    (r'(color:)\s*#8b949e\b', r'\1var(--dim-alt)'),
    (r'(color:)\s*#8b93a7\b', r'\1var(--dim-alt)'),
]
for pat, repl in replacements:
    body = re.sub(pat, repl, body)

body = re.sub(r'border-radius:\s*6px\b', 'border-radius:var(--radius-sm)', body)
body = re.sub(r'border-radius:\s*8px\b', 'border-radius:var(--radius-md)', body)
body = re.sub(r'border-radius:\s*12px\b', 'border-radius:var(--radius-lg)', body)
body = re.sub(r'(animation:)\s*pulse\s+1\.3s', r'\1pulse var(--dur-pulse)', body)
body = re.sub(r'animation:qspin \d+\.?\d*s', 'animation:qspin var(--dur-spin)', body)
body = re.sub(r'box-shadow:\s*0\s+8px\s+24px\s+rgba\(0,0,0,\.5\)', 'box-shadow:var(--shadow-md)', body)

# Transition durations
lines = body.split('\n')
for i, line in enumerate(lines):
    if ('transition' in line or 'animation' in line) and '@keyframes' not in line:
        lines[i] = re.sub(r'(?<!\.)\.15s\b', 'var(--dur-fast)', lines[i])
        lines[i] = re.sub(r'(?<!\.)\.2s\b', 'var(--dur-med)', lines[i])
body = '\n'.join(lines)

css = css[:body_start] + body
open('ui/app.css', 'w').write(css)
print(f"Done. Tokens: {len(re.findall(r'--[\w-]+\s*:', re.search(r':root\\s*{([^}]+)}', css).group(1)))}")
