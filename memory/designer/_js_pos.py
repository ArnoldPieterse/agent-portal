
import pathlib
def js_scan_pos(content):
    n=len(content); i=0; line=1
    CODE='code'; TPL='template'
    NORM='norm'; LC='lc'; BC='bc'; SS='ss'; DS='ds'; RX='rx'
    # context: kind + per-type pos stacks
    stack=[{'kind':CODE,'b':[],'p':[],'k':[]}]
    mode=NORM; prev_sig=None; issues=[]
    while i<n:
        ch=content[i]; nxt=content[i+1] if i+1<n else ''
        if ch=='\n': line+=1
        ctx=stack[-1]
        if ctx['kind']==TPL:
            if mode==NORM:
                if ch=='\\': i+=2; continue
                if ch=='`': stack.pop(); i+=1; continue
                if ch=='$' and nxt=='{':
                    stack.append({'kind':CODE,'b':[],'p':[],'k':[]}); mode=NORM; i+=2; continue
                i+=1; continue
            i+=1; continue
        if mode==LC:
            if ch=='\n': mode=NORM
            i+=1; continue
        if mode==BC:
            if ch=='*' and nxt=='/': mode=NORM; i+=2; continue
            i+=1; continue
        if mode in (SS,DS):
            q = "'" if mode==SS else '"'
            if ch=='\\': i+=2; continue
            if ch==q: mode=NORM; prev_sig='close'
            i+=1; continue
        if mode==RX:
            if ch=='\\': i+=2; continue
            if ch=='\n': mode=NORM; prev_sig='other'; i+=1; continue
            if ch=='[':
                j=i+1
                if j<n and content[j]=='^': j+=1
                if j<n and content[j]==']': j+=1
                while j<n and content[j]!=']':
                    if content[j]=='\\': j+=1
                    j+=1
                i=j+1; continue
            if ch=='/': mode=NORM; prev_sig='close'; i+=1; continue
            i+=1; continue
        if ch=='/' and nxt=='/': mode=LC; i+=2; continue
        if ch=='/' and nxt=='*': mode=BC; i+=2; continue
        if ch=="'": mode=SS; prev_sig='close'; i+=1; continue
        if ch=='"': mode=DS; prev_sig='close'; i+=1; continue
        if ch=='`': stack.append({'kind':TPL}); mode=NORM; i+=1; continue
        if ch=='/':
            if prev_sig in ('ident','num','close'): pass
            else: mode=RX; prev_sig=None; i+=1; continue
            prev_sig='other'; i+=1; continue
        if ch=='{': ctx['b'].append(i); prev_sig='other'
        elif ch=='}':
            if ctx['kind']==CODE and len(ctx['b'])==0 and len(stack)>1:
                stack.pop(); mode=NORM; i+=1; continue
            if ctx['b']: ctx['b'].pop()
            else: issues.append("extra } at line %d pos %d"%(line,i))
            prev_sig='close'
        elif ch=='(': ctx['p'].append(i); prev_sig='other'
        elif ch==')':
            if ctx['p']: ctx['p'].pop()
            else: issues.append("extra ) at line %d pos %d"%(line,i))
            prev_sig='close'
        elif ch=='[': ctx['k'].append(i); prev_sig='other'
        elif ch==']':
            if ctx['k']: ctx['k'].pop()
            else: issues.append("extra ] at line %d pos %d"%(line,i))
            prev_sig='close'
        else:
            if ch.isalnum() or ch=='_' or ch=='$': prev_sig='ident'
            elif ch.isdigit(): prev_sig='num'
            elif not ch.isspace(): prev_sig='other'
        i+=1; continue
    root=stack[0]
    for key,name in [('b','{'),('p','('),('k','[')]:
        for pos in root[key]:
            issues.append("UNCLOSED %s at line %d pos %d"%(name, content[:pos].count(chr(10))+1, pos))
    if len(stack)>1: issues.append("unterminated template/string")
    return issues

content = pathlib.Path('ui/cockpit.js').read_text(encoding='utf-8')
iss = js_scan_pos(content)
for x in iss: print(x)
print("---context around each---")
for x in iss:
    import re
    m=re.search(r'pos (\d+)',x)
    if m:
        pos=int(m.group(1)); s=max(0,pos-60)
        print(repr(content[s:pos+30]).replace('\\n',' '))
