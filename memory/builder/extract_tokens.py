import re, io, os

CSS = 'ui/app.css'
TOK = 'ui/tokens.css'

css = open(CSS, encoding='utf-8').read()

# Idempotency guard
if os.path.exists(TOK) and "@import 'tokens.css'" in css:
    print('ALREADY DONE - tokens.css exists and app.css imports it. No change.')
    raise SystemExit(0)

m_root = re.search(r':root\{.*?\}', css, flags=re.S)
m_ltc  = re.search(r'/\* Light theme.*?\*/', css, flags=re.S)
m_ltr  = re.search(r'\[data-theme=light\]\{.*?\}', css, flags=re.S)
assert m_root and m_ltc and m_ltr, (bool(m_root), bool(m_ltc), bool(m_ltr))
dark_root = m_root.group(0)
light_comment = m_ltc.group(0)
light_rule = m_ltr.group(0)

# 1) Build tokens.css (single source of truth for the token family)
tokens = (
    '/* ui/tokens.css - design-token source of truth (Designer Goal #1; extracted by Builder 2026-11-19).\n'
    '   Dark family in :root; light override in [data-theme=light]. Literal values ONLY in the light\n'
    '   block (a var() alias there would be a cycle and invalidate every token at computed-value time).\n'
    '   Loaded via @import at top of ui/app.css. | sibling: ui/app.css | parent: index.html */\n'
    + dark_root + '\n\n' + light_comment + '\n' + light_rule + '\n'
)
open(TOK, 'w', encoding='utf-8').write(tokens)

# 2) Rewrite app.css: remove the three blocks, reference tokens.css in header, add @import first.
new = css.replace(dark_root, '').replace(light_comment, '').replace(light_rule, '')
new = new.replace(
    '/* Agent Portal - UI styles (design tokens in :root at top).',
    '/* Agent Portal - UI styles (design tokens live in ui/tokens.css, imported first below).' )
# insert @import right after the leading header comment's closing */
i = new.find('*/')
new = new[:i+2] + "\n@import 'tokens.css';" + new[i+2:]
open(CSS, 'w', encoding='utf-8').write(new)

# 3) Verify
rescan = open(CSS, encoding='utf-8').read()
hex_app = re.findall(r'#[0-9a-fA-F]{3,8}\b', rescan)
tok_text = open(TOK, encoding='utf-8').read()
hex_tok = re.findall(r'#[0-9a-fA-F]{3,8}\b', tok_text)
print('app.css hex remaining =', len(hex_app), sorted(set(hex_app)))
print('tokens.css hex total  =', len(hex_tok))
print('app.css first 6 lines:')
for l in rescan.splitlines()[:6]:
    print('   ', l[:90])
