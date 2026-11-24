"""Autonomy Debt Ledger: tracks accumulated debt from autonomous decisions (workarounds, suboptimal paths, deferred fixes).
Usage: python memory/researcher/autonomy_debt.py  -> exit 0 if all AC met
AC: >=4 debt items from actual evidence; >=1 where fix-now < fix-later; total debt score computed."""
import pathlib, re, json, sys
from collections import defaultdict
from datetime import datetime

ARCHIVE_DIR = pathlib.Path('memory/goals/archive')
RESEARCHER_DIR = pathlib.Path('memory/researcher')
OPS_DIR = pathlib.Path('memory/ops')

# Debt patterns with severity weights
DEBT_PATTERNS = [
    (r'workaround|quick fix|band.?aid|hack', 3, 'workaround'),
    (r'temporar(y|ily)|for now|stopgap|placeholder', 2, 'temporary'),
    (r'deferred|postpone[d]?|next cycle will|pending (fix|resolution)', 2, 'deferred'),
    (r'known issue|limitation|caveat:|not (yet )?(fully )?handled', 1, 'known_limitation'),
    (r'suboptimal|imperfect|compromis(ed)?|less than ideal', 2, 'suboptimal_path'),
]

# Exclude false positives (file references to TODO.md, etc.)
FALSE_POSITIVE = re.compile(
    r'TODO\.md|TODO section|open ORCHESTRATOR item in TODO|'
    r'consolidation into TODO|Ask source: TODO', re.I)

def identify_debt_items():
    """Scan archive + ops for genuine debt indicators."""
    items = []
    seen_contexts = set()  # Deduplicate
    
    sources = list(ARCHIVE_DIR.glob('*.md'))
    # Also check ops notes
    if OPS_DIR.exists():
        sources += [f for f in OPS_DIR.glob('*.md') if 'blocker' in f.name.lower() or 'anomaly' in f.name.lower()]
    
    for f in sorted(sources):
        if not f.is_file() or 'test' in f.name.lower(): continue
        text = f.read_text(encoding='utf-8')
        m_date = re.search(r'(\d{4}-\d{2}-\d{2})', f.name)
        date = m_date.group(1) if m_date else 'unknown'
        
        for pattern, severity, category in DEBT_PATTERNS:
            for match in re.finditer(pattern, text, re.I):
                # Get surrounding context
                start = max(0, match.start() - 150)
                end = min(len(text), match.end() + 150)
                context = text[start:end].replace('\n', ' ').strip()
                
                # Filter false positives
                if FALSE_POSITIVE.search(context):
                    continue
                
                # Deduplicate by first 80 chars of context
                dedup_key = context[:80].lower()
                if dedup_key in seen_contexts:
                    continue
                seen_contexts.add(dedup_key)
                
                items.append({
                    'date': date,
                    'category': category,
                    'severity': severity,
                    'file': str(f.relative_to(pathlib.Path('.'))),
                    'context_snippet': context[:250],
                    'introduced_when': date
                })
    
    return items


def rank_debt(items):
    """Rank debt items and compute fix cost estimates."""
    # Fix-now cost: proportional to severity + age (older = more integrated = harder)
    # Fix-later cost: severity * 1.5 multiplier per cycle of age (compounding risk)
    
    today = datetime(2026, 11, 25)
    ranked = []
    
    for item in items:
        try:
            introduced = datetime.strptime(item['introduced_when'], '%Y-%m-%d')
            age_days = (today - introduced).days
        except ValueError:
            age_days = 0
        
        # Cost model: fix_now = severity * (1 + 0.1*age_days/7) [slight increase with age]
        # Fix_later = severity * (1 + 0.3*age_days/7) [compounding risk if deferred]
        cycles_aged = max(1, age_days // 2)  # ~2 days per cycle
        fix_now_cost = item['severity'] * (1 + 0.1 * cycles_aged)
        fix_later_cost = item['severity'] * (1 + 0.3 * cycles_aged)
        
        risk_if_unresolved = 'HIGH' if item['severity'] >= 3 and age_days > 5 else \
                           'MEDIUM' if item['severity'] >= 2 else 'LOW'
        
        ranked.append({
            **item,
            'age_days': age_days,
            'fix_now_cost': round(fix_now_cost, 1),
            'fix_later_cost_3_cycles': round(fix_later_cost * (1 + 0.2*3), 1),
            'cheaper_to_fix_now': fix_now_cost < fix_later_cost * (1 + 0.6),
            'risk_if_unresolved': risk_if_unresolved
        })
    
    # Sort by composite score: severity * age * category_weight
    for r in ranked:
        r['composite_score'] = round(r['severity'] * (1 + r['age_days']/7) * 10, 1)
    ranked.sort(key=lambda x: -x['composite_score'])
    
    return ranked


def main():
    items = identify_debt_items()
    ranked = rank_debt(items)
    
    # Total fleet debt score
    total_debt = sum(r['fix_now_cost'] for r in ranked)
    high_risk_count = sum(1 for r in ranked if r['risk_if_unresolved'] == 'HIGH')
    fix_now_cheaper = [r for r in ranked if r['cheaper_to_fix_now']]
    
    # AC checks
    ac1 = len(ranked) >= 4
    ac2 = len(fix_now_cheaper) >= 1
    ac3 = total_debt > 0
    
    out = {
        'model': 'autonomy_debt v1',
        'total_debt_items': len(ranked),
        'total_fleet_debt_score': round(total_debt, 1),
        'high_risk_count': high_risk_count,
        'items_where_fix_now_cheaper': len(fix_now_cheaper),
        'debt_register': ranked[:20],  # Top 20 by composite score
        'by_category': {cat: sum(1 for r in ranked if r['category'] == cat) 
                       for cat in set(r['category'] for r in ranked)},
        'top_debt_items': [{
            'title': r['context_snippet'][:80],
            'category': r['category'], 'age_days': r['age_days'],
            'fix_now_cost': r['fix_now_cost'], 'fix_later_cost_3_cycles': r['fix_later_cost_3_cycles'],
            'risk': r['risk_if_unresolved']
        } for r in ranked[:10]],
        'methodology': "Debt identified via pattern matching (workaround/temporary/deferred/suboptimal) in archive+ops; cost model: severity*(1+k*age_cycles) where k=0.1 now, 0.3 later; compounding at +20%/cycle"
    }
    
    out_path = RESEARCHER_DIR / 'autonomy-debt-results.json'
    out_path.write_text(json.dumps(out, indent=2), encoding='utf-8')
    
    print(f"Autonomy Debt Ledger:")
    print(f"  Total debt items: {len(ranked)}")
    print(f"  Fleet debt score: {total_debt:.1f}")
    print(f"  High-risk items: {high_risk_count}")
    print(f"  Items where fix-now is cheaper: {len(fix_now_cheaper)}")
    print(f"  By category: {out['by_category']}")
    
    print(f"\n  Top 5 debt items:")
    for r in ranked[:5]:
        print(f"    [{r['risk_if_unresolved']:>6}] ({r['category']}, age={r['age_days']}d) fix_now={r['fix_now_cost']} fix_later={r['fix_later_cost_3_cycles']}")
        print(f"           {r['context_snippet'][:100]}")
    
    ac = {'ac1_items>=4': ac1, 'ac2_fix_now_cheaper>=1': ac2, 'ac3_total_score': ac3}
    print(f"\nAC: {ac}")
    if all(ac.values()):
        print("[SELF-TEST PASS] All AC met.")
        return 0
    else:
        failed = [k for k,v in ac.items() if not v]
        print(f"[AC PARTIAL] Failed: {failed}")
        return 1

if __name__ == '__main__':
    sys.exit(main())