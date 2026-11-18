#!/usr/bin/env python
"""stale_claim_check.py - Verifier's stale-evidence detector.

Scans the memory/ tree for lines that assert an artifact exists (citing a
memory/** path) and cross-checks whether that file is actually on disk. Flags:
  MISSING   - a cited memory/**.md/.py/.json/.jsonl/.log/.css/.js does not exist
              (a 'verified'/'done' claim pointing at nothing = stale/false claim)
  STALE     - a cited artifact whose mtime predates the citing file's own mtime
              by >30 days (claim post-dates the evidence it leans on)

Usage:
  python memory/ops/stale_claim_check.py            # scan, print report
  python memory/ops/stale_claim_check.py --json     # machine-readable
Exit: 0 = no MISSING claims, 1 = at least one MISSING (stale) claim found.
"""
import os, re, sys, json, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACT_RE = re.compile(r'memory/[A-Za-z0-9_./\-]+\.(?:md|py|json|jsonl|log|css|js|txt)')
# Completion-asserting keywords: only lines that CLAIM something is done/verified/evidence
# count as 'claims'. Plain tree-listings (e.g. Archivist decay-report snapshot) are noise.
CLAIM_RE = re.compile(r'\b(verified|done|built|landed|complete[d]?|evidence|see |at |now in|stored|written|committed|ready|closed)\b', re.I)
# Paths that are auto-generated/transient and NOT evidence claims -> ignore entirely.
def is_noise(ref):
    return ('__pycache__' in ref) or ('.cpython-' in ref) or ref.endswith(('.pyc',))
STALE_DAYS = 30
# Cited .json paths often point at .jsonl log files (and vice versa). Resolve the
# real on-disk path tolerating this one-extension mismatch before flagging MISSING.
def resolve(ref):
    rabs=os.path.join(ROOT,*ref.split("/"))
    if os.path.exists(rabs): return rabs
    base=ref.rsplit('.',1)[0]
    for ext in (".json",".jsonl"):
        alt=os.path.join(ROOT,*((base+ext).split("/")))
        if os.path.exists(alt): return alt
    return None

def walk_files():
    out=[]
    for dp,_,fns in os.walk(ROOT):
        if ".git" in dp: continue
        for fn in fns:
            p=os.path.join(dp,fn)
            rel=os.path.relpath(p,ROOT).replace("\\","/")
            if rel.startswith("memory/") and rel.endswith((".md",".py",".txt",".json")):
                out.append((rel,p))
    return out

def main():
    files=walk_files()
    seen=set(); missing=[]; stale=[]
    now=time.time()
    for rel,abs_ in files:
        try: txt=open(abs_,encoding="utf-8",errors="ignore").read()
        except Exception: continue
        try: cite_mtime=os.path.getmtime(abs_)
        except OSError: continue
        # work line-by-line so we can require the citing LINE to assert completion
        for ln in txt.splitlines():
            if not CLAIM_RE.search(ln): continue
            for m in ARTIFACT_RE.finditer(ln):
                ref=m.group(0)
                if is_noise(ref) or ref==rel: continue
                key=(rel,ref)
                if key in seen: continue
                seen.add(key)
                rabs=resolve(ref)
                if rabs is None:
                    missing.append((rel,ref))
                else:
                    try:
                        amtime=os.path.getmtime(rabs)
                        age_days=(cite_mtime-amtime)/86400.0
                        if age_days>STALE_DAYS and "memory/ops/stale_claim_check" not in rel:
                            stale.append((rel,ref,round(age_days,1)))
                    except OSError: pass
    report={"scanned_files":len(files),"referenced_paths":len(seen),
            "missing":sorted(missing),"stale":sorted(stale)}
    if "--json" in sys.argv:
        print(json.dumps(report,indent=2)); 
    else:
        print("STALE CLAIM CHECK  %d files scanned, %d distinct refs"%(len(files),len(seen)))
        print("MISSING cited artifacts: %d"%len(missing))
        for c,r in report["missing"][:50]: print("  [MISSING] %s -> %s"%(c,r))
        print("STALE (artifact >%dd older than claim): %d"%(STALE_DAYS,len(stale)))
        for c,r,d in report["stale"][:30]: print("  [STALE +%dh] %s -> %s"%(d,c,r))
    sys.exit(1 if missing else 0)

if __name__=="__main__":
    main()
