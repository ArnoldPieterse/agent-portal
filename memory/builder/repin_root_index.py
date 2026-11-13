#!/usr/bin/env python3
"""repin_root_index.py - Builder 2026-11-13 (r15c). HASH-GATED re-pin one-shot.

A-R14 runbook line (Mechanic, memory/mechanic/a-r14-write-path-2026-11-13.md):
no bare inline root writes ever again; copies go through this one-shot, and the
gate SKIPS the copy when source and dest MD5 already match, so no-op runs
preserve the destination mtime (no phantom new mtimes / stale-hash confusion).

Usage (run from the canonical root on White):
  python repin_root_index.py -Source <known-good file> [-Dest index.html] [--expect-md5 <hash>]

Canonical pin as of r14c: md5 9c6b08e3d98355e632a72cb871d5b60d / 67,681 B.
Exit codes: 0 = ok (skip or verified repin), 1 = error.
"""
import argparse
import datetime
import hashlib
import os
import shutil
import sys


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def _mtime(path):
    return datetime.datetime.fromtimestamp(os.stat(path).st_mtime).strftime('%Y-%m-%d %H:%M:%S')


def repin(source, dest='index.html', expect_md5=None):
    """Hash-gated copy. Returns a result dict; never raises on expected conditions."""
    if not os.path.exists(source):
        return {'status': 'error', 'detail': 'source missing: %s' % source}
    src = md5(source)
    if expect_md5 and src != expect_md5.lower():
        return {'status': 'error',
                'detail': 'source md5 %s != --expect-md5 %s (refusing to repin from unverified source)' % (src, expect_md5)}
    exists = os.path.exists(dest)
    dst_before = md5(dest) if exists else None
    mt_before = _mtime(dest) if exists else None
    if dst_before == src:
        # GATE: hashes match -> no copy at all, mtime untouched.
        return {'status': 'skip', 'src_md5': src, 'dst_md5_after': src,
                'mtime_before': mt_before, 'mtime_after': _mtime(dest)}
    shutil.copyfile(source, dest)
    dst_after = md5(dest)
    if dst_after != src:
        return {'status': 'error', 'detail': 'post-copy hash mismatch: got %s expected %s' % (dst_after, src)}
    return {'status': 'repin', 'src_md5': src, 'dst_md5_before': dst_before,
            'dst_md5_after': dst_after, 'mtime_before': mt_before, 'mtime_after': _mtime(dest)}


def main():
    ap = argparse.ArgumentParser(description='hash-gated re-pin one-shot (A-R14 runbook)')
    ap.add_argument('-Source', dest='source', required=True)
    ap.add_argument('-Dest', dest='dest', default='index.html')
    ap.add_argument('--expect-md5', dest='expect', default=None,
                    help='refuse to run unless source md5 matches (canonical pin: 9c6b08e3d98355e632a72cb871d5b60d)')
    a = ap.parse_args()
    r = repin(a.source, a.dest, a.expect)
    if r['status'] == 'skip':
        print('SKIP: dest already matches source (md5=%s) - no copy, mtime preserved (%s)' % (r['src_md5'], r['mtime_before']))
    elif r['status'] == 'repin':
        print('REPIN DONE: %s -> %s; mtime %s -> %s' % (r['dst_md5_before'], r['dst_md5_after'], r['mtime_before'], r['mtime_after']))
    else:
        print('ERROR: %s' % r['detail'], file=sys.stderr)
    sys.exit(0 if r['status'] in ('skip', 'repin') else 1)


if __name__ == '__main__':
    main()
