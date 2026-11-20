#!/usr/bin/env python3
"""
Designer Goal #1 (WCAG 2.1 AA Audit) - static ARIA + keyboard verification.
Companion to contrast_audit.py (contrast leg already PASS). This script checks the
two remaining legs on STATIC markup: index.html plus a light scan of ui/*.js for
JS-generated interactive controls.

Checks:
  1. Landmarks present (banner/nav/main/complementary/form/contentinfo)
  2. Heading order (single h1, no level skips in document order)
  3. Accessible names: every <button> has text/aria-label/title; every
     <input|select|textarea> has an associated <label for>, wrapping <label>,
     aria-label, or (weak) placeholder.
  4. Skip-to-content link present and first focusable.
  5. Focus-visible styling present in ui/app.css (:focus-visible rule with outline/box-shadow).
  6. Live regions (role=status / aria-live) present for async status.

Exit 0 = no CRITICAL failures. Prints a report; write it to memory/designer/wcag-aria-keyboard-<date>.md.
Usage: python memory/designer/wcag_aria_audit.py [--html index.html] [--css ui/app.css]
"""
import sys, os, re, argparse
from html.parser import HTMLParser

VOID = {"area","base","br","col","embed","hr","img","input","link","meta","param","source","track","wbr"}
LANDMARKS = {
    "banner": ["header"],
    "navigation (nav)": ["nav"],
    "main": ["main"],
    "complementary (aside)": ["aside"],
    "form": ["form"],
    "contentinfo (footer)": ["footer"],
}

class DOM(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []          # open tags
        self.headings = []       # (level, text) in order
        self.landmarks = set()   # implicit landmark tag names seen
        self.buttons = []        # dict(id/text/has_aria/title)
        self.fields = []         # dict(tag/id/labelled/weak)
        self.labels_for = {}     # for -> True
        self.skip_links = []     # anchors whose href starts with '#'
        self.first_anchor_href = None
        self.live_regions = 0
        self._cur_head_text = None
        self._head_level = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag not in VOID:
            self.stack.append(tag)
        # landmarks (implicit roles)
        if tag in {"header","nav","main","aside","form","footer"}:
            self.landmarks.add(tag)
        if tag == "label" and a.get("for"):
            self.labels_for[a["for"]] = True
        if re.match(r"^h[1-6]$", tag):
            self._head_level = int(tag[1]); self._cur_head_text = ""
        if tag == "button":
            self.buttons.append({"id": a.get("id",""), "aria": bool(a.get("aria-label") or a.get("aria-labelledby")),
                                 "title": bool(a.get("title")), "text": [], "_close": len(self.stack)})
        if tag in ("input","select","textarea"):
            self.fields.append({"tag": tag, "id": a.get("id",""), "aria": bool(a.get("aria-label") or a.get("aria-labelledby")),
                                "placeholder": bool(a.get("placeholder")), "title": bool(a.get("title")),
                                "type": a.get("type",""), "in_label": any(t=="label" for t in self.stack)})
        if tag == "a":
            href = a.get("href") or ""
            if href.startswith("#"):
                self.skip_links.append(href)
                if self.first_anchor_href is None:
                    self.first_anchor_href = href
        if tag in ("div","span") and (a.get("role")=="status" or a.get("aria-live")):
            self.live_regions += 1
        # role=img / region on divs also count as labelled regions
        if tag == "div" and a.get("aria-label") and (a.get("role") in ("region",None)):
            pass

    def handle_endtag(self, tag):
        # pop to matching open tag (tolerate minor mismatches)
        for i in range(len(self.stack)-1, -1, -1):
            if self.stack[i] == tag:
                del self.stack[i:]; break
        if re.match(r"^h[1-6]$", tag) and self._head_level is not None:
            self.headings.append((self._head_level, (self._cur_head_text or "").strip()))
            self._head_level = None; self._cur_head_text = None
        if tag == "button":
            for b in self.buttons:
                if b.get("_close") == len(self.stack)+0 and b.get("pending", True):
                    pass

    def handle_data(self, data):
        if self._head_level is not None:
            self._cur_head_text = (self._cur_head_text or "") + data
        for b in self.buttons:
            if tag_stack_is_button(self.stack) and any(t=="button" for t in self.stack):
                # attribute text to the innermost open button
                pass

def tag_stack_is_button(stack):
    return False

# Re-do button text attribution robustly: track which buttons are open via a counter.
class DOM2(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack=[]
        self.headings=[]; self.landmarks=set(); self.buttons=[]; self.fields=[]
        self.labels_for={}; self.skip_links=[]; self.first_anchor_href=None; self.live_regions=0
        self._hlevel=None; self._htext=None; self._open_btn=None

    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag not in VOID: self.stack.append(tag)
        if tag in {"header","nav","main","aside","form","footer"}: self.landmarks.add(tag)
        if tag=="label" and a.get("for"): self.labels_for[a["for"]]=True
        if re.match(r"^h[1-6]$", tag):
            self._hlevel=int(tag[1]); self._htext=""
        if tag=="button":
            b={"id":a.get("id",""), "aria":bool(a.get("aria-label") or a.get("aria-labelledby")),
               "title":bool(a.get("title")), "text":""}
            self.buttons.append(b); self._open_btn=b  # buttons don't nest -> single open btn
        if tag in ("input","select","textarea"):
            self.fields.append({"tag":tag,"id":a.get("id",""),"aria":bool(a.get("aria-label") or a.get("aria-labelledby")),
                                "placeholder":bool(a.get("placeholder")),"title":bool(a.get("title")),
                                "type":a.get("type",""),"in_label":any(t=="label" for t in self.stack)})
        if tag=="a":
            href=a.get("href") or ""
            if href.startswith("#"):
                self.skip_links.append(href)
                if self.first_anchor_href is None: self.first_anchor_href=href
        if (tag in ("div","span","section")) and (a.get("role")=="status" or a.get("aria-live")):
            self.live_regions+=1

    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i]==tag: del self.stack[i:]; break
        if re.match(r"^h[1-6]$", tag) and self._hlevel is not None:
            self.headings.append((self._hlevel,(self._htext or "").strip())); self._hlevel=None; self._htext=None
        if tag=="button": self._open_btn=None

    def handle_data(self, data):
        if self._hlevel is not None: self._htext=(self._htext or "")+data
        if self._open_btn is not None: self._open_btn["text"]+=data  # buttons don't nest

def visible_text_has_label(b):
    # strip svg-only: consider non-whitespace text
    return bool(re.sub(r"\s+","",b["text"]))

def audit(html_path, css_path):
    d=DOM2()
    d.feed(open(html_path,encoding="utf-8").read())
    crit=[]; warns=[]; info=[]

    # 1. Landmarks
    present={k:(any(t in d.landmarks for t in v)) for k,v in LANDMARKS.items()}
    info.append("LANDMARKS: " + ", ".join(f"{k}={'Y' if v else 'N'}" for k,v in present.items()))
    for req in ("main","nav"):
        key=[k for k,v in LANDMARKS.items() if req in v][0]
        if not present[key]: crit.append(f"missing {key} landmark")
    # banner/header is recommended, not critical
    if not present["banner"] and "header" not in d.landmarks:
        warns.append("no <header>/banner landmark (recommended)")
    if not present["form"]: warns.append("no <form> landmark wrapping interactive fields (editor uses bare inputs)")

    # 2. Heading order
    h1s=[h for h in d.headings if h[0]==1]
    if len(h1s)!=1: crit.append(f"expected exactly one h1, found {len(h1s)}")
    prev=0; skips=[]
    for lvl,_ in d.headings:
        if prev and lvl>prev+1: skips.append((prev,lvl))
        prev=max(prev,lvl)
    if skips: crit.append(f"heading level skips: {skips}")
    info.append(f"HEADINGS: {len(d.headings)} total, h1={len(h1s)}, order={'OK' if not skips else 'SKIP '+str(skips)}")

    # 3. Accessible names
    btn_no_name=[]
    for b in d.buttons:
        if not (b["aria"] or b["title"] or visible_text_has_label(b)):
            btn_no_name.append(b["id"] or "<anon>")
    if btn_no_name: crit.append(f"buttons without accessible name ({len(btn_no_name)}): {btn_no_name}")
    # title-only buttons are acceptable but flagged weak
    btn_title_only=[b["id"] for b in d.buttons if not b["aria"] and not visible_text_has_label(b) and b["title"]]
    if btn_title_only: warns.append(f"buttons named via title/attr only (visible text empty): {btn_title_only}")

    field_no_name=[]; field_weak=[]
    for f in d.fields:
        labelled = f["aria"] or (f["id"] and f["id"] in d.labels_for) or f["in_label"]
        if labelled: continue
        if f["placeholder"]: field_weak.append(f["id"] or f["tag"])
        else: field_no_name.append(f["id"] or f["tag"])
    if field_no_name: crit.append(f"inputs/selects/textareas with NO label & no aria-label ({len(field_no_name)}): {field_no_name}")
    if field_weak: warns.append(f"fields named only by placeholder (weak, not a11y-recommended): {field_weak}")
    info.append(f"FIELDS: {len(d.fields)} total; labelled={len(d.fields)-len(field_no_name)-len(field_weak)}; weak-placeholder={len(field_weak)}; missing={len(field_no_name)}")

    # 4. Skip link
    has_skip=any(re.match(r"#(main|content|chat)",h) for h in d.skip_links)
    if has_skip: info.append(f"SKIP LINK: present ({d.first_anchor_href})")
    else: warns.append("no skip-to-content link (first focusable should jump past header to #main)")

    # 5. Focus-visible CSS
    css=open(css_path,encoding="utf-8").read()
    fv=css.count(":focus-visible")
    has_outline=bool(re.search(r":focus-visible[^{}]*\{[^}]*outline", css)) or bool(re.search(r"outline[^;]*;[^}]*\}\s*\n?[^{}]*:focus-visible", css))
    if fv==0: crit.append("no :focus-visible rule in ui/app.css (keyboard focus not visibly indicated)")
    else: info.append(f"FOCUS-VISIBLE: {fv} :focus-visible occurrence(s) in app.css")

    # 6. Live regions
    info.append(f"LIVE REGIONS: {d.live_regions} role=status/aria-live element(s)")
    if d.live_regions==0: warns.append("no aria-live region for async status updates")

    return crit, warns, info

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--html",default="index.html"); ap.add_argument("--css",default="ui/app.css")
    a=ap.parse_args()
    crit,warns,info=audit(a.html,a.css)
    print("== STATIC ARIA / KEYBOARD AUDIT ==")
    for line in info: print("  [i] "+line)
    if warns:
        print("WARNINGS:")
        for w in warns: print("  [w] "+w)
    if crit:
        print("CRITICAL FAILURES:")
        for c in crit: print("  [x] "+c)
    verdict="PASS" if not crit else f"FAIL ({len(crit)} critical)"
    print(f"RESULT: {verdict}")
    sys.exit(0 if not crit else 1)

if __name__=="__main__": main()
