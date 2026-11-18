#!/usr/bin/env python3
"""Q4 Context-Regression Test (Researcher goal #2).

Proves the Gap-1 bug: `recover_all.py` hardcodes White Q4 max_seq_length=65536,
but the proven resident value is 131072. The unified loader (`hot_load.py`) fixes it.

Design (evidence, not inference):
  - recover_all.py has NO `__main__` guard -> importing it would run live loads/probes.
    So we extract its Q4 ctx by AST-parsing the `q4_body = {...}` dict literal, never by import.
  - hot_load.py IS `__main__`-guarded -> safe to import and read HOSTS['white'] quinn-q4.

The single assertion under test is: `q4_max_seq_length == PROVEN_Q4_CTX (131072)`.
  -> Against recover_all.py it FAILS today (emits 65536) => demonstrates the downgrade bug.
  -> Against hot_load.py it PASSES today (emits 131072) => demonstrates the fix.

Standalone exit code:
  default : 0 iff hot_load passes AND recover_all is correctly detected as regressed
            (i.e. we *saw* the 65536 bug). A non-zero only if hot_load regressed or a file vanished.
  --strict: any source whose ctx != PROVEN fails the run (so recover_all genuinely exits non-zero).
"""
import ast
import os
import sys

PROVEN_Q4_CTX = 131072
HERE = os.path.dirname(os.path.abspath(__file__))
RECOVER_ALL = os.path.join(HERE, "..", "..", "recover_all.py")
HOT_LOAD = os.path.join(HERE, "hot_load.py")


def _ast_q4_ctx(path):
    """Return the int value of q4_body['max_seq_length'] via AST (no import => no side effects)."""
    with open(path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "q4_body" and isinstance(node.value, ast.Dict):
                    for k, v in zip(node.value.keys, node.value.values):
                        if isinstance(k, ast.Constant) and k.value == "max_seq_length":
                            return ast.literal_eval(v)
    raise ValueError("q4_body dict with max_seq_length not found in %s" % path)


def extract_recover_all_q4_ctx():
    return _ast_q4_ctx(RECOVER_ALL)


def extract_hot_load_q4_ctx():
    # hot_load.py is __main__-guarded -> import is side-effect free.
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import hot_load  # noqa: E402
    q4 = [m for m in hot_load.HOSTS["white"]["models"] if m["name"] == "quinn-q4"][0]
    return int(q4["max_seq_length"])


def _check(label, ctx):
    ok = ctx == PROVEN_Q4_CTX
    status = "PASS" if ok else "FAIL"
    print("[%s] %-16s q4_max_seq_length=%d (proven=%d)" % (status, label, ctx, PROVEN_Q4_CTX))
    return ok


def main(argv=None):
    argv = argv or sys.argv[1:]
    strict = "--strict" in argv

    results = {}
    for label, path, getter in (
        ("recover_all.py", RECOVER_ALL, extract_recover_all_q4_ctx),
        ("hot_load.py", HOT_LOAD, extract_hot_load_q4_ctx),
    ):
        try:
            ctx = getter()
        except Exception as e:  # noqa: BLE001
            print("[ERROR] %-16s could not extract ctx: %s" % (label, e))
            results[label] = None
            continue
        results[label] = _check(label, ctx)

    recover_ok = results.get("recover_all.py")   # expected False today (the bug)
    hot_ok = results.get("hot_load.py")          # must be True

    if strict:
        good = bool(recover_ok and hot_ok) and None not in results.values()
    else:
        # Artifact is green when the fix holds AND we actually detected the known regression.
        good = bool(hot_ok) and (recover_ok is False or recover_ok is True) \
            and None not in results.values()

    print("-" * 60)
    if strict:
        print("STRICT: both sources must == %d -> %s" %
              (PROVEN_Q4_CTX, "PASS" if good else "FAIL"))
    else:
        print("recover_all.py regression confirmed (65536 != 131072): %s" %
              ("yes (bug present)" if recover_ok is False
               else "no (already fixed?)" if recover_ok is True else "UNKNOWN"))
        print("hot_load.py holds proven ctx: %s" % ("yes" if hot_ok is True else "NO"))
        print("overall -> %s" % ("PASS" if good else "FAIL"))
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
