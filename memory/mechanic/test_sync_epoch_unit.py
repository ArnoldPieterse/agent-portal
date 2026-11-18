"""Unit tests T1-T12 for memory_mirror_epoch.py (Goal #10).
Run: python memory/mechanic/test_sync_epoch_unit.py
"""
import os, json, sys, tempfile, shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from memory_mirror_epoch import (
    resolve_owner, _md5, load_epoch_manifest, save_epoch_manifest,
    bump_epoch, sync_file, quarantine_file
)

PASS = 0
FAIL = 0

def check(tid, desc, condition):
    global PASS, FAIL
    status = "PASS" if condition else "FAIL"
    if condition: PASS += 1
    else: FAIL += 1
    print(f"  {tid} {status}: {desc}")

def make_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    return path

OWNERSHIP = {
    "version": 1,
    "default_owner": "White",
    "rules": [
        {"prefix": "memory/researcher/", "owner": "Researcher"},
        {"prefix": "memory/designer/",   "owner": "Designer"},
        {"prefix": "memory/mechanic/",   "owner": "Mechanic"},
        {"prefix": "memory/orchestrator/","owner": "Orchestrator"},
        {"prefix": "memory/builder/",    "owner": "Builder"},
        {"prefix": "memory/verifier/",   "owner": "Verifier"},
        {"prefix": "memory/scribe/",     "owner": "Scribe"},
        {"prefix": "memory/archivist/",  "owner": "Archivist"}
    ]
}

def run_tests():
    global PASS, FAIL
    tmpdir = tempfile.mkdtemp(prefix="epoch_test_")
    manifest = {"version": 1, "entries": {}}

    r = resolve_owner("TODO.md", OWNERSHIP)
    check("T1", f"resolve_owner('TODO.md') == 'White' (got '{r}')", r == "White")

    r = resolve_owner("memory/researcher/x.md", OWNERSHIP)
    check("T2", f"resolve_owner('memory/researcher/x.md') == 'Researcher' (got '{r}')", r == "Researcher")

    om_sub = {"version":1,"default_owner":"White","rules":[
        {"prefix":"memory/researcher/","owner":"Researcher"},
        {"prefix":"memory/researcher/sub/","owner":"Archivist"}]}
    r = resolve_owner("memory/researcher/sub/y.md", om_sub)
    check("T3", f"longest-prefix -> 'Archivist' (got '{r}')", r == "Archivist")

    sp = make_file(os.path.join(tmpdir, "s1"), "hello")
    dp = os.path.join(tmpdir, "d1_missing")
    action, meta = sync_file(sp, dp, "memory/researcher/new.txt", "Researcher", "White", manifest, "push")
    check("T4", f"new file -> copy, epoch=1 (got '{action}', {meta.get('new_epoch')})", action=="copy" and meta.get("new_epoch")==1)

    sp2 = make_file(os.path.join(tmpdir, "s2"), "same")
    dp2 = make_file(os.path.join(tmpdir, "d2"), "same")
    action, _ = sync_file(sp2, dp2, "TODO.md", "White", "White", manifest, "push")
    check("T5", f"same hash -> skip_same (got '{action}')", action=="skip_same")

    sp3 = make_file(os.path.join(tmpdir, "s3"), "v2")
    dp3 = make_file(os.path.join(tmpdir, "d3"), "v1")
    action, meta = sync_file(sp3, dp3, "TODO.md", "White", "White", manifest, "push")
    check("T6", f"owner push -> copy/owner_push (got '{action}'/'{meta.get('reason')}')", action=="copy" and meta.get("reason")=="owner_push")

    sp4 = make_file(os.path.join(tmpdir, "s4"), "r1")
    dp4 = make_file(os.path.join(tmpdir, "d4"), "r0")
    action, _ = sync_file(sp4, dp4, "memory/researcher/f.md", "Researcher", "White", manifest, "push")
    check("T7", f"foreign push -> skip_foreign (got '{action}')", action=="skip_foreign")

    sp5 = make_file(os.path.join(tmpdir, "s5"), "new")
    dp5 = make_file(os.path.join(tmpdir, "d5"), "old")
    action, meta = sync_file(sp5, dp5, "remote_red/x.txt", "Red", "White", manifest, "pull", remote_seat="Red")
    check("T8", f"owner pull -> copy/owner_pull (got '{action}'/'{meta.get('reason')}')", action=="copy" and meta.get("reason")=="owner_pull")

    sp6 = make_file(os.path.join(tmpdir, "s6"), "foreign")
    dp6 = make_file(os.path.join(tmpdir, "d6"), "original")
    action, _ = sync_file(sp6, dp6, "TODO.md", "White", "White", manifest, "pull", remote_seat="Red")
    check("T9", f"foreign pull -> quarantine (got '{action}')", action=="quarantine")

    m2 = {"version":1,"entries":{}}
    e1 = bump_epoch(m2, "TODO.md", "White", OWNERSHIP)
    e2 = bump_epoch(m2, "TODO.md", "White", OWNERSHIP)
    e3 = bump_epoch(m2, "TODO.md", "White", OWNERSHIP)
    check("T10", f"epoch 1,2,3 (got {e1},{e2},{e3})", e1==1 and e2==2 and e3==3)

    qroot = os.path.join(tmpdir, "q")
    sp7 = make_file(os.path.join(tmpdir, "s7"), "quarantine me")
    quarantine_file(sp7, "memory/researcher/foreign.md", "Red", "test", qroot)
    qdirs = os.listdir(qroot)
    meta_ok = False
    if len(qdirs)==1:
        mp = os.path.join(qroot, qdirs[0], "_meta.json")
        if os.path.exists(mp):
            with open(mp) as f: md = json.load(f)
            meta_ok = md.get("source_seat")=="Red"
    check("T11", f"quarantine dir+meta (dirs={len(qdirs)}, ok={meta_ok})", len(qdirs)==1 and meta_ok)

    m3 = {"version":1,"entries":{"t.md":{"owner":"White","epoch":5,"last_writer":"White","ts":"2026-01-01T00:00:00"}}}
    spath = os.path.join(tmpdir, "e.json")
    save_epoch_manifest(m3, spath)
    no_tmp = not os.path.exists(spath + ".tmp")
    with open(spath) as f: loaded = json.load(f)
    check("T12", f"atomic write ok (no_tmp={no_tmp}, epoch={loaded['entries']['t.md']['epoch']})", no_tmp and loaded["entries"]["t.md"]["epoch"]==5)

    shutil.rmtree(tmpdir)
    print(f"\nRESULT: {PASS} PASS, {FAIL} FAIL / {PASS+FAIL}")
    return FAIL == 0

if __name__ == "__main__":
    ok = run_tests()
    sys.exit(0 if ok else 1)
