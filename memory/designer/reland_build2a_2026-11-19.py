#!/usr/bin/env python3
# Re-land pass 2a (White, 2026-11-19): token additions + app.css hex/radius sweep + index.html emoji->SVG
import re, os, sys
os.chdir(r'C:\Projects\Workspace')
ok=[]

# A. tokens: new values for legacy spots
t=open('ui/tokens.css',encoding='utf-8').read()
add="""
/* 2026-11-19 (White re-land pass2): legacy value tokens */
:root{
  --hover-bg:#2a3342;--seg-on:#3a6fd6;
  --dm-bg:rgba(138,99,210,.10);--ok-soft:rgba(61,220,132,.08);--ok-line:rgba(61,220,132,.25);
  --link-dash:rgba(109,177,255,.5);--warn-border:#d29922;--warn-text:#e3b341;
}
"""
if '--hover-bg' not in t:
    open('ui/tokens.css','w',encoding='utf-8').write(t+add); ok.append('tokens+legacy')

# B. app.css hex + radius sweep
a=open('ui/app.css',encoding='utf-8').read()
n=0
def rep(old,new):
    global a,n
    if old in a:
        a=a.replace(old,new); n+=1
rep('color:#fff','color:var(--white)')
rep('#2a3342','var(--hover-bg)')
rep('background:#20304d','background:var(--sel-bg)')
rep('#3a6fd6','var(--seg-on)')
rep('background:#243b63;border-color:#33507f','background:var(--msg-you);border-color:var(--msg-you-bd)')
rep('color:#3ddc84;background:rgba(61,220,132,.08);border:1px solid rgba(61,220,132,.25)','color:var(--ok);background:var(--ok-soft);border:1px solid var(--ok-line)')
rep('border:1px solid #4a3f6b;background:rgba(138,99,210,.10)','border:1px solid var(--dm-border);background:var(--dm-bg)')
rep('color:#b79ce0','color:var(--dm-text)')
rep('.chipfile .st.err{color:#ff6b6b}','.chipfile .st.err{color:var(--err)}')
rep('#8b93a7','var(--muted)')
rep('color:#6db1ff;','color:var(--link);')
rep('rgba(109,177,255,.5)','var(--link-dash)')
rep('.flink:hover{color:#9ccaff','.flink:hover{color:var(--link-hv)')
rep('background:#141a26;border:1px solid #2c3548','background:var(--peek-bg);border:1px solid var(--peek-bd)')
rep('border-bottom:1px solid #2c3548;color:#9ccaff','border-bottom:1px solid var(--peek-bd);color:var(--link-hv)')
rep('.fdot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:var(--sp-8);background:#888}','.fdot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:var(--sp-8);background:var(--dot-idle)}')
rep('.fdot.busy{background:#ffb454}','.fdot.busy{background:var(--dot-busy)}')
rep('.fdot.unknown{background:#e05252}','.fdot.unknown{background:var(--dot-err)}')
rep('background:#0d1117','background:var(--queue-bg)')
rep('#8b949e','var(--queue-dim)')
rep('border:2px solid #30363d;border-top-color:#58a6ff','border:2px solid var(--qspin-bd);border-top-color:var(--qspin-top)')
rep('.qtxt{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#c9d1d9}','.qtxt{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--queue-tx)}')
rep('border:1px solid #d29922;background:#2d2000;color:#e3b341','border:1px solid var(--warn-border);background:var(--int-bg);color:var(--warn-text)')
# radii
a=a.replace('border-radius:8px','border-radius:var(--br-md)'); a=a.replace('border-radius:4px','border-radius:var(--br-sm)'); a=a.replace('border-radius:12px','border-radius:var(--br-lg)')
open('ui/app.css','w',encoding='utf-8').write(a); ok.append('appcss-hex:%d'%n)

# C. index.html remaining emoji -> SVG
h=open('index.html',encoding='utf-8').read()
def iconsvg(name,size):
    i=open('ui/icons.js',encoding='utf-8').read()
    m=re.search(r"\b%s\s*:\s*'(<svg[^']*)'"%name,i)
    if not m: return None
    s=m.group(1)
    if size and size!=24:
        s=s.replace('viewBox="0 0 24 24"','viewBox="0 0 24 24" width="%d" height="%d"'%(size,size))
    return s
h=h.replace('>\U0001F3AF Goals</button>','>'+iconsvg('goal',14)+' Goals</button>')
h=h.replace('>\U0001F527 Ops</button>','>'+iconsvg('wrench',14)+' Ops</button>')
h=h.replace('>\u2702 Prune done TODO</button>','>'+iconsvg('scissors',14)+' Prune done TODO</button>')
open('index.html','w',encoding='utf-8').write(h); ok.append('index-svg')

# report
import subprocess
left=[]
for fn in ['ui/app.css','index.html','ui/core.js','ui/uploads.js']:
    for k,l in enumerate(open(fn,encoding='utf-8').read().splitlines(),1):
        if re.search(r'#[0-9a-fA-F]{3,8}\b',l) and fn=='ui/app.css': left.append('HEX '+fn+':'+str(k))
        if re.search(r'[\U0001F000-\U0001FAFF\u2600-\u27BF]',l): left.append('EMOJI '+fn+':'+str(k)+' '+l.strip()[:80])
print('OK:',', '.join(ok))
print('appcss hex left:',len([x for x in left if x.startswith('HEX')]))
for x in left[:30]: print(x)
