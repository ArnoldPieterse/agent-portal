#!/usr/bin/env python3
"""ARIA accessible-name audit for the portal (Designer Goal #1, ARIA leg).

Checks every interactive element in index.html for an accessible name via one of:
  - aria-label / aria-labelledby attribute
  - wrapping <label>control</label>
  - sibling <label for="id"> linked to the control's id
  - visible text content (buttons/links)
Flags elements with NO programmatic association. Sibling labels WITHOUT a `for`
attribute do NOT count (WCAG 4.1.2: name must be programmatically associated).

Usage: python memory/designer/aria_audit.py
Exit 0 = no gaps, exit 1 = gaps found (count printed on last line).
"""
import re, html, sys

def strip_tags(s):
    return html.unescape(re.sub(r'<[^>]+>', ' ', s)).strip()

def main(path='index.html'):
    with open(path, encoding='utf-8') as f:
        doc = f.read()

    # id -> True for labels that are WRAPPING a control (label contains the control)
    wrapping_ids = set()
    for m in re.finditer(r'<label\b([^>]*)>(.*?)</label>', doc, re.I | re.S):
        attrs, inner = m.group(1), m.group(2)
        cm = re.search(r'id=["\']([^"\']+)["\']', inner)
        if cm:
            wrapping_ids.add(cm.group(1))

    # id -> True for labels with a matching `for`
    linked_ids = set()
    for m in re.finditer(r'<label\b([^>]*)>', doc, re.I):
        fm = re.search(r'for=["\']([^"\']+)["\']', m.group(1), re.I)
        if fm:
            linked_ids.add(fm.group(1))

    interactive_re = re.compile(r'<(button|input|select|textarea)\b([^>]*)>', re.I)
    gaps = []
    total = 0
    for m in interactive_re.finditer(doc):
        tag, attrs = m.group(1).lower(), m.group(2)
        im = re.search(r'id=["\']([^"\']+)["\']', attrs, re.I)
        eid = im.group(1) if im else None
        tm = re.search(r'type=["\']([^"\']+)["\']', attrs, re.I)
        t = tm.group(1).lower() if tm else ''
        if tag == 'input' and t in ('hidden',):
            continue
        total += 1
        has_attr = 'aria-label' in attrs or 'aria-labelledby' in attrs
        end = doc.find('</%s>' % tag, m.end())
        inner = doc[m.end():end] if end != -1 else ''
        visible = strip_tags(inner)
        assoc = (eid is not None) and (eid in wrapping_ids or eid in linked_ids)
        name_ok = has_attr or assoc or len(visible) > 0
        if not name_ok:
            gaps.append((tag, (eid or '?'), t))

    print('interactive elements:', total, '| missing accessible name:', len(gaps))
    for tag, eid, t in gaps:
        print(f'   {tag}#{eid}' + (f' type={t}' if t else ''))
    print(f'RESULT: {len(gaps)} element(s) missing an accessible name')
    return 1 if gaps else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'index.html'))
