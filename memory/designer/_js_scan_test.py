
import sys, pathlib
sys.path.insert(0,'memory/designer')
from _js_scan_proto import js_scan
base=pathlib.Path('ui')
fails=0; total=0
for f in sorted(base.glob('*.js')):
    c=f.read_text(encoding='utf-8',errors='replace'); total+=1
    iss=js_scan(c)
    if iss: fails+=1
    print(f"  {f.name:24} {'PASS' if not iss else 'FAIL '+str(iss)}")
print(f"\nTotal .js files: {total}, failing: {fails}")
tests = {
 "valid_iife": "(function(){var x=[1,2];return {a:1};})();",
 "valid_regex_charclass": 'function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {"&":"x"}[c];});}',
 "valid_template_interp": "var a=`hi ${ {n:1}.n } world`;",
 "valid_nested_template": "var s=`a${`b${1+2}c`}d`;",
 "valid_template_fn": "let h=`<div>${items.map(x=>`<i>${x}</i>`).join('')}</div>`;",
 "invalid_unclosed_brace": "function f(){ if(x){ return 1; // missing }",
 "invalid_unclosed_paren": "var x = ( 1 + 2;",
 "valid_division": "var r = a / b / c;",
 "valid_regex_quantifier": 'var m=s.match(/\\d{2,4}[/]x/);',
 "valid_arrow_regex": "const f=x=>x.replace(/[-]/g,'');",
}
expect_fail={"invalid_unclosed_brace","invalid_unclosed_paren"}
print("\nSelf-test cases:")
ok=True
for name,code in tests.items():
    iss=js_scan(code); should=name in expect_fail; got=bool(iss)
    status="OK" if got==should else "MISMATCH"
    if status=="MISMATCH": ok=False
    print(f"  {name:26} issues={str(iss):34} -> {'fail' if got else 'pass'} ({status})")
print("\nALL SELF-CASES CORRECT:", ok)
