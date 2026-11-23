
def js_scan(content, _debug=False):
    import sys
    def LOG(*a):
        if _debug: print('   ', *a)
    n=len(content); i=0; line=1
    CODE='code'; TPL='template'
    NORM='norm'; LC='lc'; BC='bc'; SS='ss'; DS='ds'; RX='rx'
    stack=[{'kind':CODE,'b':0,'p':0,'k':0}]
    mode=NORM; prev_sig=None; issues=[]
    def top(): return stack[-1]
    while i<n:
        ch=content[i]; nxt=content[i+1] if i+1<n else ''
        if ch=='\n': line+=1
        ctx=top()
        LOG(i, repr(ch), ctx['kind'], mode, 'depth', len(stack))
        if ctx['kind']==TPL:
            if mode==NORM:
                if ch=='\\': i+=2; continue
                if ch=='`': stack.pop(); continue
                if ch=='$' and nxt=='{':
                    stack.append({'kind':CODE,'b':0,'p':0,'k':0}); mode=NORM; i+=2; continue
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
            if prev_sig in ('ident','num','close'):
                pass
            else:
                mode=RX; prev_sig=None; i+=1; continue
            prev_sig='other'; i+=1; continue
        if ch=='{': ctx['b']+=1; prev_sig='other'
        elif ch=='}':
            if ctx['kind']==CODE and ctx['b']==0 and len(stack)>1:
                stack.pop(); mode=NORM; i+=1; continue
            ctx['b']-=1
            if ctx['b']<0 and len(stack)==1: issues.append("unbalanced braces at line %d"%line)
            prev_sig='close'
        elif ch=='(': ctx['p']+=1; prev_sig='other'
        elif ch==')':
            ctx['p']-=1
            if ctx['p']<0 and len(stack)==1: issues.append("unbalanced parens at line %d"%line)
            prev_sig='close'
        elif ch=='[': ctx['k']+=1; prev_sig='other'
        elif ch==']':
            ctx['k']-=1
            if ctx['k']<0 and len(stack)==1: issues.append("unbalanced brackets at line %d"%line)
            prev_sig='close'
        else:
            if ch.isalnum() or ch=='_' or ch=='$': prev_sig='ident'
            elif ch.isdigit(): prev_sig='num'
            elif not ch.isspace(): prev_sig='other'
        i+=1; continue
    root=stack[0]
    for key,name in [('b','braces'),('p','parens'),('k','brackets')]:
        if root[key]>0: issues.append("unclosed %s: %d extra"%(name,root[key]))
    if len(stack)>1:
        issues.append("unterminated template/string at line %d"%line)
    return issues
