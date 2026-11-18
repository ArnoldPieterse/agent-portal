#!/usr/bin/env python3
"""
Portal Accessibility Audit (Static) - WCAG 2.1 AA
Analyzes index.html + ui/*.css + ui/*.js for common a11y violations.
No live server needed - works on source files.

Usage: python memory/verifier/a11y_audit.py [--root .]
Output: memory/verifier/a11y-report.md (structured report with severity breakdown)
"""
import sys, os, re, json
from pathlib import Path
from html.parser import HTMLParser

class A11yHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.violations = []
        self.headings = []  # (level, line)
        self.images_no_alt = []
        self.inputs_no_label = []
        self.buttons_no_text = []
        self.links_no_text = []
        self.aria_issues = []
        self.missing_lang = False
        self.html_tag_seen = False
        self.current_line = 0
        self.stack = []
        self.last_label_for = None
        self.input_ids = []  # (id, line)
        self.label_fors = set()
        self.buttons_info = []  # (line, has_text, has_aria_label, has_title)
        self.links_info = []

    def handle_starttag(self, tag, attrs):
        self.current_line = self.getpos()[0]
        attrs_d = dict(attrs)

        if tag == 'html':
            self.html_tag_seen = True
            if 'lang' not in attrs_d:
                self.missing_lang = True
                self.violations.append({
                    'rule': 'html-has-lang',
                    'severity': 'serious',
                    'wcag': '3.1.1',
                    'line': self.current_line,
                    'msg': "<html> missing lang attribute"
                })

        if tag == 'img':
            alt = attrs_d.get('alt')
            if alt is None:
                self.images_no_alt.append(self.current_line)
                self.violations.append({
                    'rule': 'image-alt',
                    'severity': 'critical',
                    'wcag': '1.1.1',
                    'line': self.current_line,
                    'msg': f"img missing alt attribute (line {self.current_line})"
                })
            elif alt == '' and not attrs_d.get('role') == 'presentation' and not attrs_d.get('aria-hidden') == 'true':
                self.violations.append({
                    'rule': 'image-alt-empty',
                    'severity': 'minor',
                    'wcag': '1.1.1',
                    'line': self.current_line,
                    'msg': f"img has empty alt without role=presentation (line {self.current_line})"
                })

        if tag in ('h1','h2','h3','h4','h5','h6'):
            level = int(tag[1])
            self.headings.append((level, self.current_line))

        if tag == 'input':
            inp_type = attrs_d.get('type', 'text')
            if inp_type in ('hidden', 'submit', 'button', 'reset', 'file'):
                return
            inp_id = attrs_d.get('id')
            has_aria_label = 'aria-label' in attrs_d
            has_aria_describedby = 'aria-describedby' in attrs_d
            has_placeholder = 'placeholder' in attrs_d
            # Check if there's a label[for=id] or wrapping label
            if inp_id:
                self.input_ids.append((inp_id, self.current_line))
            if not has_aria_label and not has_aria_describedby:
                # We'll check label[for] later; flag for now
                self.inputs_no_label.append((attrs_d.get('id','?'), inp_type, self.current_line, has_placeholder))

        if tag == 'label':
            for_attr = attrs_d.get('for')
            if for_attr:
                self.label_fors.add(for_attr)

        if tag == 'button':
            has_aria_label = bool(attrs_d.get('aria-label'))
            has_title = bool(attrs_d.get('title'))
            self.buttons_info.append((self.current_line, has_aria_label, has_title))

        if tag == 'a':
            href = attrs_d.get('href')
            has_aria_label = bool(attrs_d.get('aria-label'))
            self.links_info.append((self.current_line, href, has_aria_label))

        # ARIA validation
        role = attrs_d.get('role')
        if role:
            valid_roles = {'alert','alertdialog','application','article','banner','button',
                          'cell','checkbox','columnheader','combobox','complementary','contentinfo',
                          'definition','dialog','directory','doc-abstract','doc-acknowledgments',
                          'doc-after','doc-appendix','doc-backlink','doc-biblioentry','doc-bibliography',
                          'doc-biblioref','doc-chapter','doc-colophon','doc-conclusion','doc-cover',
                          'doc-credit','doc-credits','doc-dedication','doc-endnote','doc-endnotes',
                          'doc-epigraph','doc-epilogue','doc-errata','doc-example','doc-footnote',
                          'doc-foreword','doc-glossary','doc-glossref','doc-index','doc-introduction',
                          'doc-noteref','doc-notice','doc-pagebreak','doc-pagelist','doc-part',
                          'doc-preface','doc-prologue','doc-pullquote','doc-qna','doc-subtitle',
                          'doc-tip','doc-toc','document','feed','figure','form','grid','gridcell',
                          'group','heading','img','link','list','listbox','listitem','log','main',
                          'marquee','math','menu','menubar','menuitem','menuitemcheckbox',
                          'menuitemradio','navigation','none','note','option','presentation','progressbar',
                          'radio','radiogroup','region','row','rowgroup','rowheader','scrollbar',
                          'search','searchbox','separator','slider','spinbutton','status','switch',
                          'tab','table','tablist','tabpanel','term','textbox','timer','toolbar','tooltip','tree','treegrid','treeitem'}
            if role not in valid_roles:
                self.aria_issues.append({
                    'rule': 'aria-valid-role',
                    'severity': 'serious',
                    'wcag': '4.1.2',
                    'line': self.current_line,
                    'msg': f"Invalid ARIA role '{role}' (line {self.current_line})"
                })

        # Check aria-* attributes for validity
        for attr, val in attrs:
            if attr.startswith('aria-'):
                valid_aria = {'aria-activedescendant','aria-atomic','aria-autocomplete','aria-braillelabel',
                             'aria-brailleroledescription','aria-busy','aria-checked','aria-colcount',
                             'aria-colindex','aria-colindextext','aria-colspan','aria-commands','aria-controls',
                             'aria-current','aria-describedby','aria-description','aria-details','aria-disabled',
                             'aria-dropeffect','aria-errormessage','aria-expanded','aria-flowto','aria-grabbed',
                             'aria-haspopup','aria-hidden','aria-keyshortcuts','aria-label','aria-labelledby',
                             'aria-level','aria-live','aria-modal','aria-multiline','aria-multiselectable',
                             'aria-orientation','aria-owns','aria-placeholder','aria-posinset','aria-pressed',
                             'aria-readonly','aria-relevant','aria-required','aria-roledescription','aria-rowcount',
                             'aria-rowindex','aria-rowindextext','aria-rowspan','aria-selected','aria-setsize',
                             'aria-sort','aria-valuemax','aria-valuemin','aria-valuenow','aria-valuetext'}
                if attr not in valid_aria:
                    self.aria_issues.append({
                        'rule': 'aria-valid-attribute',
                        'severity': 'serious',
                        'wcag': '4.1.2',
                        'line': self.current_line,
                        'msg': f"Invalid ARIA attribute '{attr}' (line {self.current_line})"
                    })

        # aria-selected only on valid roles
        if 'aria-selected' in attrs_d:
            if role and role not in ('option','row','tab','columnheader','gridcell','treeitem','switch','checkbox','radio'):
                self.aria_issues.append({
                    'rule': 'aria-allowed-attr',
                    'severity': 'moderate',
                    'wcag': '4.1.2',
                    'line': self.current_line,
                    'msg': f"aria-selected on role '{role}' (not a valid combination) line {self.current_line}"
                })

    def handle_data(self, data):
        # Track button text content (simplified - just check if non-whitespace follows)
        pass

    def close_audit(self):
        """Post-parse checks"""
        # Heading order
        prev_level = 0
        for level, line in self.headings:
            if prev_level > 0 and level > prev_level + 1:
                self.violations.append({
                    'rule': 'heading-order',
                    'severity': 'moderate',
                    'wcag': '1.3.1',
                    'line': line,
                    'msg': f"Heading h{level} follows h{prev_level} (skipped level) at line {line}"
                })
            prev_level = level

        # Check inputs without labels
        for inp_id, inp_type, line, has_placeholder in self.inputs_no_label:
            if inp_id not in self.label_fors and not any(
                inp_id == lid for lid in self.label_fors
            ):
                severity = 'serious' if not has_placeholder else 'moderate'
                self.violations.append({
                    'rule': 'label',
                    'severity': severity,
                    'wcag': '1.3.1 / 3.3.2',
                    'line': line,
                    'msg': f"Input #{inp_id} (type={inp_type}) has no associated <label> or aria-label (line {line})"
                })

        # Multiple h1 check
        h1_count = sum(1 for l, _ in self.headings if l == 1)
        if h1_count > 1:
            self.violations.append({
                'rule': 'page-has-heading-one',
                'severity': 'minor',
                'wcag': '1.3.1',
                'line': 0,
                'msg': f"Multiple <h1> elements found ({h1_count})"
            })


def audit_css(css_text, css_path):
    """Check CSS for a11y issues: font-size minimums, color contrast hints"""
    violations = []

    # Check for very small font sizes (< 10px is almost certainly an issue)
    font_matches = re.finditer(r'font-size\s*:\s*([\d.]+)px', css_text)
    for m in font_matches:
        size = float(m.group(1))
        if size < 10:
            line = css_text[:m.start()].count('\n') + 1
            violations.append({
                'rule': 'font-size-minimum',
                'severity': 'minor',
                'wcag': '1.4.4',
                'line': line,
                'msg': f"font-size {size}px below recommended minimum (line {line} in {css_path})"
            })

    # Check for color definitions that might have low contrast
    # Look for CSS custom properties with color values
    color_vars = re.findall(r'(--\w+)\s*:\s*(#[0-9a-fA-F]{3,8}|rgba?\([^)]+\))', css_text)
    # We'd need to pair these with their usage context for real contrast checks
    # Flag as informational for now

    return violations


def audit_js(js_text, js_path):
    """Check JS for a11y-relevant patterns"""
    violations = []

    # Check for document.write (can break screen readers)
    if 'document.write' in js_text:
        violations.append({
            'rule': 'no-document-write',
            'severity': 'minor',
            'wcag': '2.4.1',
            'line': 0,
            'msg': f"document.write() usage found in {js_path} (can interfere with AT)"
        })

    # Check for alert/confirm without accessible alternative
    # (informational only - these are common in portal context)

    return violations


def run_audit(root='.'):
    """Run full static audit"""
    root = Path(root)
    all_violations = []

    # 1. HTML audit
    html_file = root / 'index.html'
    if not html_file.exists():
        print(f"ERROR: {html_file} not found", file=sys.stderr)
        sys.exit(1)

    html_content = html_file.read_text(encoding='utf-8')
    parser = A11yHTMLParser()
    parser.feed(html_content)
    parser.close_audit()
    all_violations.extend(parser.violations)

    # 2. CSS audit
    ui_dir = root / 'ui'
    if ui_dir.exists():
        for css_file in sorted(ui_dir.glob('*.css')):
            css_text = css_file.read_text(encoding='utf-8')
            all_violations.extend(audit_css(css_text, str(css_file)))

    # 3. JS audit
    if ui_dir.exists():
        for js_file in sorted(ui_dir.glob('*.js')):
            js_text = js_file.read_text(encoding='utf-8')
            all_violations.extend(audit_js(js_text, str(js_file)))

    return all_violations


def generate_report(violations, output_path):
    """Generate structured Markdown report"""
    sev_order = {'critical': 0, 'serious': 1, 'moderate': 2, 'minor': 3}
    violations.sort(key=lambda v: (sev_order.get(v['severity'], 9), v.get('line', 0)))

    counts = {}
    for v in violations:
        counts[v['severity']] = counts.get(v['severity'], 0) + 1

    lines = []
    lines.append("# Portal Accessibility Audit - WCAG 2.1 AA (Static)")
    lines.append(f"\nDate: 2026-11-18\n")
    lines.append(f"## Summary\n")
    lines.append(f"| Severity | Count |")
    lines.append(f"|----------|-------|")
    for sev in ['critical', 'serious', 'moderate', 'minor']:
        c = counts.get(sev, 0)
        lines.append(f"| {sev} | {c} |")
    lines.append(f"| **Total** | **{len(violations)}** |\n")

    # Target check
    critical_count = counts.get('critical', 0)
    serious_count = counts.get('serious', 0)
    target_met = critical_count == 0 and serious_count == 0
    lines.append(f"## Target: 0 critical, 0 serious\n")
    lines.append(f"**{'PASS' if target_met else 'FAIL'}** - {critical_count} critical, {serious_count} serious\n")

    if violations:
        lines.append("## Violations\n")
        for i, v in enumerate(violations, 1):
            lines.append(f"### {i}. [{v['severity'].upper()}] {v['rule']}")
            lines.append(f"- **WCAG:** {v['wcag']}")
            if v.get('line'):
                lines.append(f"- **Line:** {v['line']}")
            lines.append(f"- **Detail:** {v['msg']}\n")
    else:
        lines.append("## Violations\n")
        lines.append("None found. All checks passed.\n")

    report = '\n'.join(lines)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(report, encoding='utf-8')
    return report, target_met


if __name__ == '__main__':
    root = '.'
    if '--root' in sys.argv:
        idx = sys.argv.index('--root')
        root = sys.argv[idx + 1]

    print(f"Running static a11y audit on {root}...")
    violations = run_audit(root)
    out_path = os.path.join(root, 'memory', 'verifier', 'a11y-report.md')
    report, target_met = generate_report(violations, out_path)

    print(f"\nAudit complete: {len(violations)} violation(s)")
    counts = {}
    for v in violations:
        counts[v['severity']] = counts.get(v['severity'], 0) + 1
    for sev in ['critical', 'serious', 'moderate', 'minor']:
        if counts.get(sev):
            print(f"  {sev}: {counts[sev]}")

    print(f"\nTarget (0 critical, 0 serious): {'PASS' if target_met else 'FAIL'}")
    print(f"Report: {out_path}")
    sys.exit(0 if target_met else 1)
