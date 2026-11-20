#!/usr/bin/env python
"""Memory Deduplication Engine (Archivist goal #8, serves goal #6 pass 3).

Finds near-duplicate content across memory/ files using character shingling
+ Jaccard similarity. Pairs with similarity > threshold are reported as merge
candidates: keep the more specific (longer / dated) file, redirect the other.

Usage:
  python memory/archivist/dedup.py [--threshold 0.85] [--roots memory/goals/archive memory/synthesis]
                                   [--min-chars 200] [--json out.json]

Exit codes: 0 = ran clean (regardless of findings), 1 = usage/IO error.
"""
import argparse, hashlib, itertools, json, os, sys, time

def shingles(text, k=5):
    """Character k-shingles of normalized text."""
    t = ' '.join(text.lower().split())  # normalize whitespace
    if len(t) < k:
        return {t} if t else set()
    return {t[i:i+k] for i in range(len(t) - k + 1)}

def jaccard(a, b):
    if not a or not b:
        return 0.0
    # cheap pre-filter: size ratio
    if len(a) < len(b) * 0.5 or len(b) < len(a) * 0.5:
        return 0.0
    inter = len(a & b)
    return inter / (len(a) + len(b) - inter)

def specificity(p, size):
    """Prefer keeping: dated files over undated, longer files over shorter."""
    name = os.path.basename(p).lower()
    has_date = any(ch.isdigit() for ch in name[:10])
    return (has_date, size)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--threshold', type=float, default=0.85)
    ap.add_argument('--roots', nargs='+', default=['memory/goals/archive', 'memory/synthesis'])
    ap.add_argument('--min-chars', type=int, default=200)
    ap.add_argument('--json', dest='json_out')
    ap.add_argument('--apply', action='store_true', help='write redirect stubs for each pair')
    args = ap.parse_args()

    files = []
    for root in args.roots:
        if not os.path.isdir(root):
            continue
        for dp, dn, fn in os.walk(root):
            for f in fn:
                p = os.path.join(dp, f)
                try:
                    text = open(p, encoding='utf-8', errors='replace').read()
                except OSError:
                    continue
                if len(text) < args.min_chars:
                    continue
                files.append((p, len(text), shingles(text)))
    print(f"scanned {len(files)} files (>= {args.min_chars} chars) under: {', '.join(args.roots)}")

    t0 = time.time()
    pairs = []
    for (pa, sa, ga), (pb, sb, gb) in itertools.combinations(files, 2):
        sim = jaccard(ga, gb)
        if sim >= args.threshold:
            keep, drop = sorted([(pa, sa), (pb, sb)], key=lambda ps: specificity(*ps), reverse=True)
            pairs.append({
                'similarity': round(sim, 3),
                'keep': keep[0], 'keep_bytes': keep[1],
                'redirect': drop[0], 'redirect_bytes': drop[1],
                'recoverable_bytes': drop[1],
            })
    pairs.sort(key=lambda x: -x['similarity'])
    dt = time.time() - t0

    total_recoverable = sum(p['recoverable_bytes'] for p in pairs)
    print(f"found {len(pairs)} near-dup pairs (>= {args.threshold}), "
          f"{total_recoverable:,} B recoverable, in {dt:.1f}s")
    for p in pairs[:20]:
        print(f"  {p['similarity']:.3f}  keep={p['keep']}  redirect={p['redirect']} ({p['recoverable_bytes']:,} B)")

    if args.json_out:
        json.dump({'threshold': args.threshold, 'roots': args.roots,
                   'files_scanned': len(files), 'pairs': pairs,
                   'total_recoverable_bytes': total_recoverable},
                  open(args.json_out, 'w', encoding='utf-8'), indent=1)
        print(f"json written: {args.json_out}")

    if args.apply:
        import datetime
        today = datetime.date.today().isoformat()
        applied, skipped = [], []
        for p in pairs:
            keep, red = p['keep'], p['redirect']
            # skip if redirect already a stub
            try:
                existing = open(red, encoding='utf-8', errors='replace').read()
            except OSError:
                skipped.append((red, 'not found'))
                continue
            if existing.startswith('# REDIRECT'):
                skipped.append((red, 'already stub'))
                continue
            # verify keep file still exists
            if not os.path.isfile(keep):
                skipped.append((red, f'keep missing: {keep}'))
                continue
            stub = (f"# REDIRECT → {keep}\n\n"
                    f"Merged by dedup.py on {today}. Similarity={p['similarity']:.3f}.\n"
                    f"Original content preserved in the keep file.\n")
            open(red, 'w', encoding='utf-8').write(stub)
            applied.append({'redirect': red, 'keep': keep, 'similarity': p['similarity']})
        print(f"\nAPPLIED: {len(applied)} redirects written, {len(skipped)} skipped")
        for s in skipped:
            print(f"  skip: {s}")
        # verify all pointers resolve
        broken = [a['redirect'] for a in applied if not os.path.isfile(a['keep'])]
        print(f"pointer check: {len(applied) - len(broken)}/{len(applied)} resolve OK")
        if args.json_out:
            data = json.load(open(args.json_out))
            data['applied'] = applied
            data['skipped'] = [{'redirect': s[0], 'reason': s[1]} for s in skipped]
            data['broken_pointers'] = broken
            json.dump(data, open(args.json_out, 'w', encoding='utf-8'), indent=1)
    return 0

if __name__ == '__main__':
    sys.exit(main())
